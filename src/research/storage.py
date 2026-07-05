from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


MARKET_RESEARCH_SCHEMA_VERSION: str = "10K1"
DEFAULT_DB_FILENAME = "market_research.db"

SCHEMA_TABLES: dict[str, str] = {
    "schema_metadata": """
CREATE TABLE IF NOT EXISTS schema_metadata (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL
)
""",
    "raw_sports_odds": """
CREATE TABLE IF NOT EXISTS raw_sports_odds (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key         TEXT,
    source_name        TEXT,
    source_file        TEXT,
    sport              TEXT,
    league             TEXT,
    event_id           TEXT,
    event_time         TEXT,
    home_team          TEXT,
    away_team          TEXT,
    market             TEXT,
    selection          TEXT,
    odds_american      REAL,
    implied_probability REAL,
    observed_at        TEXT,
    inserted_at        TEXT NOT NULL
)
""",
    "raw_equity_prices": """
CREATE TABLE IF NOT EXISTS raw_equity_prices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key  TEXT,
    symbol      TEXT NOT NULL,
    price       REAL,
    volume      REAL,
    observed_at TEXT,
    inserted_at TEXT NOT NULL
)
""",
    "raw_option_chains": """
CREATE TABLE IF NOT EXISTS raw_option_chains (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key         TEXT,
    underlying_symbol  TEXT NOT NULL,
    option_symbol      TEXT,
    expiration_date    TEXT,
    is_0dte            INTEGER,
    days_to_expiration REAL,
    minutes_to_expiration REAL,
    contract_type      TEXT,
    strike             REAL,
    bid                REAL,
    ask                REAL,
    mid                REAL,
    last               REAL,
    volume             REAL,
    open_interest      REAL,
    implied_volatility REAL,
    delta              REAL,
    gamma              REAL,
    theta              REAL,
    vega               REAL,
    underlying_price   REAL,
    observed_at        TEXT,
    inserted_at        TEXT NOT NULL
)
""",
    "raw_option_quotes": """
CREATE TABLE IF NOT EXISTS raw_option_quotes (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key         TEXT,
    underlying_symbol  TEXT NOT NULL,
    option_symbol      TEXT,
    expiration_date    TEXT,
    is_0dte            INTEGER,
    minutes_to_expiration REAL,
    contract_type      TEXT,
    strike             REAL,
    bid                REAL,
    ask                REAL,
    mid                REAL,
    spread_pct         REAL,
    premium            REAL,
    contract_multiplier REAL,
    volume             REAL,
    open_interest      REAL,
    implied_volatility REAL,
    delta              REAL,
    gamma              REAL,
    theta              REAL,
    vega               REAL,
    moneyness          REAL,
    distance_to_strike REAL,
    observed_at        TEXT,
    inserted_at        TEXT NOT NULL
)
""",
    "raw_prediction_markets": """
CREATE TABLE IF NOT EXISTS raw_prediction_markets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key  TEXT,
    event_id    TEXT,
    market_id   TEXT,
    contract_id TEXT,
    question    TEXT,
    outcome     TEXT,
    yes_price   REAL,
    no_price    REAL,
    observed_at TEXT,
    inserted_at TEXT NOT NULL
)
""",
    "raw_macro_liquidity": """
CREATE TABLE IF NOT EXISTS raw_macro_liquidity (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key  TEXT,
    indicator   TEXT,
    value       REAL,
    observed_at TEXT,
    inserted_at TEXT NOT NULL
)
""",
    "raw_order_books": """
CREATE TABLE IF NOT EXISTS raw_order_books (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_key    TEXT,
    market_type   TEXT,
    instrument_id TEXT,
    bid           REAL,
    ask           REAL,
    bid_size      REAL,
    ask_size      REAL,
    observed_at   TEXT,
    inserted_at   TEXT NOT NULL
)
""",
    "features_sports": """
CREATE TABLE IF NOT EXISTS features_sports (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sport         TEXT,
    event_id      TEXT,
    feature_name  TEXT,
    feature_value REAL,
    as_of_time    TEXT,
    inserted_at   TEXT NOT NULL
)
""",
    "features_equities": """
CREATE TABLE IF NOT EXISTS features_equities (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol        TEXT,
    feature_name  TEXT,
    feature_value REAL,
    as_of_time    TEXT,
    inserted_at   TEXT NOT NULL
)
""",
    "features_0dte_options": """
CREATE TABLE IF NOT EXISTS features_0dte_options (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    underlying_symbol TEXT,
    option_symbol     TEXT,
    expiration_date   TEXT,
    feature_name      TEXT,
    feature_value     REAL,
    as_of_time        TEXT,
    inserted_at       TEXT NOT NULL
)
""",
    "features_prediction_markets": """
CREATE TABLE IF NOT EXISTS features_prediction_markets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id     TEXT,
    contract_id   TEXT,
    feature_name  TEXT,
    feature_value REAL,
    as_of_time    TEXT,
    inserted_at   TEXT NOT NULL
)
""",
    "model_predictions": """
CREATE TABLE IF NOT EXISTS model_predictions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name        TEXT,
    model_version     TEXT,
    market_type       TEXT,
    instrument_id     TEXT,
    prediction_value  REAL,
    confidence        REAL,
    edge              REAL,
    as_of_time        TEXT,
    inserted_at       TEXT NOT NULL
)
""",
    "backtest_runs": """
CREATE TABLE IF NOT EXISTS backtest_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT UNIQUE,
    model_name  TEXT,
    model_version TEXT,
    market_type TEXT,
    started_at  TEXT,
    finished_at TEXT,
    config_json TEXT,
    inserted_at TEXT NOT NULL
)
""",
    "backtest_trades": """
CREATE TABLE IF NOT EXISTS backtest_trades (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT,
    market_type   TEXT,
    instrument_id TEXT,
    side          TEXT,
    entry_price   REAL,
    exit_price    REAL,
    quantity      REAL,
    pnl           REAL,
    opened_at     TEXT,
    closed_at     TEXT,
    inserted_at   TEXT NOT NULL
)
""",
    "option_backtest_trades": """
CREATE TABLE IF NOT EXISTS option_backtest_trades (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id            TEXT,
    underlying_symbol TEXT,
    option_symbol     TEXT,
    expiration_date   TEXT,
    is_0dte           INTEGER,
    contract_type     TEXT,
    strike            REAL,
    entry_bid         REAL,
    entry_ask         REAL,
    entry_mid         REAL,
    exit_bid          REAL,
    exit_ask          REAL,
    exit_mid          REAL,
    contracts         REAL,
    premium_risk      REAL,
    max_loss          REAL,
    spread_pct_at_entry REAL,
    entry_time        TEXT,
    exit_time         TEXT,
    forced_exit       INTEGER,
    pnl               REAL,
    inserted_at       TEXT NOT NULL
)
""",
    "arbitrage_opportunities": """
CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    market_type       TEXT,
    opportunity_type  TEXT,
    instrument_group  TEXT,
    implied_sum       REAL,
    arbitrage_margin  REAL,
    expected_profit   REAL,
    detected_at       TEXT,
    inserted_at       TEXT NOT NULL
)
""",
    "settlements": """
CREATE TABLE IF NOT EXISTS settlements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    market_type     TEXT,
    instrument_id   TEXT,
    result          TEXT,
    settlement_price REAL,
    settled_at      TEXT,
    inserted_at     TEXT NOT NULL
)
""",
    "performance_metrics": """
CREATE TABLE IF NOT EXISTS performance_metrics (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT,
    market_type   TEXT,
    metric_name   TEXT,
    metric_value  REAL,
    calculated_at TEXT,
    inserted_at   TEXT NOT NULL
)
""",
}


@dataclass(slots=True, frozen=True)
class ResearchSchemaDescriptor:
    schema_version: str
    table_names: tuple[str, ...]
    local_only: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "table_names": list(self.table_names),
            "local_only": self.local_only,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class ResearchStoreDescriptor:
    db_filename: str
    schema_version: str
    local_only: bool = True
    path: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "db_filename": self.db_filename,
            "schema_version": self.schema_version,
            "local_only": self.local_only,
            "path": self.path,
            "metadata": dict(self.metadata),
        }


def get_all_table_names() -> list[str]:
    return list(SCHEMA_TABLES.keys())


def get_create_sql(table_name: str) -> str:
    return SCHEMA_TABLES[table_name]


def describe_research_schema(
    *,
    metadata: Mapping[str, Any] | None = None,
) -> ResearchSchemaDescriptor:
    return ResearchSchemaDescriptor(
        schema_version=MARKET_RESEARCH_SCHEMA_VERSION,
        table_names=tuple(get_all_table_names()),
        metadata=dict(metadata or {}),
    )


def describe_research_store(
    *,
    path: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ResearchStoreDescriptor:
    return ResearchStoreDescriptor(
        db_filename=DEFAULT_DB_FILENAME,
        schema_version=MARKET_RESEARCH_SCHEMA_VERSION,
        path=path,
        metadata=dict(metadata or {}),
    )


def get_default_market_research_db_path() -> Path:
    return Path(__file__).resolve().parent / DEFAULT_DB_FILENAME


def connect_market_research_db(db_path: Path | str | None = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = get_default_market_research_db_path()
    return sqlite3.connect(str(db_path))


def initialize_market_research_db(db_path: Path | str | None = None) -> Path:
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
            "INSERT OR REPLACE INTO schema_metadata (key, value, updated_at) VALUES (?, ?, ?)",
            ("schema_version", MARKET_RESEARCH_SCHEMA_VERSION, now_iso),
        )
        conn.commit()
    finally:
        conn.close()

    return db_path


def list_market_research_tables(db_path: Path | str | None = None) -> list[str]:
    path = Path(db_path) if db_path is not None else get_default_market_research_db_path()
    if not path.exists():
        return []

    conn = connect_market_research_db(path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = ? ORDER BY name",
            ("table",),
        ).fetchall()
        return sorted(name for (name,) in rows if name and not name.startswith("sqlite_"))
    finally:
        conn.close()


def get_market_research_schema_version(db_path: Path | str | None = None) -> str:
    if db_path is None:
        db_path = get_default_market_research_db_path()
    conn = connect_market_research_db(db_path)
    try:
        cursor = conn.execute("SELECT value FROM schema_metadata WHERE key='schema_version'")
        row = cursor.fetchone()
        if row is None:
            return ""
        return str(row[0])
    finally:
        conn.close()


def table_exists(table_name: str, db_path: Path | str | None = None) -> bool:
    return table_name in list_market_research_tables(db_path)


def insert_schema_metadata(key: str, value: str, db_path: Path | str | None = None) -> None:
    if db_path is None:
        db_path = get_default_market_research_db_path()
    conn = connect_market_research_db(db_path)
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO schema_metadata (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, now_iso),
        )
        conn.commit()
    finally:
        conn.close()

