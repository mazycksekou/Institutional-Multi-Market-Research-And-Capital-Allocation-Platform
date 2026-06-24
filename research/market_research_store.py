from __future__ import annotations

import sqlite3
from pathlib import Path

from src.research.storage import (
    DEFAULT_DB_FILENAME,
    MARKET_RESEARCH_SCHEMA_VERSION,
    SCHEMA_TABLES,
    connect_market_research_db as _connect_market_research_db,
    get_all_table_names,
    get_create_sql,
    initialize_market_research_db as _initialize_market_research_db,
    insert_schema_metadata as _insert_schema_metadata,
    list_market_research_tables as _list_market_research_tables,
    table_exists as _table_exists,
)


def get_default_market_research_db_path() -> Path:
    """Return the legacy canonical path ``<research package>/market_research.db``."""
    return Path(__file__).resolve().parent / DEFAULT_DB_FILENAME


def connect_market_research_db(db_path: Path | str | None = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = get_default_market_research_db_path()
    return _connect_market_research_db(db_path)


def initialize_market_research_db(db_path: Path | str | None = None) -> Path:
    if db_path is None:
        db_path = get_default_market_research_db_path()
    return _initialize_market_research_db(db_path)


def list_market_research_tables(db_path=None) -> list[str]:
    if db_path is None:
        db_path = get_default_market_research_db_path()
    return _list_market_research_tables(db_path)


def get_market_research_schema_version(db_path: Path | str | None = None) -> str:
    if db_path is None:
        db_path = get_default_market_research_db_path()
    conn = _connect_market_research_db(db_path)
    try:
        if not _table_exists("schema_metadata", db_path):
            return ""
        cursor = conn.execute("SELECT value FROM schema_metadata WHERE key='schema_version'")
        row = cursor.fetchone()
        if row is None:
            return ""
        return str(row[0])
    finally:
        conn.close()


def table_exists(table_name: str, db_path: Path | str | None = None) -> bool:
    if db_path is None:
        db_path = get_default_market_research_db_path()
    return _table_exists(table_name, db_path)


def insert_schema_metadata(key: str, value: str, db_path: Path | str | None = None) -> None:
    if db_path is None:
        db_path = get_default_market_research_db_path()
    _insert_schema_metadata(key, value, db_path)


__all__ = [
    "DEFAULT_DB_FILENAME",
    "MARKET_RESEARCH_SCHEMA_VERSION",
    "SCHEMA_TABLES",
    "connect_market_research_db",
    "get_all_table_names",
    "get_create_sql",
    "get_default_market_research_db_path",
    "get_market_research_schema_version",
    "initialize_market_research_db",
    "insert_schema_metadata",
    "list_market_research_tables",
    "table_exists",
]
