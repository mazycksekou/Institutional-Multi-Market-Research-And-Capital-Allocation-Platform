"""
Tests for automation_scheduler/historical_odds_sqlite.py.

Uses temporary SQLite databases only.
No external network, no downloading, no scraping.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
import tempfile
from pathlib import Path

import pytest

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


def _connection() -> tuple[sqlite3.Connection, Path]: ...


def _tmp_db() -> Path:
    return Path(tempfile.mkstemp(suffix=".db")[1])


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    import csv as csvmod
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csvmod.writer(f)
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


def test_initialize_creates_tables() -> None:
    db_path = _tmp_db()
    try:
        conn = connect_historical_odds_db(db_path)
        initialize_historical_odds_db(conn)
        table_names = [
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        ]
        for t in HISTORICAL_ODDS_SQLITE_TABLES:
            assert t in table_names
        conn.close()
    finally:
        db_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 2. upsert inserts valid row into events, odds, results, source_imports
# ---------------------------------------------------------------------------


def test_upsert_valid_row() -> None:
    db_path = _tmp_db()
    try:
        conn = connect_historical_odds_db(db_path)
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
        conn.close()
    finally:
        db_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 3. inserting same row twice is idempotent
# ---------------------------------------------------------------------------


def test_upsert_idempotent() -> None:
    db_path = _tmp_db()
    try:
        conn = connect_historical_odds_db(db_path)
        initialize_historical_odds_db(conn)
        row = _make_valid_row()
        upsert_canonical_historical_odds_rows(conn, [row], source_file="test.csv")
        upsert_canonical_historical_odds_rows(conn, [row], source_file="test.csv")
        counts = get_sqlite_table_counts(conn)
        # odds should still be exactly 1
        assert counts["historical_odds"] == 1
        # source_imports records each call (2 calls)
        assert counts["source_imports"] == 2
        conn.close()
    finally:
        db_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 4. invalid row rejected
# ---------------------------------------------------------------------------


def test_upsert_rejects_invalid() -> None:
    db_path = _tmp_db()
    try:
        conn = connect_historical_odds_db(db_path)
        initialize_historical_odds_db(conn)
        # row missing essential fields
        bad_row = build_canonical_historical_odds_row(source_name="x")
        result = upsert_canonical_historical_odds_rows(conn, [bad_row], source_file="bad.csv")
        assert result["rows_inserted"] == 0
        assert result["rows_rejected"] == 1
        counts = get_sqlite_table_counts(conn)
        assert counts["historical_odds"] == 0
        conn.close()
    finally:
        db_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 5. query filters work
# ---------------------------------------------------------------------------


def test_query_filters() -> None:
    db_path = _tmp_db()
    try:
        conn = connect_historical_odds_db(db_path)
        initialize_historical_odds_db(conn)
        row1 = _make_valid_row()
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
        )
        upsert_canonical_historical_odds_rows(conn, [row1, row2], source_file="multi.csv")

        # sport filter
        rows = query_historical_odds_rows(conn, sport="soccer")
        assert len(rows) == 1

        # league filter
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
        conn.close()
    finally:
        db_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 6. summarize works
# ---------------------------------------------------------------------------


def test_summarize() -> None:
    db_path = _tmp_db()
    try:
        conn = connect_historical_odds_db(db_path)
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
        conn.close()
    finally:
        db_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 7. import_historical_odds_file_to_sqlite works with Football-Data CSV
# ---------------------------------------------------------------------------


def test_import_football_csv_via_store() -> None:
    header = [
        "Div", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
        "B365H", "B365D", "B365A",
    ]
    data = [
        ["E0", "2023-08-12", "Arsenal", "Chelsea", "3", "1", "H", "1.50", "4.00", "6.50"],
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_foot.csv"
        _write_csv(csv_path, header, data)
        db_path = Path(tmpdir) / "store.db"
        conn = connect_historical_odds_db(db_path)
        initialize_historical_odds_db(conn)
        res = import_historical_odds_file_to_sqlite(
            conn, "football_data_uk", csv_path, source_file="test_foot.csv"
        )
        assert res["rows_inserted"] == 3  # home, draw, away
        counts = get_sqlite_table_counts(conn)
        assert counts["historical_odds"] == 3
        conn.close()


# ---------------------------------------------------------------------------
# 8. validate_sqlite_store
# ---------------------------------------------------------------------------


def test_validate_store() -> None:
    db_path = _tmp_db()
    try:
        conn = connect_historical_odds_db(db_path)
        initialize_historical_odds_db(conn)
        val = validate_sqlite_store(conn)
        assert val["ok"] is True
        assert val["errors"] == []
        conn.close()
    finally:
        db_path.unlink(missing_ok=True)


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
