"""
Phase 10H12 – Line Movement Schema + Odds Snapshot Store.

Provides a safe SQLite table for tracking opening, decision, current,
and closing odds snapshots across moneyline, spread/runline, totals,
team totals, and player props.

Uses Python stdlib ``sqlite3`` only.
No downloads, no scraping, no network calls, no extra dependencies.
"""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LINE_MOVEMENT_SCHEMA_VERSION: str = "10H12"

# ---------------------------------------------------------------------------
# Idempotent table / index creation SQL
# ---------------------------------------------------------------------------

CREATE_LINE_SNAPSHOTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS historical_line_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    event_id TEXT,
    odds_id TEXT,
    source_key TEXT,
    source_file TEXT,
    sport TEXT,
    league TEXT,
    event_date TEXT,
    home_team TEXT,
    away_team TEXT,
    bookmaker TEXT,
    market TEXT,
    market_family TEXT,
    selection TEXT,
    player_name TEXT,
    team_name TEXT,
    line_value REAL,
    odds_value REAL,
    implied_probability REAL,
    snapshot_label TEXT,
    snapshot_time TEXT,
    raw_market_name TEXT,
    raw_selection_name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

LINE_SNAPSHOTS_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_line_snapshots_event ON historical_line_snapshots (event_id)",
    "CREATE INDEX IF NOT EXISTS idx_line_snapshots_sport_market ON historical_line_snapshots (sport, market)",
    "CREATE INDEX IF NOT EXISTS idx_line_snapshots_source ON historical_line_snapshots (source_key)",
    "CREATE INDEX IF NOT EXISTS idx_line_snapshots_snapshot_label ON historical_line_snapshots (snapshot_label)",
    "CREATE INDEX IF NOT EXISTS idx_line_snapshots_snapshot_time ON historical_line_snapshots (snapshot_time)",
    "CREATE INDEX IF NOT EXISTS idx_line_snapshots_player_name ON historical_line_snapshots (player_name)",
]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_hash(prefix: str, parts: list[str]) -> str:
    raw = prefix + ":" + "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Classification (local copy to avoid circular imports)
# ---------------------------------------------------------------------------


def _classify_market_family(market: str | None, selection: str | None = None) -> str:
    """Return one of the seven market families (reduced set)."""
    if not market:
        return "unknown"
    lower = (
        market.lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )
    if lower in ("1x2", "moneyline", "ml"):
        return "moneyline_or_1x2"
    if lower in ("runline", "spread", "pointspread"):
        return "spread_or_runline"
    if lower in ("total", "overunder", "totals", "over/under", "o/u", "ou", "gametotal", "totalpoints"):
        return "total"
    if lower.startswith("team_total") or lower in ("team total",):
        return "team_total"
    if selection and "player" in selection.lower():
        return "player_prop"
    if lower in (
        "playerpoints", "playerpointsprop", "playerprop",
        "player_points", "player_points_prop",
    ):
        return "player_prop"
    return "unknown"


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------


def initialize_line_movement_schema(conn: sqlite3.Connection) -> None:
    """Create the ``historical_line_snapshots`` table and indexes (idempotent)."""
    conn.executescript(CREATE_LINE_SNAPSHOTS_TABLE_SQL)
    for idx_sql in LINE_SNAPSHOTS_INDEXES_SQL:
        conn.execute(idx_sql)
    conn.commit()


# ---------------------------------------------------------------------------
# Identifier helpers
# ---------------------------------------------------------------------------


def make_line_snapshot_id(row: dict[str, Any]) -> str:
    """Deterministic ID for a line snapshot."""
    return _stable_hash(
        "ls",
        [
            str(row.get("event_id", "")),
            str(row.get("odds_id", "")),
            str(row.get("market_family", "")),
            str(row.get("selection", "")),
            str(row.get("snapshot_label", "")),
            str(row.get("snapshot_time", "")),
        ],
    )


def normalize_snapshot_label(value: Any) -> str:
    """Normalise a snapshot label to one of the allowed values."""
    if value is None:
        return "unknown"
    v = str(value).strip().lower()
    allowed = {"opening", "decision", "current", "closing", "unknown"}
    if v in allowed:
        return v
    if v in ("open", "start"):
        return "opening"
    if v in ("dec", "pick"):
        return "decision"
    if v in ("latest", "now"):
        return "current"
    if v in ("close", "end", "final"):
        return "closing"
    return "unknown"


def extract_line_value(row: dict[str, Any]) -> float | None:
    """Extract a numeric line value from a row dict.

    Checks common field names for spread/line/value.
    """
    for key in ("line_value", "player_line", "total_line", "spread_line",
                "runline", "handicap", "point_spread", "opening_line",
                "closing_line", "current_line"):
        v = row.get(key)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return None


# ---------------------------------------------------------------------------
# Row → snapshots conversion
# ---------------------------------------------------------------------------


def canonical_row_to_line_snapshots(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert a canonical historical‑odds row into zero or more line snapshots.

    Always creates a **decision** snapshot from ``odds_at_decision_time``.
    If ``opening_odds`` or ``closing_odds`` (or ``opening_line``/``closing_line``)
    exist, corresponding snapshots are also created.
    """
    snapshots: list[dict[str, Any]] = []
    now = _utc_now()

    event_id = row.get("event_id", "")
    odds_id = row.get("odds_id", "")
    sport = row.get("sport", "")
    league = row.get("league", "")
    event_date = row.get("event_date", "")
    home_team = row.get("home_team", "")
    away_team = row.get("away_team", "")
    bookmaker = row.get("bookmaker", "")
    market = row.get("market", "")
    selection = row.get("selection", "")
    source_key = row.get("source_key", "")
    source_file = row.get("source_file", "")
    raw_market_name = row.get("raw_market_name", "")
    raw_selection_name = row.get("raw_selection_name", "")

    market_family = _classify_market_family(market, selection)
    player_name = row.get("player_name")
    team_name = row.get("team_name")

    line_val = extract_line_value(row)

    # Helper to create a snapshot dict ----------------------------------------
    def _snap(label: str, odds: float | None, prob: float | None,
              snapshot_time: str | None) -> dict[str, Any]:
        base = {
            "event_id": event_id,
            "odds_id": odds_id,
            "source_key": source_key,
            "source_file": source_file,
            "sport": sport,
            "league": league,
            "event_date": event_date,
            "home_team": home_team,
            "away_team": away_team,
            "bookmaker": bookmaker,
            "market": market,
            "market_family": market_family,
            "selection": selection,
            "player_name": player_name,
            "team_name": team_name,
            "line_value": line_val,
            "odds_value": odds,
            "implied_probability": prob,
            "snapshot_label": label,
            "snapshot_time": snapshot_time or now,
            "raw_market_name": raw_market_name,
            "raw_selection_name": raw_selection_name,
            "created_at": now,
            "updated_at": now,
        }
        base["snapshot_id"] = make_line_snapshot_id(base)
        return base

    # Decision snapshot --------------------------------------------------------
    odds_dec = row.get("odds_at_decision_time")
    prob_dec = row.get("market_implied_probability")
    if odds_dec is not None:
        snapshots.append(_snap("decision", float(odds_dec),
                               float(prob_dec) if prob_dec is not None else None,
                               row.get("collected_at")))

    # Opening snapshot ---------------------------------------------------------
    opening_odds = row.get("opening_odds")
    if opening_odds is not None:
        opening_prob = None
        try:
            from automation_scheduler.historical_odds_importers import odds_to_implied_probability
            opening_prob = odds_to_implied_probability(float(opening_odds))
        except Exception:
            pass
        snapshots.append(_snap("opening", float(opening_odds), opening_prob,
                               row.get("opening_time")))

    # Closing snapshot ---------------------------------------------------------
    closing_odds = row.get("closing_odds")
    if closing_odds is not None:
        closing_prob = None
        try:
            from automation_scheduler.historical_odds_importers import odds_to_implied_probability
            closing_prob = odds_to_implied_probability(float(closing_odds))
        except Exception:
            pass
        snapshots.append(_snap("closing", float(closing_odds), closing_prob,
                               row.get("closing_time")))

    # Current snapshot (if present) --------------------------------------------
    current_odds = row.get("current_odds")
    if current_odds is not None:
        current_prob = None
        try:
            from automation_scheduler.historical_odds_importers import odds_to_implied_probability
            current_prob = odds_to_implied_probability(float(current_odds))
        except Exception:
            pass
        snapshots.append(_snap("current", float(current_odds), current_prob,
                               row.get("snapshot_time")))

    return snapshots


# ---------------------------------------------------------------------------
# Upsert snapshots
# ---------------------------------------------------------------------------


def upsert_line_snapshots(
    conn: sqlite3.Connection,
    snapshots: list[dict[str, Any]],
) -> dict[str, Any]:
    """Insert or update (upsert) line snapshots.

    Returns a summary dict with keys ``rows_seen``, ``rows_inserted_or_updated``,
    ``rows_rejected``, ``warnings``.
    """
    seen = len(snapshots)
    inserted_or_updated = 0
    rejected = 0
    warnings: list[str] = []

    for snap in snapshots:
        sid = snap.get("snapshot_id")
        if not sid:
            rejected += 1
            warnings.append("Snapshots without snapshot_id")
            continue
        try:
            conn.execute(
                """INSERT INTO historical_line_snapshots
                   (snapshot_id, event_id, odds_id,
                    source_key, source_file,
                    sport, league, event_date,
                    home_team, away_team,
                    bookmaker, market, market_family,
                    selection, player_name, team_name,
                    line_value, odds_value, implied_probability,
                    snapshot_label, snapshot_time,
                    raw_market_name, raw_selection_name,
                    created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(snapshot_id) DO UPDATE SET
                    updated_at=excluded.updated_at,
                    odds_value=excluded.odds_value,
                    implied_probability=excluded.implied_probability,
                    line_value=excluded.line_value,
                    snapshot_time=excluded.snapshot_time,
                    raw_market_name=excluded.raw_market_name,
                    raw_selection_name=excluded.raw_selection_name""",
                (
                    sid,
                    snap.get("event_id"),
                    snap.get("odds_id"),
                    snap.get("source_key"),
                    snap.get("source_file"),
                    snap.get("sport"),
                    snap.get("league"),
                    snap.get("event_date"),
                    snap.get("home_team"),
                    snap.get("away_team"),
                    snap.get("bookmaker"),
                    snap.get("market"),
                    snap.get("market_family"),
                    snap.get("selection"),
                    snap.get("player_name"),
                    snap.get("team_name"),
                    snap.get("line_value"),
                    snap.get("odds_value"),
                    snap.get("implied_probability"),
                    snap.get("snapshot_label"),
                    snap.get("snapshot_time"),
                    snap.get("raw_market_name"),
                    snap.get("raw_selection_name"),
                    snap.get("created_at"),
                    snap.get("updated_at"),
                ),
            )
            inserted_or_updated += 1
        except Exception as exc:
            rejected += 1
            warnings.append(str(exc))

    conn.commit()
    return {
        "rows_seen": seen,
        "rows_inserted_or_updated": inserted_or_updated,
        "rows_rejected": rejected,
        "warnings": warnings,
    }


def upsert_line_snapshots_for_canonical_rows(
    conn: sqlite3.Connection,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Convenience wrapper: convert each canonical row to snapshots and upsert them.

    Returns the dict from :func:`upsert_line_snapshots`.
    """
    all_snaps: list[dict[str, Any]] = []
    for r in rows:
        all_snaps.extend(canonical_row_to_line_snapshots(r))
    return upsert_line_snapshots(conn, all_snaps)


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


def query_line_snapshots(
    conn: sqlite3.Connection,
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    snapshot_label: str | None = None,
    player_name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Return line snapshots filtered by the given criteria."""
    conditions: list[str] = []
    params: list[Any] = []

    if sport is not None:
        conditions.append("LOWER(sport) = LOWER(?)")
        params.append(sport)
    if league is not None:
        conditions.append("LOWER(league) = LOWER(?)")
        params.append(league)
    if market is not None:
        conditions.append("LOWER(market) = LOWER(?)")
        params.append(market)
    if source_key is not None:
        conditions.append("LOWER(source_key) = LOWER(?)")
        params.append(source_key)
    if snapshot_label is not None:
        label = normalize_snapshot_label(snapshot_label)
        conditions.append("snapshot_label = ?")
        params.append(label)
    if player_name is not None:
        conditions.append("LOWER(player_name) LIKE LOWER(?)")
        params.append(f"%{player_name}%")
    if start_date is not None:
        conditions.append("event_date >= ?")
        params.append(start_date)
    if end_date is not None:
        conditions.append("event_date <= ?")
        params.append(end_date)

    where = " AND ".join(conditions) if conditions else "1=1"
    sql = f"""SELECT * FROM historical_line_snapshots WHERE {where}
              ORDER BY event_date, snapshot_time LIMIT ?
    """
    params.append(limit)
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def summarize_line_movement_store(
    conn: sqlite3.Connection,
) -> dict[str, Any]:
    """Return a summary of the line movement SQLite store."""
    total_snapshots = conn.execute(
        "SELECT COUNT(*) AS cnt FROM historical_line_snapshots"
    ).fetchone()["cnt"]

    counts_by_label = {
        r["label"]: r["cnt"]
        for r in conn.execute(
            "SELECT snapshot_label AS label, COUNT(*) AS cnt FROM "
            "historical_line_snapshots GROUP BY snapshot_label"
        )
    }

    sports = [
        r["sport"]
        for r in conn.execute(
            "SELECT DISTINCT sport FROM historical_line_snapshots ORDER BY sport"
        )
    ]
    leagues = [
        r["league"]
        for r in conn.execute(
            "SELECT DISTINCT league FROM historical_line_snapshots ORDER BY league"
        )
    ]
    markets = [
        r["market"]
        for r in conn.execute(
            "SELECT DISTINCT market FROM historical_line_snapshots ORDER BY market"
        )
    ]
    market_families = [
        r["mf"]
        for r in conn.execute(
            "SELECT DISTINCT market_family AS mf FROM "
            "historical_line_snapshots ORDER BY market_family"
        )
    ]
    source_keys = [
        r["sk"]
        for r in conn.execute(
            "SELECT DISTINCT source_key AS sk FROM "
            "historical_line_snapshots ORDER BY source_key"
        )
    ]
    player_names = [
        r["pn"]
        for r in conn.execute(
            "SELECT DISTINCT player_name AS pn FROM "
            "historical_line_snapshots WHERE player_name IS NOT NULL "
            "ORDER BY player_name"
        )
    ]

    has_opening = counts_by_label.get("opening", 0) > 0
    has_decision = counts_by_label.get("decision", 0) > 0
    has_closing = counts_by_label.get("closing", 0) > 0
    has_current = counts_by_label.get("current", 0) > 0

    line_movement_ready = has_opening and has_decision and has_closing
    clv_ready = line_movement_ready and has_closing

    warnings: list[str] = []
    if not line_movement_ready:
        missing = []
        if not has_opening:
            missing.append("opening")
        if not has_closing:
            missing.append("closing")
        if not has_decision:
            missing.append("decision")
        warnings.append(
            f"Line movement not ready: missing {', '.join(missing)} snapshots."
        )

    return {
        "ok": True,
        "total_snapshots": total_snapshots,
        "opening_snapshots": counts_by_label.get("opening", 0),
        "decision_snapshots": counts_by_label.get("decision", 0),
        "current_snapshots": counts_by_label.get("current", 0),
        "closing_snapshots": counts_by_label.get("closing", 0),
        "sports": sports,
        "leagues": leagues,
        "markets": markets,
        "market_families": market_families,
        "source_keys": source_keys,
        "player_names": player_names,
        "line_movement_ready": line_movement_ready,
        "clv_ready": clv_ready,
        "warnings": warnings,
    }


def calculate_line_movement_readiness(
    summary_or_rows: dict[str, Any] | list[dict[str, Any]],
) -> dict[str, Any]:
    """Return a readiness dict from a summary or a list of rows.

    If passed a dict with keys expected from ``summarize_line_movement_store``,
    use that. Otherwise compute summary first.
    """
    if isinstance(summary_or_rows, dict) and "total_snapshots" in summary_or_rows:
        s = summary_or_rows
    else:
        # compute summary from rows
        from collections import Counter
        labels: Counter[str] = Counter()
        for r in (summary_or_rows or []):
            labels[r.get("snapshot_label", "unknown")] += 1
        s = {
            "opening_snapshots": labels.get("opening", 0),
            "decision_snapshots": labels.get("decision", 0),
            "closing_snapshots": labels.get("closing", 0),
            "current_snapshots": labels.get("current", 0),
        }

    has_opening = s.get("opening_snapshots", 0) > 0
    has_decision = s.get("decision_snapshots", 0) > 0
    has_closing = s.get("closing_snapshots", 0) > 0

    line_movement_ready = has_opening and has_decision and has_closing
    clv_ready = line_movement_ready and has_closing

    missing: list[str] = []
    if not has_opening:
        missing.append("opening")
    if not has_decision:
        missing.append("decision")
    if not has_closing:
        missing.append("closing")

    reason = ("Line movement is ready. CLV is ready." if clv_ready
              else f"Missing: {', '.join(missing)} snapshots")

    return {
        "line_movement_ready": line_movement_ready,
        "clv_ready": clv_ready,
        "has_opening": has_opening,
        "has_decision": has_decision,
        "has_closing": has_closing,
        "reason": reason,
        "missing": missing,
    }


# ---------------------------------------------------------------------------
# Backfill from existing historical odds
# ---------------------------------------------------------------------------


def backfill_line_snapshots_from_historical_odds(
    conn: sqlite3.Connection,
    limit: int = 100000,
) -> dict[str, Any]:
    """Read existing canonical rows from the SQLite historical odds store
    and create corresponding line snapshots.

    Uses :func:`query_historical_odds_rows` (from ``historical_odds_sqlite``).

    Returns a summary dict with ``rows_read``, ``snapshots_created``,
    ``warnings``.
    """
    from automation_scheduler.historical_odds_sqlite import (
        query_historical_odds_rows,
    )
    rows = query_historical_odds_rows(conn, limit=limit)
    if not rows:
        return {"rows_read": 0, "snapshots_created": 0, "warnings": []}
    result = upsert_line_snapshots_for_canonical_rows(conn, rows)
    return {
        "rows_read": len(rows),
        "snapshots_created": result.get("rows_inserted_or_updated", 0),
        "warnings": result.get("warnings", []),
    }
