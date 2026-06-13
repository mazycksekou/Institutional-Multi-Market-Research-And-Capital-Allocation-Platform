"""
Phase 10H7 – SQLite‑backed Backtesting Bridge.

Reads validated historical‑odds rows from the SQLite store (Phase 10H6),
converts them to the canonical backtest format expected by
:func:`~automation_scheduler.backtesting_engine.run_backtest`, and returns a
compact projection summary.

No Streamlit changes yet.
No downloads / scraping / bankroll‑math rewrites.
The existing backtesting engine remains the canonical owner.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation_scheduler.backtesting_engine import run_backtest
from automation_scheduler.historical_odds_importers import (
    CANONICAL_HISTORICAL_ODDS_REQUIRED_FIELDS,
    normalize_team_name,
    normalize_market_name,
    normalize_selection_name,
)
from automation_scheduler.historical_odds_sqlite import (
    connect_historical_odds_db,
    query_historical_odds_rows,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HISTORICAL_BACKTEST_BRIDGE_VERSION: str = "10H7"

DEFAULT_HISTORICAL_MODEL_ID: str = "sqlite-historical-backtest"

DEFAULT_SQLITE_BACKTEST_LIMIT: int = 1000

# Fields that are always allowed inside features_known_at_decision_time.
# Any field known *after* the decision point is excluded.
_PRE_DECISION_FIELD_WHITELIST: set[str] = {
    "source_key",
    "source_file",
    "sport",
    "league",
    "season",
    "event_date",
    "home_team",
    "away_team",
    "bookmaker",
    "market",
    "selection",
    "odds_at_decision_time",
    "market_implied_probability",
    "opening_odds",
    "collected_at",
    "raw_market_name",
    "raw_selection_name",
    "raw_event_id",
    "raw_row_index",
    "features_known_at_decision_time",
}

_FORBIDDEN_IN_FEATURES: set[str] = {
    "final_result",
    "winner",
    "home_score",
    "away_score",
    "profit_loss",
    "closing_line",
    "closing_odds",
    "clv",
    "result_status",
    "settlement_result",
    "paper_result",
    "pnl",
}


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _build_safe_features(row: dict[str, Any]) -> dict[str, Any]:
    """Return a dict that contains only pre‑decision fields from *row*."""
    safe: dict[str, Any] = {}
    for key in _PRE_DECISION_FIELD_WHITELIST:
        if key in row and row[key] is not None:
            safe[key] = row[key]
    # remove any that accidentally leaked through
    for forbidden in _FORBIDDEN_IN_FEATURES:
        safe.pop(forbidden, None)
    return safe


def sqlite_odds_row_to_backtest_row(
    row: dict[str, Any],
    *,
    model_probability: float | None = None,
    raw_index: int | None = None,
) -> dict[str, Any]:
    """Convert a single SQLite historical‑odds row into a canonical backtest row.

    Parameters
    ----------
    row : dict
        A dict returned by :func:`~automation_scheduler.historical_odds_sqlite.query_historical_odds_rows`.
    model_probability : float, optional
        Override for the model probability. Default: ``market_implied_probability``.
    raw_index : int, optional
        Row index used when converting a batch; preserved as ``raw_row_index``.

    Returns
    -------
    dict
        A backtest‑ready row consumable by :func:`run_backtest`.
    """
    mp = row.get("market_implied_probability")
    model_prob = (
        float(model_probability)
        if model_probability is not None
        else (float(mp) if mp is not None else 0.0)
    )

    backtest_row: dict[str, Any] = {
        "event_id": row.get("event_id") or "",
        "contract_id": row.get("odds_id") or "",
        "source_key": row.get("source_key") or "",
        "source_file": row.get("source_file") or "",
        "sport": row.get("sport") or "",
        "league": row.get("league") or "",
        "event_date": row.get("event_date") or "",
        "decision_time": row.get("event_date") or row.get("collected_at") or "",
        "home_team": row.get("home_team") or "",
        "away_team": row.get("away_team") or "",
        "market": row.get("market") or "",
        "selection": row.get("selection") or "",
        "odds_at_decision_time": row.get("odds_at_decision_time"),
        "odds": row.get("odds_at_decision_time"),
        "market_implied_probability": float(row["market_implied_probability"]) if row.get("market_implied_probability") is not None else 0.0,
        "model_probability": model_prob,
        "edge": 0.0,
        "stake": 1.0,
        "final_result": row.get("final_result") or "",
        "home_score": row.get("home_score"),
        "away_score": row.get("away_score"),
        "winner": row.get("winner"),
        "raw_row_index": raw_index if raw_index is not None else row.get("raw_row_index"),
        "features_known_at_decision_time": _build_safe_features(row),
    }

    # Explicitly remove any leaking keys from the top level
    for f in _FORBIDDEN_IN_FEATURES:
        if f not in ("final_result", "home_score", "away_score", "winner"):
            backtest_row.pop(f, None)

    return backtest_row


def sqlite_odds_rows_to_backtest_rows(
    rows: list[dict[str, Any]],
    *,
    model_probability: float | None = None,
) -> list[dict[str, Any]]:
    """Convert a list of SQLite rows to a list of canonical backtest rows."""
    return [
        sqlite_odds_row_to_backtest_row(r, model_probability=model_probability, raw_index=idx)
        for idx, r in enumerate(rows)
    ]


# ---------------------------------------------------------------------------
# Query adapter
# ---------------------------------------------------------------------------


def query_sqlite_backtest_rows(
    conn: Any,
    *,
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = DEFAULT_SQLITE_BACKTEST_LIMIT,
    model_probability: float | None = None,
) -> list[dict[str, Any]]:
    """Query the SQLite store and return converted backtest rows."""
    raw_rows = query_historical_odds_rows(
        conn,
        sport=sport,
        league=league,
        market=market,
        source_key=source_key,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return sqlite_odds_rows_to_backtest_rows(raw_rows, model_probability=model_probability)


# ---------------------------------------------------------------------------
# Bridge runner
# ---------------------------------------------------------------------------


def run_sqlite_historical_backtest(
    conn: Any,
    *,
    model_id: str = DEFAULT_HISTORICAL_MODEL_ID,
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = DEFAULT_SQLITE_BACKTEST_LIMIT,
    model_probability: float | None = None,
    strategy_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Query SQLite, convert rows, run a historical backtest, and return results.

    Parameters
    ----------
    conn : sqlite3.Connection
        An open connection to the historical‑odds SQLite database.
    model_id : str
        Identifier for the backtest run.
    sport, league, market, source_key, start_date, end_date, limit
        Filter arguments passed to :func:`query_sqlite_backtest_rows`.
    model_probability : float, optional
        Override model probability for every row.
    strategy_config : dict, optional
        Strategy configuration forwarded to :func:`run_backtest`.

    Returns
    -------
    dict
        Contains ``ok``, ``bridge_version``, ``model_id``, ``query``,
        ``rows_loaded``, ``rows_converted``, ``backtest_result``,
        and ``projection_summary``.
    """
    query_params = {
        "sport": sport,
        "league": league,
        "market": market,
        "source_key": source_key,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
    }

    raw_db_rows = query_historical_odds_rows(
        conn,
        sport=sport,
        league=league,
        market=market,
        source_key=source_key,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    rows_loaded = len(raw_db_rows)
    backtest_rows = sqlite_odds_rows_to_backtest_rows(
        raw_db_rows, model_probability=model_probability
    )
    rows_converted = len(backtest_rows)

    bt_result: dict[str, Any] = {}
    if rows_converted > 0:
        try:
            bt_result = run_backtest(
                model_id=model_id,
                rows=backtest_rows,
                strategy_config=strategy_config,
            )
        except Exception as exc:
            bt_result = {"error": str(exc)}
    else:
        bt_result = {
            "ok": False,
            "status": "insufficient_data",
            "sample_size": 0,
        }

    # projection summary ---------------------------------------------------
    sports_set: set[str] = set()
    leagues_set: set[str] = set()
    markets_set: set[str] = set()
    source_keys_set: set[str] = set()
    for r in raw_db_rows:
        if r.get("sport"):
            sports_set.add(str(r["sport"]))
        if r.get("league"):
            leagues_set.add(str(r["league"]))
        if r.get("market"):
            markets_set.add(str(r["market"]))
        if r.get("source_key"):
            source_keys_set.add(str(r["source_key"]))

    projection_summary: dict[str, Any] = {
        "rows_loaded": rows_loaded,
        "rows_converted": rows_converted,
        "sports": sorted(sports_set),
        "leagues": sorted(leagues_set),
        "markets": sorted(markets_set),
        "source_keys": sorted(source_keys_set),
        "backtest_ran": rows_converted > 0,
    }

    return {
        "ok": bool(bt_result.get("ok", False)) if rows_converted > 0 else False,
        "bridge_version": HISTORICAL_BACKTEST_BRIDGE_VERSION,
        "model_id": model_id,
        "query": query_params,
        "rows_loaded": rows_loaded,
        "rows_converted": rows_converted,
        "backtest_result": bt_result,
        "projection_summary": projection_summary,
    }


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def summarize_sqlite_historical_backtest(
    result: dict[str, Any],
) -> dict[str, Any]:
    """Return a compact human‑readable summary of the bridge result."""
    bt = result.get("backtest_result") or {}
    proj = result.get("projection_summary") or {}

    bets = bt.get("bets", 0)
    no_bets = bt.get("no_bets", 0)
    profit_loss = bt.get("profit_loss", 0.0)
    roi_percent = bt.get("roi_percent", 0.0)
    max_drawdown_percent = bt.get("max_drawdown_percent", 0.0)

    missing_keys = any(
        k not in bt for k in ("bets", "no_bets", "profit_loss", "roi_percent", "max_drawdown_percent")
    )
    projection_ready = (
        result.get("rows_loaded", 0) > 0 and not missing_keys
    )
    reason = ""
    if not projection_ready:
        if result.get("rows_loaded", 0) == 0:
            reason = "no rows loaded from SQLite"
        elif missing_keys:
            reason = "backtest_result missing expected summary fields"

    return {
        "ok": bool(result.get("ok")),
        "model_id": result.get("model_id", ""),
        "rows_loaded": result.get("rows_loaded", 0),
        "rows_converted": result.get("rows_converted", 0),
        "bets": bets,
        "no_bets": no_bets,
        "profit_loss": profit_loss,
        "roi_percent": roi_percent,
        "max_drawdown_percent": max_drawdown_percent,
        "sports": proj.get("sports", []),
        "leagues": proj.get("leagues", []),
        "markets": proj.get("markets", []),
        "source_keys": proj.get("source_keys", []),
        "projection_ready": projection_ready,
        "reason": reason,
    }


# ---------------------------------------------------------------------------
# Filter options for Streamlit (Phase 10H8)
# ---------------------------------------------------------------------------


def get_sqlite_backtest_filter_options(
    conn: Any,
) -> dict[str, Any]:
    """Read available filter options from the SQLite store.

    Returns
    -------
    dict
        Keys: ``sports``, ``leagues``, ``markets``, ``source_keys``,
        ``event_date_min``, ``event_date_max``, ``total_odds``.
    """
    # query_historical_odds_rows can expose a `limit` argument; we pass a high
    # number to get all distinct values via the summary helper.
    from automation_scheduler.historical_odds_sqlite import summarize_historical_odds_db

    summary = summarize_historical_odds_db(conn)

    date_min: str | None = None
    date_max: str | None = None
    cursor = conn.execute("SELECT MIN(event_date) AS dmin, MAX(event_date) AS dmax FROM historical_odds")
    row = cursor.fetchone()
    if row:
        date_min = row["dmin"]
        date_max = row["dmax"]

    return {
        "sports": summary.get("sports", []),
        "leagues": summary.get("leagues", []),
        "markets": summary.get("markets", []),
        "source_keys": summary.get("sources", []),
        "event_date_min": date_min,
        "event_date_max": date_max,
        "total_odds": summary.get("total_odds", 0),
    }
