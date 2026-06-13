"""
Phase 10H6 – SQLite Historical Odds Store.

Provides a local SQLite storage layer for validated canonical historical‑odds rows
produced by :mod:`automation_scheduler.historical_odds_importers`.

Uses Python stdlib ``sqlite3`` only.
No SQLAlchemy, no external dependencies, no network calls, no scraping.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation_scheduler.historical_odds_importers import (
    CANONICAL_HISTORICAL_ODDS_OPTIONAL_FIELDS,
    CANONICAL_HISTORICAL_ODDS_REQUIRED_FIELDS,
    SUPPORTED_IMPORTER_KEYS,
    import_historical_odds_file,
    validate_canonical_historical_odds_row,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SQLITE_SCHEMA_VERSION: str = "10H6"

HISTORICAL_ODDS_SQLITE_TABLES: list[str] = [
    "source_imports",
    "historical_events",
    "historical_odds",
    "historical_results",
]

DEFAULT_QUERY_LIMIT: int = 1000

# ---------------------------------------------------------------------------
# Time / id helpers
# ---------------------------------------------------------------------------


def utc_now_iso() -> str:
    """Return current UTC time in ISO‑8601 format."""
    return datetime.now(timezone.utc).isoformat()


def stable_hash_id(prefix: str, parts: list[str]) -> str:
    """Return a deterministic hex hash based on *prefix* and *parts*."""
    raw = prefix + ":" + "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def make_event_id(row: dict[str, Any]) -> str:
    """Create a deterministic event identifier from canonical row fields."""
    return stable_hash_id(
        "evt",
        [
            row.get("source_key", ""),
            row.get("sport", ""),
            row.get("league", ""),
            row.get("event_date", ""),
            row.get("home_team", ""),
            row.get("away_team", ""),
        ],
    )


def make_odds_id(row: dict[str, Any], event_id: str) -> str:
    """Create a deterministic odds identifier."""
    return stable_hash_id(
        "odds",
        [
            event_id,
            row.get("market", ""),
            row.get("selection", ""),
            str(row.get("bookmaker", "")),
        ],
    )


# ---------------------------------------------------------------------------
# Connection & schema
# ---------------------------------------------------------------------------


def connect_historical_odds_db(db_path: str | Path) -> sqlite3.Connection:
    """Open a connection to the SQLite database at *db_path*.

    Returns a ``Connection`` with ``row_factory`` set to ``sqlite3.Row``.
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS source_imports (
    import_id TEXT PRIMARY KEY,
    source_key TEXT,
    source_name TEXT,
    source_file TEXT,
    imported_at TEXT,
    rows_seen INTEGER,
    rows_inserted INTEGER,
    rows_rejected INTEGER,
    warning_total INTEGER,
    projection_ready INTEGER,
    summary_json TEXT
);

CREATE TABLE IF NOT EXISTS historical_events (
    event_id TEXT PRIMARY KEY,
    source_key TEXT NOT NULL,
    source_file TEXT,
    sport TEXT NOT NULL,
    league TEXT NOT NULL,
    season TEXT,
    event_date TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    raw_event_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_odds (
    odds_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    source_key TEXT NOT NULL,
    source_file TEXT,
    sport TEXT NOT NULL,
    league TEXT NOT NULL,
    event_date TEXT NOT NULL,
    bookmaker TEXT,
    market TEXT NOT NULL,
    selection TEXT NOT NULL,
    odds_at_decision_time REAL NOT NULL,
    market_implied_probability REAL NOT NULL,
    opening_odds REAL,
    closing_odds REAL,
    collected_at TEXT,
    raw_market_name TEXT,
    raw_selection_name TEXT,
    raw_row_index INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES historical_events(event_id)
);

CREATE TABLE IF NOT EXISTS historical_results (
    event_id TEXT PRIMARY KEY,
    final_result TEXT NOT NULL,
    home_score REAL,
    away_score REAL,
    winner TEXT,
    profit_loss REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES historical_events(event_id)
);
"""

CREATE_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_historical_odds_sport
    ON historical_odds (sport);
CREATE INDEX IF NOT EXISTS idx_historical_odds_league
    ON historical_odds (league);
CREATE INDEX IF NOT EXISTS idx_historical_odds_market
    ON historical_odds (market);
CREATE INDEX IF NOT EXISTS idx_historical_odds_source_key
    ON historical_odds (source_key);
CREATE INDEX IF NOT EXISTS idx_historical_odds_event_date
    ON historical_odds (event_date);
CREATE INDEX IF NOT EXISTS idx_historical_odds_sport_market_date
    ON historical_odds (sport, market, event_date);
"""


def initialize_historical_odds_db(conn: sqlite3.Connection) -> None:
    """Create all required tables and indexes if they do not exist (idempotent)."""
    conn.executescript(CREATE_TABLES_SQL)
    conn.executescript(CREATE_INDEXES_SQL)
    conn.commit()


# ---------------------------------------------------------------------------
# Inspect tables
# ---------------------------------------------------------------------------


def get_sqlite_table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """Return a dictionary mapping table name to row count."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    counts: dict[str, int] = {}
    for row in cur:
        name: str = row["name"]
        cnt = conn.execute(f"SELECT COUNT(*) AS cnt FROM [{name}]").fetchone()["cnt"]
        counts[name] = cnt
    return counts


# ---------------------------------------------------------------------------
# Insert / upsert canonical rows
# ---------------------------------------------------------------------------


def upsert_canonical_historical_odds_rows(
    conn: sqlite3.Connection,
    rows: list[dict[str, Any]],
    source_file: str | None = None,
) -> dict[str, Any]:
    """Store validated canonical rows in the SQLite store.

    * Invalid rows (according to :func:`validate_canonical_historical_odds_row`)
      are counted and rejected.
    * Valid rows are upserted into ``historical_events``, ``historical_odds``,
      and ``historical_results``.  Duplicate identifiers (same key fields) are
      harmless and will not create extra rows.
    * A summary row is inserted into ``source_imports`` for each call.

    Returns a dict with keys ``ok``, ``rows_seen``, ``rows_inserted``,
    ``rows_rejected``, ``warning_total``, ``import_id``.
    """
    now = utc_now_iso()
    seen = len(rows)
    inserted = 0
    rejected = 0
    warning_total = 0
    last_warnings: list[list[str]] = []

    for row in rows:
        val = validate_canonical_historical_odds_row(row)
        if not val["ok"]:
            rejected += 1
            warning_total += len(val["warnings"])
            last_warnings.append(val["warnings"])
            continue

        event_id = make_event_id(row)
        odds_id = make_odds_id(row, event_id)

        # historical_events ---------------------------------------------------
        home_team = row.get("home_team", "")
        away_team = row.get("away_team", "")
        raw_event_id = row.get("raw_event_id")
        season = row.get("season")

        # upsert: check existence
        existing_event = conn.execute(
            "SELECT event_id FROM historical_events WHERE event_id=?",
            (event_id,),
        ).fetchone()

        if existing_event is None:
            conn.execute(
                """INSERT INTO historical_events
                   (event_id, source_key, source_file, sport, league, season,
                    event_date, home_team, away_team, raw_event_id,
                    created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    event_id,
                    row.get("source_key", ""),
                    source_file or row.get("source_file"),
                    row.get("sport", ""),
                    row.get("league", ""),
                    season,
                    row.get("event_date", ""),
                    home_team,
                    away_team,
                    raw_event_id,
                    now,
                    now,
                ),
            )
        else:
            conn.execute(
                """UPDATE historical_events
                   SET updated_at=?
                   WHERE event_id=?""",
                (now, event_id),
            )

        # historical_odds ----------------------------------------------------
        odds_at = row.get("odds_at_decision_time")
        prob = row.get("market_implied_probability")
        opening = row.get("opening_odds")
        closing = row.get("closing_odds")
        collected_at = row.get("collected_at")
        raw_market_name = row.get("raw_market_name")
        raw_selection_name = row.get("raw_selection_name")
        raw_row_index = row.get("raw_row_index")

        # use UPSERT (INSERT … ON CONFLICT DO UPDATE)
        conn.execute(
            """INSERT INTO historical_odds
               (odds_id, event_id, source_key, source_file,
                sport, league, event_date, bookmaker,
                market, selection,
                odds_at_decision_time, market_implied_probability,
                opening_odds, closing_odds,
                collected_at, raw_market_name, raw_selection_name,
                raw_row_index,
                created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(odds_id) DO UPDATE SET
                updated_at=excluded.updated_at,
                odds_at_decision_time=excluded.odds_at_decision_time,
                market_implied_probability=excluded.market_implied_probability,
                bookmaker=excluded.bookmaker,
                opening_odds=excluded.opening_odds,
                closing_odds=excluded.closing_odds,
                collected_at=excluded.collected_at,
                raw_market_name=excluded.raw_market_name,
                raw_selection_name=excluded.raw_selection_name,
                raw_row_index=excluded.raw_row_index""",
            (
                odds_id,
                event_id,
                row.get("source_key", ""),
                source_file or row.get("source_file"),
                row.get("sport", ""),
                row.get("league", ""),
                row.get("event_date", ""),
                row.get("bookmaker"),
                row.get("market", ""),
                row.get("selection", ""),
                odds_at,
                prob,
                opening,
                closing,
                collected_at,
                raw_market_name,
                raw_selection_name,
                raw_row_index,
                now,
                now,
            ),
        )

        # historical_results --------------------------------------------------
        final_result = row.get("final_result")
        if final_result is None:
            continue  # nothing to store

        home_score = row.get("home_score")
        away_score = row.get("away_score")
        winner = row.get("winner")
        profit_loss = row.get("profit_loss")

        existing_res = conn.execute(
            "SELECT event_id FROM historical_results WHERE event_id=?",
            (event_id,),
        ).fetchone()

        if existing_res is None:
            conn.execute(
                """INSERT INTO historical_results
                   (event_id, final_result, home_score, away_score,
                    winner, profit_loss, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    event_id,
                    final_result,
                    home_score,
                    away_score,
                    winner,
                    profit_loss,
                    now,
                    now,
                ),
            )
        else:
            conn.execute(
                """UPDATE historical_results
                   SET updated_at=?,
                       final_result=?,
                       home_score=?,
                       away_score=?,
                       winner=?,
                       profit_loss=?
                   WHERE event_id=?""",
                (
                    now,
                    final_result,
                    home_score,
                    away_score,
                    winner,
                    profit_loss,
                    event_id,
                ),
            )

        inserted += 1
        warning_total += len(val["warnings"])

    # source_imports record -------------------------------------------------
    projection_ready = 1 if inserted > 0 and rejected == 0 else 0
    import_id = uuid.uuid4().hex
    summary = {
        "rows_seen": seen,
        "rows_inserted": inserted,
        "rows_rejected": rejected,
        "warning_total": warning_total,
        "projection_ready": bool(projection_ready),
    }
    conn.execute(
        """INSERT INTO source_imports
           (import_id, source_key, source_name, source_file, imported_at,
            rows_seen, rows_inserted, rows_rejected, warning_total,
            projection_ready, summary_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            import_id,
            None,
            __name__,
            source_file,
            now,
            seen,
            inserted,
            rejected,
            warning_total,
            projection_ready,
            json.dumps(summary),
        ),
    )
    conn.commit()

    return {
        "ok": rejected == 0,
        "rows_seen": seen,
        "rows_inserted": inserted,
        "rows_rejected": rejected,
        "warning_total": warning_total,
        "import_id": import_id,
    }


# ---------------------------------------------------------------------------
# Import file → SQLite convenience function
# ---------------------------------------------------------------------------


def import_historical_odds_file_to_sqlite(
    conn: sqlite3.Connection,
    source_key: str,
    path: str | Path,
    source_file: str | None = None,
) -> dict[str, Any]:
    """Read a raw odds file with the appropriate importer and store the result.

    Returns the dict from :func:`upsert_canonical_historical_odds_rows`.
    """
    rows = import_historical_odds_file(source_key, path, source_file=source_file)
    return upsert_canonical_historical_odds_rows(
        conn, rows, source_file=source_file or str(path)
    )


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


def query_historical_odds_rows(
    conn: sqlite3.Connection,
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = DEFAULT_QUERY_LIMIT,
) -> list[dict[str, Any]]:
    """Return canonical rows filtered by the given criteria.

    The result is a list of dicts obtained by joining
    ``historical_odds``, ``historical_events``, and ``historical_results``.
    """
    conditions: list[str] = []
    params: list[Any] = []

    if sport is not None:
        conditions.append("LOWER(o.sport) = LOWER(?)")
        params.append(sport)
    if league is not None:
        conditions.append("LOWER(o.league) = LOWER(?)")
        params.append(league)
    if market is not None:
        conditions.append("LOWER(o.market) = LOWER(?)")
        params.append(market)
    if source_key is not None:
        conditions.append("LOWER(o.source_key) = LOWER(?)")
        params.append(source_key)
    if start_date is not None:
        conditions.append("o.event_date >= ?")
        params.append(start_date)
    if end_date is not None:
        conditions.append("o.event_date <= ?")
        params.append(end_date)

    where = " AND ".join(conditions) if conditions else "1=1"
    sql = f"""SELECT
                 o.odds_id,
                 o.event_id,
                 o.source_key,
                 o.source_file,
                 o.sport,
                 o.league,
                 o.event_date,
                 o.bookmaker,
                 o.market,
                 o.selection,
                 o.odds_at_decision_time,
                 o.market_implied_probability,
                 o.opening_odds,
                 o.closing_odds,
                 o.collected_at,
                 o.raw_market_name,
                 o.raw_selection_name,
                 o.raw_row_index,
                 e.season,
                 e.home_team,
                 e.away_team,
                 e.raw_event_id,
                 r.final_result,
                 r.home_score,
                 r.away_score,
                 r.winner,
                 r.profit_loss
              FROM historical_odds o
              LEFT JOIN historical_events e ON e.event_id = o.event_id
              LEFT JOIN historical_results r ON r.event_id = o.event_id
              WHERE {where}
              ORDER BY o.event_date, o.odds_id
              LIMIT ?
    """
    params.append(limit)
    cur = conn.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def summarize_historical_odds_db(conn: sqlite3.Connection) -> dict[str, Any]:
    """Return a summary of the SQLite store contents."""
    counts = get_sqlite_table_counts(conn)

    sports: list[str] = [
        r["sport"]
        for r in conn.execute(
            "SELECT DISTINCT sport FROM historical_odds ORDER BY sport"
        )
    ]
    leagues: list[str] = [
        r["league"]
        for r in conn.execute(
            "SELECT DISTINCT league FROM historical_odds ORDER BY league"
        )
    ]
    markets: list[str] = [
        r["market"]
        for r in conn.execute(
            "SELECT DISTINCT market FROM historical_odds ORDER BY market"
        )
    ]
    sources: list[str] = [
        r["source_key"]
        for r in conn.execute(
            "SELECT DISTINCT source_key FROM historical_odds ORDER BY source_key"
        )
    ]

    total_odds = counts.get("historical_odds", 0)
    total_events = counts.get("historical_events", 0)

    projection_ready = total_odds > 0 and (
        conn.execute(
            "SELECT COUNT(*) AS cnt FROM source_imports WHERE projection_ready=0"
        ).fetchone()["cnt"]
        == 0
    )

    return {
        "ok": True,
        "table_counts": counts,
        "total_odds": total_odds,
        "total_events": total_events,
        "sports": sports,
        "leagues": leagues,
        "markets": markets,
        "sources": sources,
        "projection_ready": projection_ready,
    }


# ---------------------------------------------------------------------------
# Validate store
# ---------------------------------------------------------------------------


def validate_sqlite_store(conn: sqlite3.Connection) -> dict[str, Any]:
    """Verify that the database contains the expected tables and schema version."""
    errors: list[str] = []
    table_names = [
        r["name"]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]
    for required in HISTORICAL_ODDS_SQLITE_TABLES:
        if required not in table_names:
            errors.append(f"missing table {required}")

    if errors:
        return {"ok": False, "errors": errors}
    return {"ok": True, "errors": []}
