"""
Phase 10K1 Uniﬁed Research Warehouse Foundation – tests.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Generator

import pytest

# ------------------------------------------------------------------
# Import the module(s) under test
# ------------------------------------------------------------------
from src.research.storage import (
    MARKET_RESEARCH_SCHEMA_VERSION,
    get_all_table_names,
    get_default_market_research_db_path,
    initialize_market_research_db,
    list_market_research_tables,
    get_market_research_schema_version,
    table_exists,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
_TABLES_WITH_0DTE_FIELDS = {"raw_option_chains", "raw_option_quotes"}
_0DTE_COLUMNS_CHAINS = {
    "underlying_symbol",
    "option_symbol",
    "expiration_date",
    "is_0dte",
    "days_to_expiration",
    "minutes_to_expiration",
    "contract_type",
    "strike",
    "bid",
    "ask",
    "mid",
    "implied_volatility",
    "delta",
    "gamma",
    "theta",
    "vega",
}
_0DTE_COLUMNS_QUOTES = {
    "spread_pct",
    "premium",
    "contract_multiplier",
    "moneyness",
    "distance_to_strike",
}


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Return a temporary path for a market_research.db (file not yet created)."""
    return tmp_path / "market_research.db"


# ------------------------------------------------------------------
# Import‑time tests (no database created)
# ------------------------------------------------------------------
class TestImportDoesNotCreateDb:
    def test_default_path_ends_with_market_research_db(self) -> None:
        path = get_default_market_research_db_path()
        assert path.name == "market_research.db"
        assert path.parts[-2] == "research"
        assert path.parts[-3] == "src"

    def test_import_does_not_create_database(self) -> None:
        path = get_default_market_research_db_path()
        assert not path.exists(), (
            "Importing research.market_research_store should NOT create the database file."
        )


# ------------------------------------------------------------------
# Initialisation tests (using tmp_path)
# ------------------------------------------------------------------
class TestInitialize:
    def test_creates_db_and_all_tables(self, tmp_db_path: Path) -> None:
        created = initialize_market_research_db(tmp_db_path)
        assert created == tmp_db_path
        assert tmp_db_path.exists()

        tables = list_market_research_tables(tmp_db_path)
        required = set(get_all_table_names())
        for t in required:
            assert t in tables, f"Missing table: {t}"
        # Ensure no extra unexpected tables (sqlite internals are filtered)
        user_tables = {t for t in tables if t not in ("schema_metadata",)}  # schema_metadata is user table
        user_tables.discard("schema_metadata")
        assert user_tables == required - {"schema_metadata"}

    def test_schema_version_stored(self, tmp_db_path: Path) -> None:
        initialize_market_research_db(tmp_db_path)
        version = get_market_research_schema_version(tmp_db_path)
        assert version == MARKET_RESEARCH_SCHEMA_VERSION

    def test_initialization_is_idempotent(self, tmp_db_path: Path) -> None:
        p1 = initialize_market_research_db(tmp_db_path)
        p2 = initialize_market_research_db(tmp_db_path)
        assert p1 == p2
        tables = list_market_research_tables(tmp_db_path)
        assert "sqlite_sequence" not in tables
        assert sorted(tables) == sorted(get_all_table_names())
        # re-invoke does not cause errors
        version = get_market_research_schema_version(tmp_db_path)
        assert version == MARKET_RESEARCH_SCHEMA_VERSION

    def test_table_exists_true_after_init(self, tmp_db_path: Path) -> None:
        initialize_market_research_db(tmp_db_path)
        for t in get_all_table_names():
            assert table_exists(t, tmp_db_path)

    def test_table_exists_false_before_init(self, tmp_db_path: Path) -> None:
        assert not table_exists("raw_sports_odds", tmp_db_path)

    def test_insert_schema_metadata(self, tmp_db_path: Path) -> None:
        initialize_market_research_db(tmp_db_path)
        from src.research.storage import insert_schema_metadata
        insert_schema_metadata("test_key", "test_value", tmp_db_path)
        # verify through raw SQL
        conn = sqlite3.connect(str(tmp_db_path))
        try:
            row = conn.execute(
                "SELECT value FROM schema_metadata WHERE key='test_key'"
            ).fetchone()
            assert row is not None
            assert row[0] == "test_value"
        finally:
            conn.close()


# ------------------------------------------------------------------
# 0DTE-specific schema checks
# ------------------------------------------------------------------
class TestSchema0DTEColumns:
    @pytest.fixture(autouse=True)
    def init_db(self, tmp_db_path: Path) -> None:
        initialize_market_research_db(tmp_db_path)
        self._db_path = tmp_db_path

    def _get_column_names(self, table: str) -> set[str]:
        conn = sqlite3.connect(str(self._db_path))
        try:
            cursor = conn.execute(f"PRAGMA table_info({table})")
            return {row[1] for row in cursor.fetchall()}
        finally:
            conn.close()

    def test_raw_option_chains_includes_0dte_columns(self) -> None:
        cols = self._get_column_names("raw_option_chains")
        for field in _0DTE_COLUMNS_CHAINS:
            assert field in cols, f"Missing 0DTE column {field!r} in raw_option_chains"

    def test_raw_option_quotes_includes_0dte_columns(self) -> None:
        cols = self._get_column_names("raw_option_quotes")
        for field in _0DTE_COLUMNS_QUOTES:
            assert field in cols, f"Missing 0DTE column {field!r} in raw_option_quotes"

    def test_no_table_named_stocks_as_primary_options_table(self) -> None:
        """No table with only 'stocks' as the primary options table."""
        tables = list_market_research_tables(self._db_path)
        assert "stocks" not in tables, (
            "Table 'stocks' is not allowed as the primary options storage. "
            "Use raw_option_chains / raw_option_quotes."
        )


# ------------------------------------------------------------------
# Safety tests – no connector/vendor/scraper imports
# ------------------------------------------------------------------
class TestNoForbiddenDependencies:
    """Check that the research modules do not import vendor/API/scraper modules."""

    def test_market_research_schema_no_forbidden_imports(self) -> None:
        import src.research.storage as mod
        src = mod.__file__ or ""
        content = Path(src).read_text(encoding="utf-8")
        forbidden = [
            "requests",
            "httpx",
            "soup",
            "scraper",
            "selenium",
            "yfinance",
            "streamlit",
            "pandas",
        ]
        for token in forbidden:
            assert token not in content, f"Forbidden import/token {token!r} found in src/research/storage.py"

    def test_market_research_store_no_forbidden_imports(self) -> None:
        import src.research.storage as mod
        src = mod.__file__ or ""
        content = Path(src).read_text(encoding="utf-8")
        forbidden = [
            "requests",
            "httpx",
            "soup",
            "scraper",
            "selenium",
            "yfinance",
            "streamlit",
            "pandas",
        ]
        for token in forbidden:
            assert token not in content, f"Forbidden import/token {token!r} found in src/research/storage.py"
