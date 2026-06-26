from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Mapping, Sequence

from .engine import run_backtest
from src.data.historical_odds import query_historical_odds_rows


def sqlite_odds_row_to_backtest_row(row: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    return {
        "event_id": payload.get("event_id") or payload.get("event") or payload.get("event_key"),
        "sport": payload.get("sport"),
        "league": payload.get("league"),
        "event_date": payload.get("event_date"),
        "home_team": payload.get("home_team"),
        "away_team": payload.get("away_team"),
        "market_type": payload.get("market_type") or payload.get("market"),
        "market_name": payload.get("market_name") or payload.get("market"),
        "selection_name": payload.get("selection_name") or payload.get("selection"),
        "recommended_odds": payload.get("recommended_odds", payload.get("odds")),
        "model_probability": payload.get("model_probability", payload.get("predicted_probability")),
        "closing_odds": payload.get("closing_odds"),
        "result_status": payload.get("result_status"),
        "timestamp": payload.get("timestamp"),
        "features": dict(payload.get("features") or {}),
        "_source": "sqlite_odds_row",
    }


def sqlite_odds_rows_to_backtest_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [sqlite_odds_row_to_backtest_row(row) for row in rows if isinstance(row, Mapping)]


def query_sqlite_backtest_rows(
    db_path: str | Path | sqlite3.Connection,
    *,
    table_name: str = "historical_odds",
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    if isinstance(db_path, sqlite3.Connection):
        rows = query_historical_odds_rows(
            db_path,
            sport=sport,
            league=league,
            market=market,
            source_key=source_key,
            start_date=start_date,
            end_date=end_date,
            limit=limit if limit is not None else 1000,
        )
    else:
        path = Path(db_path)
        if not path.exists():
            return []
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        try:
            rows = query_historical_odds_rows(
                conn,
                sport=sport,
                league=league,
                market=market,
                source_key=source_key,
                start_date=start_date,
                end_date=end_date,
                limit=limit if limit is not None else 1000,
            )
        finally:
            conn.close()
    converted = sqlite_odds_rows_to_backtest_rows(rows)
    if limit is not None:
        return converted[: max(0, int(limit))]
    return converted


def run_sqlite_historical_backtest(
    db_path: str | Path | sqlite3.Connection,
    *,
    model_id: str = "sqlite_historical_backtest",
    table_name: str = "historical_odds",
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
    model_probability: float | None = None,
    strategy_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = query_sqlite_backtest_rows(
        db_path,
        table_name=table_name,
        sport=sport,
        league=league,
        market=market,
        source_key=source_key,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    base_dir = Path(db_path).parent if not isinstance(db_path, sqlite3.Connection) else Path.cwd()
    backtest_result = run_backtest(model_id=model_id, rows=rows, base_data_dir=base_dir, strategy_config=strategy_config)
    projection_summary = {
        "rows_loaded": len(rows),
        "rows_converted": len(rows),
        "sports": sorted({str(row.get("sport") or "") for row in rows if row.get("sport")}),
        "leagues": sorted({str(row.get("league") or "") for row in rows if row.get("league")}),
        "markets": sorted({str(row.get("market") or "") for row in rows if row.get("market")}),
        "source_keys": sorted({str(row.get("source_key") or "") for row in rows if row.get("source_key")}),
        "backtest_ran": bool(rows),
    }
    return {
        "ok": bool(backtest_result.get("ok", True)),
        "bridge_version": "10H7",
        "model_id": model_id,
        "query": {
            "sport": sport,
            "league": league,
            "market": market,
            "source_key": source_key,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit if limit is not None else 1000,
        },
        "rows_loaded": len(rows),
        "rows_converted": len(rows),
        "backtest_result": backtest_result,
        "projection_summary": projection_summary,
    }


def summarize_sqlite_historical_backtest(
    db_path: str | Path | Sequence[Mapping[str, Any]] | Mapping[str, Any],
    *,
    table_name: str = "historical_odds",
    limit: int | None = None,
) -> dict[str, Any]:
    if isinstance(db_path, Mapping) and ("backtest_result" in db_path or "projection_summary" in db_path):
        result = dict(db_path)
        bt = result.get("backtest_result") or {}
        proj = result.get("projection_summary") or {}
        bankroll = bt.get("strategy_bankroll_summary", {}) if isinstance(bt, Mapping) else {}
        bets = bankroll.get("bets", bt.get("bets", 0) if isinstance(bt, Mapping) else 0)
        no_bets = bankroll.get("no_bets", bt.get("no_bets", 0) if isinstance(bt, Mapping) else 0)
        profit_loss = bankroll.get("profit_loss", bt.get("profit_loss", 0.0) if isinstance(bt, Mapping) else 0.0)
        roi_percent = bankroll.get("roi_percent", bt.get("roi_percent", 0.0) if isinstance(bt, Mapping) else 0.0)
        max_drawdown_percent = bankroll.get("max_drawdown_percent", bt.get("max_drawdown_percent", 0.0) if isinstance(bt, Mapping) else 0.0)
        projection_ready = bool(result.get("ok")) and int(result.get("rows_loaded", 0)) > 0 and int(result.get("rows_converted", 0)) > 0
        reason = ""
        if not projection_ready:
            if result.get("rows_loaded", 0) == 0:
                reason = "no rows loaded from SQLite"
            elif result.get("rows_converted", 0) == 0:
                reason = "rows converted is 0"
            elif not result.get("ok"):
                reason = "bridge result indicates failure"
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
    if isinstance(db_path, Sequence) and not isinstance(db_path, (str, bytes, Path)):
        rows = sqlite_odds_rows_to_backtest_rows(db_path)
    elif isinstance(db_path, sqlite3.Connection):
        rows = query_sqlite_backtest_rows(db_path, table_name=table_name, limit=limit)
    else:
        rows = query_sqlite_backtest_rows(db_path, table_name=table_name, limit=limit)
    market_types: dict[str, int] = {}
    for row in rows:
        market_type = str(row.get("market_type") or "UNKNOWN")
        market_types[market_type] = market_types.get(market_type, 0) + 1
    return {
        "ok": True,
        "status": "summarized",
        "row_count": len(rows),
        "market_types": market_types,
        "warnings": [] if rows else ["no_rows"],
    }


def get_sqlite_backtest_filter_options(
    db_path: str | Path | Sequence[Mapping[str, Any]],
    *,
    table_name: str = "historical_odds",
) -> dict[str, Any]:
    if isinstance(db_path, Sequence) and not isinstance(db_path, (str, bytes, Path)):
        rows = sqlite_odds_rows_to_backtest_rows(db_path)
    elif isinstance(db_path, sqlite3.Connection):
        rows = query_sqlite_backtest_rows(db_path, table_name=table_name)
    else:
        rows = query_sqlite_backtest_rows(db_path, table_name=table_name)
    return {
        "ok": True,
        "status": "available",
        "sports": sorted({str(row.get("sport") or "UNKNOWN") for row in rows}),
        "market_types": sorted({str(row.get("market_type") or "UNKNOWN") for row in rows}),
        "selections": sorted({str(row.get("selection_name") or "UNKNOWN") for row in rows}),
        "row_count": len(rows),
    }


__all__ = [
    "get_sqlite_backtest_filter_options",
    "query_sqlite_backtest_rows",
    "run_sqlite_historical_backtest",
    "sqlite_odds_row_to_backtest_row",
    "sqlite_odds_rows_to_backtest_rows",
    "summarize_sqlite_historical_backtest",
]
