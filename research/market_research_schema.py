"""
Phase 10K1 Unified Research Warehouse Foundation.

Defines the master schema (CREATE TABLE statements) for
``research/market_research.db``.

One database, many clean tables.
No vendor connectors, no API calls, no scraper logic.
"""

from typing import Dict

MARKET_RESEARCH_SCHEMA_VERSION: str = "10K1"

# ---------------------------------------------------------------------------
# CREATE TABLE statements (IF NOT EXISTS so that initialize is idempotent)
# ---------------------------------------------------------------------------
SCHEMA_TABLES: Dict[str, str] = {
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


def get_all_table_names() -> list[str]:
    """Return the canonical list of table names in the schema."""
    return list(SCHEMA_TABLES.keys())


def get_create_sql(table_name: str) -> str:
    """Return the CREATE TABLE SQL for *table_name*."""
    return SCHEMA_TABLES[table_name]
