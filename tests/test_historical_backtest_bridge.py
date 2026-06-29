"""
Tests for automation_scheduler/historical_backtest_bridge.py.

Uses tmp_path SQLite databases and tiny canonical rows.
No external network, no scraping, no database writes to permanent locations.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

import pytest
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.streamlit_dashboard_facade import build_canonical_historical_odds_row, CANONICAL_HISTORICAL_ODDS_REQUIRED_FIELDS
from src.services.streamlit_dashboard_facade import connect_historical_odds_db, initialize_historical_odds_db, query_historical_odds_rows, upsert_canonical_historical_odds_rows
from src.services.streamlit_dashboard_facade import DEFAULT_HISTORICAL_MODEL_ID, DEFAULT_SQLITE_BACKTEST_LIMIT, HISTORICAL_BACKTEST_BRIDGE_VERSION, query_sqlite_backtest_rows, run_sqlite_historical_backtest, sqlite_odds_row_to_backtest_row, sqlite_odds_rows_to_backtest_rows, summarize_sqlite_historical_backtest, get_sqlite_backtest_filter_options

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_valid_rows() -> list[dict]:
    row1 = build_canonical_historical_odds_row(
        source_name="TestSource",
        source_key="football_data_uk",
        source_file="test.csv",
        sport="soccer",
        league="E0",
        event_date="2023-08-12",
        home_team="TeamA",
        away_team="TeamB",
        market="1x2",
        selection="home",
        odds_at_decision_time=2.0,
        final_result="H",
    )
    row2 = build_canonical_historical_odds_row(
        source_name="TestSource",
        source_key="sportsbookreview_scraper",
        source_file="test2.csv",
        sport="baseball",
        league="MLB",
        event_date="2024-06-01",
        home_team="Yankees",
        away_team="RedSox",
        market="moneyline",
        selection="Yankees",
        odds_at_decision_time=-110,
        final_result="W",
    )
    return [row1, row2]


def _populate_db(conn: sqlite3.Connection) -> None:
    initialize_historical_odds_db(conn)
    rows = _make_valid_rows()
    result = upsert_canonical_historical_odds_rows(conn, rows, source_file="multi.csv")
    assert result["rows_inserted"] == 2


# ---------------------------------------------------------------------------
# 1. sqlite_odds_row_to_backtest_row creates row with expected fields
# ---------------------------------------------------------------------------


def test_sqlite_row_to_backtest_row(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        _populate_db(conn)
        raw_rows = query_historical_odds_rows(conn)
        assert len(raw_rows) == 2

        bt = sqlite_odds_row_to_backtest_row(raw_rows[0])
        assert "event_id" in bt
        assert "source_key" in bt
        assert "sport" in bt
        assert "league" in bt
        assert "market" in bt
        assert "selection" in bt
        assert bt["odds_at_decision_time"] is not None
        assert 0.0 <= bt["model_probability"] <= 1.0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 2. features_known_at_decision_time excludes forbidden fields
# ---------------------------------------------------------------------------


def test_features_exclude_leakage(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        _populate_db(conn)
        raw_rows = query_historical_odds_rows(conn)
        bt = sqlite_odds_row_to_backtest_row(raw_rows[0])

        feat = bt.get("features_known_at_decision_time", {})
        forbidden = {"final_result", "winner", "home_score", "away_score",
                     "profit_loss", "closing_line", "closing_odds", "clv"}
        for f in forbidden:
            assert f not in feat, f"feature contains forbidden key {f!r}"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 3. query_sqlite_backtest_rows returns converted rows
# ---------------------------------------------------------------------------


def test_query_sqlite_backtest_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        _populate_db(conn)
        bt_rows = query_sqlite_backtest_rows(conn)
        assert len(bt_rows) == 2
        for r in bt_rows:
            assert "source_key" in r
            assert "sport" in r
            assert "market" in r
            assert r["model_probability"] is not None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 4. get_sqlite_backtest_filter_options returns correct structure
# ---------------------------------------------------------------------------


def test_get_filter_options(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        _populate_db(conn)
        opts = get_sqlite_backtest_filter_options(conn)
        assert "sports" in opts
        assert "leagues" in opts
        assert "markets" in opts
        assert "source_keys" in opts
        assert opts["event_date_min"] is not None
        assert opts["event_date_max"] is not None
        assert opts["total_odds"] > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 5. run_sqlite_historical_backtest returns ok True and includes summary
# ---------------------------------------------------------------------------


def test_run_sqlite_historical_backtest(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        _populate_db(conn)
        result = run_sqlite_historical_backtest(conn)
        assert result["ok"] is True
        assert result["rows_loaded"] == 2
        assert result["rows_converted"] == 2
        assert "backtest_result" in result
        assert "projection_summary" in result
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 6. summarize_sqlite_historical_backtest returns compact stable keys
# ---------------------------------------------------------------------------


def test_summarize_backtest(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        _populate_db(conn)
        result = run_sqlite_historical_backtest(conn)
        summary = summarize_sqlite_historical_backtest(result)
        for key in ("ok", "model_id", "rows_loaded", "rows_converted",
                     "bets", "no_bets", "profit_loss", "roi_percent",
                     "max_drawdown_percent", "sports", "leagues",
                     "markets", "source_keys", "projection_ready", "reason"):
            assert key in summary, f"missing key {key!r}"
        # Even if backtest produces no bets, summary should have zero values.
        assert summary["projection_ready"] is True
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 7. query filters work for sport, league, market, source_key, date range
# ---------------------------------------------------------------------------


def test_query_filters_work(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        _populate_db(conn)
        # sport filter
        bt_rows = query_sqlite_backtest_rows(conn, sport="soccer")
        assert len(bt_rows) == 1
        # league filter (case‑insensitive)
        bt_rows = query_sqlite_backtest_rows(conn, league="MLB")
        assert len(bt_rows) == 1
        # market filter
        bt_rows = query_sqlite_backtest_rows(conn, market="1x2")
        assert len(bt_rows) == 1
        # source_key filter
        bt_rows = query_sqlite_backtest_rows(conn, source_key="football_data_uk")
        assert len(bt_rows) == 1
        # date range
        bt_rows = query_sqlite_backtest_rows(
            conn, start_date="2023-01-01", end_date="2023-12-31"
        )
        assert len(bt_rows) == 1
    finally:
        conn.close()
