"""
Phase 10K1 Unified Research Warehouse Foundation – store layer.

Safe functions for initialising and inspecting
``research/market_research.db``.

No vendor connectors, no API calls, no external collection logic.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from research.market_research_schema import (
    MARKET_RESEARCH_SCHEMA_VERSION,
    SCHEMA_TABLES,
    get_all_table_names,
)

DEFAULT_DB_FILENAME = "market_research.db"


def get_default_market_research_db_path() -> Path:
    """Return the canonical path ``<research package>/market_research.db``."""
    return Path(__file__).resolve().parent / DEFAULT_DB_FILENAME


def connect_market_research_db(
    db_path: Optional[Path | str] = None,
) -> sqlite3.Connection:
    """Open a sqlite3 connection to *db_path* (default ``get_default_market_research_db_path()``)."""
    if db_path is None:
        db_path = get_default_market_research_db_path()
    return sqlite3.connect(str(db_path))


def initialize_market_research_db(
    db_path: Optional[Path | str] = None,
) -> Path:
    """
    Idempotent initialisation of the market research database.

    1. Creates parent directories if needed.
    2. Executes every CREATE TABLE IF NOT EXISTS statement from the schema module.
    3. Stores ``MARKET_RESEARCH_SCHEMA_VERSION`` in ``schema_metadata``.

    Returns the resolved path to the database.
    """
    if db_path is None:
        db_path = get_default_market_research_db_path()
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = connect_market_research_db(db_path)
    try:
        for create_sql in SCHEMA_TABLES.values():
            conn.execute(create_sql)

        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO schema_metadata (key, value, updated_at) "
            "VALUES (?, ?, ?)",
            ("schema_version", MARKET_RESEARCH_SCHEMA_VERSION, now_iso),
        )
        conn.commit()
    finally:
        conn.close()

    return db_path


def list_market_research_tables(db_path=None) -> list[str]:
    """Return warehouse table names, excluding SQLite internal tables."""
    path = Path(db_path) if db_path is not None else get_default_market_research_db_path()
    if not path.exists():
        return []

    conn = connect_market_research_db(path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = ? ORDER BY name",
            ("table",),
        ).fetchall()
        return sorted(
            name
            for (name,) in rows
            if name and not name.startswith('sqlite_')
        )
    finally:
        conn.close()
def get_market_research_schema_version(
    db_path: Optional[Path | str] = None,
) -> str:
    """Read the ``schema_version`` from the ``schema_metadata`` table."""
    if db_path is None:
        db_path = get_default_market_research_db_path()
    conn = connect_market_research_db(db_path)
    try:
        cursor = conn.execute(
            "SELECT value FROM schema_metadata WHERE key='schema_version'"
        )
        row = cursor.fetchone()
        if row is None:
            return ""
        return str(row[0])
    finally:
        conn.close()


def table_exists(
    table_name: str,
    db_path: Optional[Path | str] = None,
) -> bool:
    """Return *True* if *table_name* exists in the database."""
    return table_name in list_market_research_tables(db_path)


def insert_schema_metadata(
    key: str,
    value: str,
    db_path: Optional[Path | str] = None,
) -> None:
    """Insert or replace a row into ``schema_metadata``."""
    if db_path is None:
        db_path = get_default_market_research_db_path()
    conn = connect_market_research_db(db_path)
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO schema_metadata (key, value, updated_at) "
            "VALUES (?, ?, ?)",
            (key, value, now_iso),
        )
        conn.commit()
    finally:
        conn.close()
