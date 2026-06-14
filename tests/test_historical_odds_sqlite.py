"""
Tests for automation_scheduler/historical_odds_sqlite.py.

Uses pytest tmp_path fixtures for temporary SQLite databases.
No external network, no downloading, no scraping.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
from pathlib import Path

import pytest
import sqlite3

# ensure the parent package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from automation_scheduler.historical_odds_importers import (
    build_canonical_historical_odds_row,
    import_football_data_csv,
)
from automation_scheduler.historical_odds_sqlite import (
    DEFAULT_QUERY_LIMIT,
    HISTORICAL_ODDS_SQLITE_TABLES,
    SQLITE_SCHEMA_VERSION,
    connect_historical_odds_db,
    get_sqlite_table_counts,
    initialize_historical_odds_db,
    import_historical_odds_file_to_sqlite,
    make_event_id,
    make_odds_id,
    query_historical_odds_rows,
    stable_hash_id,
    summarize_historical_odds_db,
    upsert_canonical_historical_odds_rows,
    validate_sqlite_store,
    utc_now_iso,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)


def _make_valid_row() -> dict:
    return build_canonical_historical_odds_row(
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


# ---------------------------------------------------------------------------
# 1. initialize_historical_odds_db creates all required tables
# ---------------------------------------------------------------------------


def test_initialize_creates_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        initialize_historical_odds_db(conn)
        table_names = [
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        ]
        for t in HISTORICAL_ODDS_SQLITE_TABLES:
            assert t in table_names
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 2. upsert inserts valid row into events, odds, results, source_imports
# ---------------------------------------------------------------------------


def test_upsert_valid_row(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        initialize_historical_odds_db(conn)
        row = _make_valid_row()
        result = upsert_canonical_historical_odds_rows(conn, [row], source_file="test.csv")
        assert result["rows_inserted"] == 1
        assert result["rows_rejected"] == 0
        counts = get_sqlite_table_counts(conn)
        assert counts["historical_events"] == 1
        assert counts["historical_odds"] == 1
        assert counts["historical_results"] == 1
        assert counts["source_imports"] == 1
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 3. inserting same row twice is idempotent
# ---------------------------------------------------------------------------


def test_upsert_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        initialize_historical_odds_db(conn)
        row = _make_valid_row()
        upsert_canonical_historical_odds_rows(conn, [row], source_file="test.csv")
        upsert_canonical_historical_odds_rows(conn, [row], source_file="test.csv")
        counts = get_sqlite_table_counts(conn)
        assert counts["historical_odds"] == 1
        assert counts["source_imports"] == 2
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 4. invalid row rejected
# ---------------------------------------------------------------------------


def test_upsert_rejects_invalid(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        initialize_historical_odds_db(conn)
        bad_row = build_canonical_historical_odds_row(source_name="x")
        result = upsert_canonical_historical_odds_rows(conn, [bad_row], source_file="bad.csv")
        assert result["rows_inserted"] == 0
        assert result["rows_rejected"] == 1
        counts = get_sqlite_table_counts(conn)
        assert counts["historical_odds"] == 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 5. query filters work
# ---------------------------------------------------------------------------


def test_query_filters(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        initialize_historical_odds_db(conn)
        row1 = _make_valid_row()
        # row2 must be fully valid (include final_result) to avoid rejection
        row2 = build_canonical_historical_odds_row(
            source_name="Other",
            source_key="sportsbookreview_scraper",
            source_file="other.csv",
            sport="baseball",
            league="MLB",
            event_date="2024-06-01",
            home_team="Yankees",
            away_team="RedSox",
            market="moneyline",
            selection="Yankees",
            odds_at_decision_time=-110,
            final_result="H",
        )
        result = upsert_canonical_historical_odds_rows(
            conn, [row1, row2], source_file="multi.csv"
        )
        # ensure both rows were inserted, none rejected
        assert result["rows_inserted"] == 2
        assert result["rows_rejected"] == 0

        # sport filter
        rows = query_historical_odds_rows(conn, sport="soccer")
        assert len(rows) == 1

        # league filter (case‑insensitive)
        rows = query_historical_odds_rows(conn, league="MLB")
        assert len(rows) == 1

        # market filter
        rows = query_historical_odds_rows(conn, market="1x2")
        assert len(rows) == 1

        # source_key filter
        rows = query_historical_odds_rows(conn, source_key="football_data_uk")
        assert len(rows) == 1

        # date range
        rows = query_historical_odds_rows(conn, start_date="2023-01-01", end_date="2023-12-31")
        assert len(rows) == 1
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 6. summarize works
# ---------------------------------------------------------------------------


def test_summarize(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        initialize_historical_odds_db(conn)
        row = _make_valid_row()
        upsert_canonical_historical_odds_rows(conn, [row], source_file="test.csv")
        summary = summarize_historical_odds_db(conn)
        assert summary["ok"] is True
        assert summary["total_odds"] == 1
        assert "soccer" in summary["sports"]
        assert "E0" in summary["leagues"]
        assert "1x2" in summary["markets"]
        assert "football_data_uk" in summary["sources"]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 7. import_historical_odds_file_to_sqlite works with Football-Data CSV
# ---------------------------------------------------------------------------


def test_import_football_csv_via_store(tmp_path: Path) -> None:
    csv_path = tmp_path / "test_foot.csv"
    header = [
        "Div", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
        "B365H", "B365D", "B365A",
    ]
    data = [
        ["E0", "2023-08-12", "Arsenal", "Chelsea", "3", "1", "H", "1.50", "4.00", "6.50"],
    ]
    _write_csv(csv_path, header, data)

    db_path = tmp_path / "store.db"
    conn = connect_historical_odds_db(db_path)
    try:
        initialize_historical_odds_db(conn)
        res = import_historical_odds_file_to_sqlite(
            conn, "football_data_uk", csv_path, source_file="test_foot.csv"
        )
        assert res["rows_inserted"] == 3  # home, draw, away
        counts = get_sqlite_table_counts(conn)
        assert counts["historical_odds"] == 3
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 8. validate_sqlite_store
# ---------------------------------------------------------------------------


def test_validate_store(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = connect_historical_odds_db(db_path)
    try:
        initialize_historical_odds_db(conn)
        val = validate_sqlite_store(conn)
        assert val["ok"] is True
        assert val["errors"] == []
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 9. stable IDs deterministic
# ---------------------------------------------------------------------------


def test_stable_ids_deterministic() -> None:
    row = _make_valid_row()
    eid1 = make_event_id(row)
    eid2 = make_event_id(row)
    assert eid1 == eid2

    oid1 = make_odds_id(row, eid1)
    oid2 = make_odds_id(row, eid1)
    assert oid1 == oid2


def test_stable_hash_id_deterministic() -> None:
    h1 = stable_hash_id("test", ["a", "b"])
    h2 = stable_hash_id("test", ["a", "b"])
    assert h1 == h2


def test_event_date_min_max_correct_after_format_normalization(tmp_path: Path) -> None:
    csv_content = (
        "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"
        "E0,31/08/2024,Arsenal,Chelsea,3,1,H,1.5,4.0,6.5\n"
        "E1,01/01/2025,ManU,Liverpool,0,0,D,2.0,3.0,4.0\n"
    )
    csv_path = tmp_path / "date_test.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    db_path = tmp_path / "date_store.db"
    conn = connect_historical_odds_db(db_path)
    initialize_historical_odds_db(conn)
    import_historical_odds_file_to_sqlite(conn, "football_data_uk", csv_path)
    cursor = conn.execute("SELECT MIN(event_date) AS dmin, MAX(event_date) AS dmax FROM historical_odds")
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    assert row["dmin"] == "2024-08-31"
    assert row["dmax"] == "2025-01-01"


def test_line_movement_schema_independent(tmp_path: Path) -> None:
    """Ensure that the new line‑movement table does not interfere with existing
    historical odds operations."""
    from automation_scheduler.historical_line_movement import (
        initialize_line_movement_schema,
        summarize_line_movement_store,
    )
    db_path = tmp_path / "independent.db"
    conn = connect_historical_odds_db(db_path)
    initialize_historical_odds_db(conn)
    initialize_line_movement_schema(conn)

    # Existing historical_odds table still works
    row = _make_valid_row()
    upsert_canonical_historical_odds_rows(conn, [row], source_file="test.csv")
    counts = get_sqlite_table_counts(conn)
    assert counts["historical_odds"] == 1

    # Summary of line movement store should be empty but not crash
    summary = summarize_line_movement_store(conn)
    assert summary["ok"]
    assert summary["total_snapshots"] == 0

    conn.close()
