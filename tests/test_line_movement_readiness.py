"""
Tests for Phase 10H19 line movement readiness layer.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from automation_scheduler.line_movement_readiness import (
    LINE_MOVEMENT_READINESS_VERSION,
    REQUIRED_LINE_MOVEMENT_COLUMNS,
    normalize_line_movement_readiness_value,
    get_sqlite_table_names,
    get_sqlite_table_columns,
    inspect_line_movement_schema,
    build_line_movement_snapshot_coverage,
    build_line_movement_readiness_snapshot,
    describe_line_movement_readiness,
)


# ---------------------------------------------------------------------------
# normalise helper
# ---------------------------------------------------------------------------


def test_normalize_line_movement_readiness_value_handles_common_values():
    assert normalize_line_movement_readiness_value(None) == ""
    assert normalize_line_movement_readiness_value(True) == "Yes"
    assert normalize_line_movement_readiness_value(False) == "No"
    assert normalize_line_movement_readiness_value(42) == "42"
    assert normalize_line_movement_readiness_value(3.14) == "3.14"
    assert normalize_line_movement_readiness_value([1, 2]) == "[1, 2]"
    assert normalize_line_movement_readiness_value({"a": 1}) == '{"a": 1}'
    assert normalize_line_movement_readiness_value("hello") == "hello"


# ---------------------------------------------------------------------------
# get_sqlite_table_names
# ---------------------------------------------------------------------------


def test_get_sqlite_table_names_missing_db_path():
    result = get_sqlite_table_names("")
    assert result["ok"] is False
    assert "missing_db_path" in result["warnings"]


def test_get_sqlite_table_names_missing_file():
    result = get_sqlite_table_names("/nonexistent/foo.db")
    assert result["ok"] is False
    assert "missing_db_file" in result["warnings"]


def test_get_sqlite_table_names_returns_tables(tmp_path):
    db_path = tmp_path / "test_tables.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE foo (x TEXT)")
    conn.execute("CREATE TABLE bar (y TEXT)")
    conn.close()
    result = get_sqlite_table_names(db_path)
    assert result["ok"] is True
    assert result["version"] == LINE_MOVEMENT_READINESS_VERSION
    assert "foo" in result["tables"]
    assert "bar" in result["tables"]
    assert len(result["tables"]) >= 2


# ---------------------------------------------------------------------------
# get_sqlite_table_columns
# ---------------------------------------------------------------------------


def test_get_sqlite_table_columns_missing_table(tmp_path):
    db_path = tmp_path / "no_table.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE foo (x TEXT)")
    conn.close()
    result = get_sqlite_table_columns(db_path, "historical_line_snapshots")
    assert result["ok"] is False
    assert "missing_table" in result["warnings"]


# ---------------------------------------------------------------------------
# inspect_line_movement_schema
# ---------------------------------------------------------------------------


def test_inspect_line_movement_schema_missing_table_not_ready(tmp_path):
    db_path = tmp_path / "missing_table.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE some_other (x TEXT)")
    conn.close()
    result = inspect_line_movement_schema(db_path)
    assert result["table_exists"] is False
    assert result["schema_ready"] is False


def test_inspect_line_movement_schema_ready_when_required_columns_exist(tmp_path):
    db_path = tmp_path / "ready_schema.db"
    conn = sqlite3.connect(str(db_path))
    # create table with all required columns
    cols = ", ".join(REQUIRED_LINE_MOVEMENT_COLUMNS)
    cols += " TEXT, UNIQUE"  # extra columns allowed
    # but we need proper types; use TEXT for all
    col_def = ", ".join(f"{c} TEXT" for c in REQUIRED_LINE_MOVEMENT_COLUMNS)
    conn.execute(f"CREATE TABLE historical_line_snapshots ({col_def})")
    conn.close()
    result = inspect_line_movement_schema(db_path)
    assert result["table_exists"] is True
    assert result["schema_ready"] is True
    assert not result["missing_columns"]


def test_inspect_line_movement_schema_reports_missing_columns(tmp_path):
    db_path = tmp_path / "partial_schema.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE historical_line_snapshots (snapshot_id TEXT, event_id TEXT)")
    conn.close()
    result = inspect_line_movement_schema(db_path)
    assert result["table_exists"] is True
    assert result["schema_ready"] is False
    assert "snapshot_id" not in result["missing_columns"]
    assert "event_id" not in result["missing_columns"]
    assert "sport" in result["missing_columns"]


# ---------------------------------------------------------------------------
# build_line_movement_snapshot_coverage
# ---------------------------------------------------------------------------


def test_build_line_movement_snapshot_coverage_empty_table(tmp_path):
    db_path = tmp_path / "empty_coverage.db"
    cols = ", ".join(REQUIRED_LINE_MOVEMENT_COLUMNS)
    col_def = ", ".join(f"{c} TEXT" for c in REQUIRED_LINE_MOVEMENT_COLUMNS)
    conn = sqlite3.connect(str(db_path))
    conn.execute(f"CREATE TABLE historical_line_snapshots ({col_def})")
    conn.close()
    cov = build_line_movement_snapshot_coverage(db_path)
    assert cov["ok"] is True
    assert cov["total_snapshots"] == 0
    assert cov["linked_snapshot_count"] == 0
    assert cov["unlinked_snapshot_count"] == 0


def test_build_line_movement_snapshot_coverage_counts_snapshots(tmp_path):
    db_path = tmp_path / "count_snaps.db"
    col_def = ", ".join(f"{c} TEXT" for c in REQUIRED_LINE_MOVEMENT_COLUMNS)
    conn = sqlite3.connect(str(db_path))
    conn.execute(f"CREATE TABLE historical_line_snapshots ({col_def})")
    conn.execute(
        "INSERT INTO historical_line_snapshots (snapshot_id,event_id) VALUES (?,?)",
        ("s1", "e1"),
    )
    conn.execute(
        "INSERT INTO historical_line_snapshots (snapshot_id,event_id) VALUES (?,?)",
        ("s2", "e1"),
    )
    conn.close()
    cov = build_line_movement_snapshot_coverage(db_path)
    assert cov["total_snapshots"] == 2
    assert cov["linked_snapshot_count"] == 2
    assert cov["unlinked_snapshot_count"] == 0


def test_build_line_movement_snapshot_coverage_counts_unlinked_snapshots(tmp_path):
    db_path = tmp_path / "unlinked.db"
    col_def = ", ".join(f"{c} TEXT" for c in REQUIRED_LINE_MOVEMENT_COLUMNS)
    conn = sqlite3.connect(str(db_path))
    conn.execute(f"CREATE TABLE historical_line_snapshots ({col_def})")
    conn.execute(
        "INSERT INTO historical_line_snapshots (snapshot_id,event_id) VALUES (?,?)",
        ("s1", "e1"),
    )
    conn.execute(
        "INSERT INTO historical_line_snapshots (snapshot_id,event_id) VALUES (?,?)",
        ("s2", ""),
    )
    conn.close()
    cov = build_line_movement_snapshot_coverage(db_path)
    assert cov["total_snapshots"] == 2
    assert cov["linked_snapshot_count"] == 1
    assert cov["unlinked_snapshot_count"] == 1


# ---------------------------------------------------------------------------
# build_line_movement_readiness_snapshot
# ---------------------------------------------------------------------------


def test_build_line_movement_readiness_snapshot_missing_schema(tmp_path):
    db_path = tmp_path / "no_snaps.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE foo (x TEXT)")
    conn.close()
    result = build_line_movement_readiness_snapshot(db_path)
    assert result["ok"] is True
    assert result["readiness"]["ready"] is False
    assert "missing_schema" in result["readiness"]["reasons"]


def test_build_line_movement_readiness_snapshot_ready_with_snapshots(tmp_path):
    db_path = tmp_path / "fully_ready.db"
    col_def = ", ".join(f"{c} TEXT" for c in REQUIRED_LINE_MOVEMENT_COLUMNS)
    conn = sqlite3.connect(str(db_path))
    conn.execute(f"CREATE TABLE historical_line_snapshots ({col_def})")
    conn.execute(
        "INSERT INTO historical_line_snapshots ("
        "snapshot_id,event_id,odds_id,source_key,source_file,"
        "sport,league,event_date,home_team,away_team,bookmaker,market,"
        "market_family,selection,player_name,team_name,line_value,odds_value,"
        "implied_probability,snapshot_label,snapshot_time,raw_market_name,"
        "raw_selection_name,created_at,updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "s1", "e1", "o1", "src", "file",
            "soccer", "EPL", "2023-01-01", "home", "away", "book", "1X2",
            "moneyline_or_1x2", "Home", None, None, "0", "1.5",
            "0.67", "decision", "2023-01-01T12:00:00Z", "rawMkt", "rawSel",
            "2023-01-01T12:00:00Z", "2023-01-01T12:00:00Z",
        ),
    )
    conn.close()
    result = build_line_movement_readiness_snapshot(db_path)
    assert result["ok"] is True
    assert result["readiness"]["ready"] is True
    assert result["readiness"]["schema_ready"] is True
    assert result["readiness"]["has_snapshots"] is True
    assert result["readiness"]["has_linked_events"] is True
    assert result["readiness"]["has_snapshot_time"] is True
    assert result["readiness"]["has_market_family"] is True
    assert result["readiness"]["has_bookmaker"] is True
    assert result["readiness"]["reasons"] == []


def test_build_line_movement_readiness_snapshot_reasons_for_missing_data(tmp_path):
    db_path = tmp_path / "partial_data.db"
    col_def = ", ".join(f"{c} TEXT" for c in REQUIRED_LINE_MOVEMENT_COLUMNS)
    conn = sqlite3.connect(str(db_path))
    conn.execute(f"CREATE TABLE historical_line_snapshots ({col_def})")
    # insert a row with empty event_id and no bookmaker
    conn.execute(
        "INSERT INTO historical_line_snapshots ("
        "snapshot_id,event_id,snapshot_time,market_family,bookmaker) "
        "VALUES (?,?,?,?,?)",
        ("s1", "", "", "", ""),
    )
    conn.close()
    result = build_line_movement_readiness_snapshot(db_path)
    assert result["ok"] is True
    reasons = result["readiness"]["reasons"]
    assert "missing_linked_events" in reasons
    assert "missing_snapshot_time" in reasons
    assert "missing_market_family" in reasons
    assert "missing_bookmaker" in reasons


# ---------------------------------------------------------------------------
# describe_line_movement_readiness
# ---------------------------------------------------------------------------


def test_describe_line_movement_readiness_mentions_no_vendor_import():
    snapshot = {
        "ok": True,
        "schema": {"schema_ready": True, "missing_columns": []},
        "coverage": {
            "total_snapshots": 0, "linked_snapshot_count": 0,
            "unlinked_snapshot_count": 0, "event_count": 0,
            "sport_count": 0, "market_family_count": 0,
            "bookmaker_count": 0,
            "earliest_snapshot_time": None,
            "latest_snapshot_time": None,
        },
        "readiness": {
            "ready": False, "reasons": ["missing_snapshots"],
        },
    }
    msgs = describe_line_movement_readiness(snapshot)
    combined = " ".join(msgs)
    assert "does not connect to vendors" in combined.lower()
    assert "import paid data" in combined.lower()


def test_describe_line_movement_readiness_mentions_as_of_leakage_guard():
    snapshot = {
        "ok": True,
        "schema": {"schema_ready": True, "missing_columns": []},
        "coverage": {
            "total_snapshots": 10, "linked_snapshot_count": 10,
            "unlinked_snapshot_count": 0, "event_count": 5,
            "sport_count": 1, "market_family_count": 2,
            "bookmaker_count": 1,
            "earliest_snapshot_time": "2023-01-01T00:00:00Z",
            "latest_snapshot_time": "2023-01-01T12:00:00Z",
        },
        "readiness": {
            "ready": True, "reasons": [],
        },
    }
    msgs = describe_line_movement_readiness(snapshot)
    combined = " ".join(msgs)
    assert "snapshot_time <= hypothetical_bet_time" in combined
    assert "look-ahead bias" in combined
