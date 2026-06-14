"""
Tests for Phase 10H23 – Line Movement Data Quality Dashboard.

Covers normalize, missing, group key, coverage, duplicates, missing links,
books/markets/sports, readiness, main snapshot, SQLite wrapper, and describe.
"""

from __future__ import annotations

import json

from automation_scheduler.line_movement_data_quality_dashboard import (
    LINE_MOVEMENT_DATA_QUALITY_DASHBOARD_VERSION,
    build_line_movement_data_quality_snapshot,
    build_line_movement_data_quality_snapshot_from_sqlite,
    build_line_movement_quality_group_key,
    build_line_movement_quality_readiness,
    describe_line_movement_data_quality_dashboard,
    detect_line_movement_duplicate_snapshots,
    is_missing_quality_value,
    normalize_line_movement_quality_value,
    summarize_line_movement_books_markets_sports,
    summarize_line_movement_missing_links,
    summarize_line_movement_quality_coverage,
)


def test_normalize_line_movement_quality_value_handles_common_values():
    assert normalize_line_movement_quality_value(None) == ""
    assert normalize_line_movement_quality_value(True) == "Yes"
    assert normalize_line_movement_quality_value(False) == "No"
    assert normalize_line_movement_quality_value(42) == "42"
    assert normalize_line_movement_quality_value(3.14) == "3.14"
    assert normalize_line_movement_quality_value([1, 2]) == json.dumps([1, 2])
    assert normalize_line_movement_quality_value({"a": 1}) == json.dumps({"a": 1}, sort_keys=True)
    assert normalize_line_movement_quality_value("  hello  ") == "hello"


def test_is_missing_quality_value():
    assert is_missing_quality_value(None) is True
    assert is_missing_quality_value("") is True
    assert is_missing_quality_value("   ") is True
    assert is_missing_quality_value("abc") is False
    assert is_missing_quality_value(0) is False
    assert is_missing_quality_value(False) is False


def test_build_line_movement_quality_group_key_is_stable():
    row = {
        "event_id": "e1",
        "sport": "Soccer",
        "league": "EPL",
        "event_date": "2024-01-01",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "bookmaker": "BookA",
        "market_family": "total",
        "market": "Over/Under",
        "selection": "Over",
        "snapshot_label": "decision",
        "snapshot_time": "2024-01-01T12:00:00Z",
    }
    key = build_line_movement_quality_group_key(row)
    # same row produces same key
    key2 = build_line_movement_quality_group_key(row)
    assert key == key2

    # different case yields same key
    row2 = {k: v.upper() if isinstance(v, str) else v for k, v in row.items()}
    key3 = build_line_movement_quality_group_key(row2)
    assert key == key3

    # non-dict does not crash
    assert build_line_movement_quality_group_key("not a dict") == ""


def test_summarize_line_movement_quality_coverage_empty():
    result = summarize_line_movement_quality_coverage([])
    assert result["ok"] is True
    assert result["total_snapshots"] == 0
    assert "no_snapshots" in result["warnings"]


def test_summarize_line_movement_quality_coverage_counts_missing_fields():
    rows = [
        {"event_id": "e1", "snapshot_time": "2024-01-01T12:00:00Z",
         "market_family": "total", "bookmaker": "B1", "sport": "soccer",
         "market": "Over/Under", "selection": "Over"},
        {"event_id": "e2", "snapshot_time": "", "market_family": "",
         "bookmaker": None, "sport": "  ", "market": None, "selection": None},
    ]
    result = summarize_line_movement_quality_coverage(rows)
    assert result["total_snapshots"] == 2
    assert result["missing_event_id_count"] == 0
    assert result["missing_snapshot_time_count"] == 1
    assert result["missing_market_family_count"] == 1
    assert result["missing_bookmaker_count"] == 1
    assert result["missing_sport_count"] == 1
    assert result["missing_market_count"] == 1
    assert result["missing_selection_count"] == 1
    assert result["linked_snapshots"] == 2
    assert result["unlinked_snapshots"] == 0


def test_summarize_line_movement_quality_coverage_lists_sports_markets_books():
    rows = [
        {"sport": "Soccer", "market_family": "total", "bookmaker": "B1",
         "snapshot_label": "decision"},
        {"sport": "Basketball", "market_family": "moneyline", "bookmaker": "B2",
         "snapshot_label": "closing"},
        {"sport": "Soccer", "market_family": "", "bookmaker": None,
         "snapshot_label": None},
    ]
    result = summarize_line_movement_quality_coverage(rows)
    assert "soccer" in result["sports"]
    assert "total" in result["market_families"]
    assert "b1" in result["bookmakers"]
    assert "decision" in result["snapshot_labels"]
    # blanks excluded
    assert "" not in result["sports"]
    assert "" not in result["market_families"]
    assert "" not in result["bookmakers"]


def test_detect_line_movement_duplicate_snapshots_empty():
    result = detect_line_movement_duplicate_snapshots([])
    assert result["ok"] is True
    assert result["duplicate_group_count"] == 0
    assert result["duplicate_snapshot_count"] == 0


def test_detect_line_movement_duplicate_snapshots_finds_duplicate_group():
    rows = [
        {"event_id": "e1", "bookmaker": "B1", "market_family": "total",
         "market": "O/U", "selection": "Over", "snapshot_label": "decision",
         "snapshot_time": "2024-01-01T12:00:00Z", "snapshot_id": "s1"},
        {"event_id": "e1", "bookmaker": "B1", "market_family": "total",
         "market": "O/U", "selection": "Over", "snapshot_label": "decision",
         "snapshot_time": "2024-01-01T12:00:00Z", "snapshot_id": "s2"},
        {"event_id": "e2", "bookmaker": "B2", "market_family": "moneyline",
         "market": "ML", "selection": "Home", "snapshot_label": "opening",
         "snapshot_time": "2024-01-02T10:00:00Z", "snapshot_id": "s3"},
    ]
    result = detect_line_movement_duplicate_snapshots(rows)
    assert result["duplicate_group_count"] == 1
    assert result["duplicate_snapshot_count"] == 2


def test_summarize_line_movement_missing_links_empty():
    result = summarize_line_movement_missing_links([])
    assert result["ok"] is True
    assert result["missing_link_count"] == 0
    assert "no_snapshots" in result["warnings"]


def test_summarize_line_movement_missing_links_counts_blank_event_id():
    rows = [
        {"event_id": "e1"},
        {"event_id": ""},
        {"event_id": None},
        {"event_id": "  "},
    ]
    result = summarize_line_movement_missing_links(rows)
    assert result["missing_link_count"] == 3
    assert result["linked_count"] == 1
    assert len(result["missing_link_rows"]) == 3


def test_summarize_line_movement_books_markets_sports_counts():
    rows = [
        {"sport": "Soccer", "market_family": "total", "bookmaker": "B1", "market": "O/U"},
        {"sport": "Basketball", "market_family": "moneyline", "bookmaker": "B2", "market": "ML"},
        {"sport": "Soccer", "market_family": "total", "bookmaker": "B1", "market": "O/U"},
        {"sport": "Baseball", "market_family": "", "bookmaker": None, "market": ""},
    ]
    result = summarize_line_movement_books_markets_sports(rows)
    assert result["sport_count"] == 3
    assert result["market_family_count"] == 2
    assert result["bookmaker_count"] == 2
    assert result["market_count"] == 2


def test_build_line_movement_quality_readiness_blocks_no_snapshots():
    cv = {"total_snapshots": 0, "linked_snapshots": 0,
          "missing_snapshot_time_count": 0, "missing_market_family_count": 0,
          "missing_bookmaker_count": 0, "missing_sport_count": 0,
          "missing_market_count": 0}
    dups = {"duplicate_snapshot_count": 0}
    ml = {"missing_link_count": 0}
    rd = build_line_movement_quality_readiness(cv, dups, ml)
    assert rd["ready"] is False
    assert "no_snapshots" in rd["reasons"]
    assert rd["readiness_level"] == "blocked"


def test_build_line_movement_quality_readiness_blocks_missing_links():
    cv = {"total_snapshots": 10, "linked_snapshots": 0,
          "missing_snapshot_time_count": 0, "missing_market_family_count": 0,
          "missing_bookmaker_count": 0, "missing_sport_count": 0,
          "missing_market_count": 0}
    dups = {"duplicate_snapshot_count": 0}
    ml = {"missing_link_count": 10}
    rd = build_line_movement_quality_readiness(cv, dups, ml)
    assert rd["ready"] is False
    assert "missing_linked_events" in rd["reasons"]


def test_build_line_movement_quality_readiness_blocks_duplicate_snapshots():
    cv = {"total_snapshots": 10, "linked_snapshots": 10,
          "missing_snapshot_time_count": 0, "missing_market_family_count": 0,
          "missing_bookmaker_count": 0, "missing_sport_count": 0,
          "missing_market_count": 0}
    dups = {"duplicate_snapshot_count": 5}
    ml = {"missing_link_count": 0}
    rd = build_line_movement_quality_readiness(cv, dups, ml)
    assert rd["ready"] is False
    assert "duplicate_snapshots" in rd["reasons"]


def test_build_line_movement_quality_readiness_ready_when_clean():
    cv = {"total_snapshots": 10, "linked_snapshots": 10,
          "missing_snapshot_time_count": 0, "missing_market_family_count": 0,
          "missing_bookmaker_count": 0, "missing_sport_count": 0,
          "missing_market_count": 0}
    dups = {"duplicate_snapshot_count": 0}
    ml = {"missing_link_count": 0}
    rd = build_line_movement_quality_readiness(cv, dups, ml)
    assert rd["ready"] is True
    assert rd["readiness_level"] == "strong"


def test_build_line_movement_data_quality_snapshot_empty():
    snap = build_line_movement_data_quality_snapshot()
    assert snap["ok"] is True
    assert snap["coverage"]["total_snapshots"] == 0
    assert snap["readiness"]["ready"] is False
    assert "no_snapshots" in snap["readiness"]["reasons"]


def test_build_line_movement_data_quality_snapshot_clean_rows():
    rows = [
        {"event_id": "e1", "snapshot_time": "2024-01-01T12:00:00Z",
         "market_family": "total", "bookmaker": "B1", "sport": "soccer",
         "market": "O/U", "selection": "Over", "snapshot_label": "decision",
         "snapshot_id": "s1"},
        {"event_id": "e2", "snapshot_time": "2024-01-02T12:00:00Z",
         "market_family": "moneyline", "bookmaker": "B2", "sport": "basketball",
         "market": "ML", "selection": "Home", "snapshot_label": "opening",
         "snapshot_id": "s2"},
    ]
    snap = build_line_movement_data_quality_snapshot(rows)
    assert snap["ok"] is True
    assert snap["coverage"]["total_snapshots"] == 2
    assert snap["coverage"]["linked_snapshots"] == 2
    assert snap["readiness"]["ready"] is True


def test_build_line_movement_data_quality_snapshot_with_duplicates():
    rows = [
        {"event_id": "e1", "bookmaker": "B1", "market_family": "total",
         "market": "O/U", "selection": "Over", "snapshot_label": "decision",
         "snapshot_time": "2024-01-01T12:00:00Z", "sport": "soccer",
         "snapshot_id": "s1"},
        {"event_id": "e1", "bookmaker": "B1", "market_family": "total",
         "market": "O/U", "selection": "Over", "snapshot_label": "decision",
         "snapshot_time": "2024-01-01T12:00:00Z", "sport": "soccer",
         "snapshot_id": "s2"},
    ]
    snap = build_line_movement_data_quality_snapshot(rows)
    assert snap["duplicates"]["duplicate_group_count"] >= 1
    assert snap["duplicates"]["duplicate_snapshot_count"] == 2


def test_build_line_movement_data_quality_snapshot_with_missing_links():
    rows = [
        {"event_id": "e1"},
        {"event_id": ""},
        {"event_id": None},
    ]
    snap = build_line_movement_data_quality_snapshot(rows)
    assert snap["missing_links"]["missing_link_count"] == 2


def test_build_line_movement_data_quality_snapshot_uses_asof_query():
    rows = [
        {"event_id": "e1", "snapshot_time": "2024-01-01T10:00:00Z",
         "sport": "soccer"},
    ]
    snap = build_line_movement_data_quality_snapshot(
        rows, hypothetical_bet_time="2024-01-01T12:00:00Z"
    )
    asof = snap["asof_query"]
    assert asof.get("available_snapshots") == 1
    assert asof.get("future_snapshots") == 0
    assert asof.get("invalid_time_snapshots") == 0


def test_build_line_movement_data_quality_snapshot_from_sqlite_missing_db():
    import tempfile
    path = "nonexistent_path_that_does_not_exist.db"
    result = build_line_movement_data_quality_snapshot_from_sqlite(path)
    assert result["ok"] is False
    assert "cannot_open_database" in str(result.get("warnings", [])) or \
           "cannot_open_database" in str(result.get("load", {})).lower()


def test_describe_line_movement_data_quality_dashboard_mentions_no_vendor_import():
    msgs = describe_line_movement_data_quality_dashboard()
    combined = " ".join(msgs)
    assert "does not connect to vendors" in combined or "does not connect" in combined


def test_describe_line_movement_data_quality_dashboard_mentions_checkpoint():
    msgs = describe_line_movement_data_quality_dashboard()
    combined = " ".join(msgs)
    assert "checkpoint" in combined or "review" in combined


def test_data_quality_dashboard_does_not_require_vendor_connector():
    snap = build_line_movement_data_quality_snapshot()
    assert "vendor" not in str(snap.get("warnings", [])).lower()
    assert "api" not in str(snap.get("warnings", [])).lower()
