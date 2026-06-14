"""
Phase 10H22 – Tests for As‑Of Line Movement Query Engine.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation_scheduler.asof_line_movement_query import (
    AS_OF_LINE_MOVEMENT_QUERY_VERSION,
    normalize_asof_line_movement_value,
    parse_asof_datetime,
    normalize_asof_date_time_label,
    is_snapshot_available_as_of,
    build_asof_snapshot_group_key,
    filter_line_movement_snapshots_as_of,
    select_latest_asof_snapshots,
    summarize_asof_line_movement_snapshots,
    build_asof_line_movement_query_snapshot,
    load_line_movement_snapshots_from_sqlite,
    build_asof_line_movement_query_snapshot_from_sqlite,
    describe_asof_line_movement_query_engine,
)


# ---------------------------------------------------------------------------
# normalize_asof_line_movement_value tests
# ---------------------------------------------------------------------------


def test_normalize_asof_line_movement_value_handles_common_values():
    assert normalize_asof_line_movement_value(None) == ""
    assert normalize_asof_line_movement_value(True) == "Yes"
    assert normalize_asof_line_movement_value(False) == "No"
    assert normalize_asof_line_movement_value(42) == "42"
    assert normalize_asof_line_movement_value(3.14) == "3.14"
    assert normalize_asof_line_movement_value([1, 2]) == json.dumps([1, 2], sort_keys=True)
    assert normalize_asof_line_movement_value({"a": 1}) == json.dumps({"a": 1}, sort_keys=True)
    assert normalize_asof_line_movement_value("  hello  ") == "hello"


# ---------------------------------------------------------------------------
# parse_asof_datetime tests
# ---------------------------------------------------------------------------


def test_parse_asof_datetime_accepts_date():
    dt = parse_asof_datetime("2024-06-15")
    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 6
    assert dt.day == 15
    assert dt.tzinfo is not None


def test_parse_asof_datetime_accepts_z_datetime():
    dt = parse_asof_datetime("2024-06-15T12:30:00Z")
    assert dt is not None
    assert dt.hour == 12
    assert dt.minute == 30
    assert dt.tzinfo is not None


def test_parse_asof_datetime_returns_none_for_invalid():
    assert parse_asof_datetime(None) is None
    assert parse_asof_datetime("") is None
    assert parse_asof_datetime("not_a_date") is None


# ---------------------------------------------------------------------------
# is_snapshot_available_as_of tests
# ---------------------------------------------------------------------------


def test_is_snapshot_available_as_of_true_when_before():
    assert is_snapshot_available_as_of("2024-06-15T10:00:00Z", "2024-06-15T12:00:00Z") is True


def test_is_snapshot_available_as_of_true_when_equal():
    assert is_snapshot_available_as_of("2024-06-15T12:00:00Z", "2024-06-15T12:00:00Z") is True


def test_is_snapshot_available_as_of_false_when_after():
    assert is_snapshot_available_as_of("2024-06-15T14:00:00Z", "2024-06-15T12:00:00Z") is False


def test_is_snapshot_available_as_of_false_for_invalid():
    assert is_snapshot_available_as_of(None, "2024-06-15T12:00:00Z") is False
    assert is_snapshot_available_as_of("2024-06-15T10:00:00Z", None) is False
    assert is_snapshot_available_as_of("invalid", "2024-06-15T12:00:00Z") is False


# ---------------------------------------------------------------------------
# build_asof_snapshot_group_key tests
# ---------------------------------------------------------------------------


def test_build_asof_snapshot_group_key_is_stable():
    row1 = {"event_id": "e1", "bookmaker": "bookA", "market_family": "total",
            "market": "Over/Under", "selection": "Over", "line_value": 220.5}
    row2 = {"event_id": "e1", "bookmaker": "bookA", "market_family": "total",
            "market": "over/under", "selection": "over", "line_value": 220.5}
    assert build_asof_snapshot_group_key(row1) == build_asof_snapshot_group_key(row2)


# ---------------------------------------------------------------------------
# filter_line_movement_snapshots_as_of tests
# ---------------------------------------------------------------------------


def _make_snapshot(
    event_id: str = "e1",
    snapshot_time: str = "2024-06-15T10:00:00Z",
    bookmaker: str = "bookA",
    market_family: str = "total",
    market: str = "Over/Under",
    selection: str = "Over",
    line_value: float = 220.5,
    snapshot_id: str = "",
    **kw: Any,
) -> dict[str, Any]:
    s: dict[str, Any] = {
        "event_id": event_id,
        "snapshot_time": snapshot_time,
        "bookmaker": bookmaker,
        "market_family": market_family,
        "market": market,
        "selection": selection,
        "line_value": line_value,
        "snapshot_id": snapshot_id or f"{event_id}_{snapshot_time}",
    }
    s.update(kw)
    return s


def test_filter_line_movement_snapshots_as_of_requires_hypothetical_time():
    result = filter_line_movement_snapshots_as_of([])
    assert result["ok"] is False
    assert "missing_hypothetical_bet_time" in result["warnings"]


def test_filter_line_movement_snapshots_as_of_excludes_future_rows():
    snaps = [
        _make_snapshot(snapshot_time="2024-06-15T10:00:00Z"),
        _make_snapshot(snapshot_time="2024-06-15T14:00:00Z"),
    ]
    result = filter_line_movement_snapshots_as_of(snaps, hypothetical_bet_time="2024-06-15T12:00:00Z")
    assert result["available_snapshots"] == 1
    assert result["future_snapshots"] == 1


def test_filter_line_movement_snapshots_as_of_counts_invalid_times():
    snaps = [
        _make_snapshot(snapshot_time=""),
        _make_snapshot(snapshot_time="invalid"),
    ]
    result = filter_line_movement_snapshots_as_of(snaps, hypothetical_bet_time="2024-06-15T12:00:00Z")
    assert result["invalid_time_snapshots"] == 2


def test_filter_line_movement_snapshots_as_of_filters_event_id():
    snaps = [
        _make_snapshot(event_id="e1"),
        _make_snapshot(event_id="e2"),
    ]
    result = filter_line_movement_snapshots_as_of(snaps, event_id="e1",
                                                   hypothetical_bet_time="2024-06-15T12:00:00Z")
    assert result["available_snapshots"] == 1
    assert result["unmatched_snapshots"] == 1


def test_filter_line_movement_snapshots_as_of_filters_market_fields():
    snaps = [
        _make_snapshot(market_family="total", market="Over/Under", selection="Over"),
        _make_snapshot(market_family="moneyline", market="ML", selection="Home"),
    ]
    result = filter_line_movement_snapshots_as_of(
        snaps,
        hypothetical_bet_time="2024-06-15T12:00:00Z",
        market_family="total",
        market="Over/Under",
        selection="Over",
    )
    assert result["available_snapshots"] == 1
    assert result["unmatched_snapshots"] == 1


# ---------------------------------------------------------------------------
# select_latest_asof_snapshots tests
# ---------------------------------------------------------------------------


def test_select_latest_asof_snapshots_selects_latest_per_group():
    snaps = [
        _make_snapshot(event_id="e1", snapshot_time="2024-06-15T10:00:00Z",
                       snapshot_id="s1"),
        _make_snapshot(event_id="e1", snapshot_time="2024-06-15T12:00:00Z",
                       snapshot_id="s2"),
    ]
    result = select_latest_asof_snapshots(snaps, hypothetical_bet_time="2024-06-15T12:00:00Z")
    assert result["selected_snapshot_count"] == 1
    assert result["latest_snapshots"][0]["snapshot_id"] == "s2"


def test_select_latest_asof_snapshots_uses_deterministic_tie_break():
    snaps = [
        _make_snapshot(event_id="e1", snapshot_time="2024-06-15T10:00:00Z",
                       snapshot_id="aaa"),
        _make_snapshot(event_id="e1", snapshot_time="2024-06-15T10:00:00Z",
                       snapshot_id="bbb"),
    ]
    result = select_latest_asof_snapshots(snaps, hypothetical_bet_time="2024-06-15T12:00:00Z")
    assert result["selected_snapshot_count"] == 1
    # deterministic by snapshot_id (bbb > aaa? Actually sorted descending by time (equal) then snapshot_id lexicographically)
    # For tie, we pick first after sorting by -timestamp (equal) then snapshot_id ascending.
    # aaa < bbb, so after sort we pick aaa (first after ascending snapshot_id). We'll just check stable.
    first_id = result["latest_snapshots"][0]["snapshot_id"]
    expected = "aaa"  # because sorted by snapshot_id ascending then pick first.
    assert first_id == expected


def test_select_latest_asof_snapshots_respects_limit():
    snaps = [
        _make_snapshot(event_id="e1", snapshot_time="2024-06-15T10:00:00Z"),
        _make_snapshot(event_id="e2", snapshot_time="2024-06-15T10:00:00Z"),
    ]
    result = select_latest_asof_snapshots(snaps, hypothetical_bet_time="2024-06-15T12:00:00Z",
                                           limit=1)
    assert len(result["latest_snapshots"]) == 1


# ---------------------------------------------------------------------------
# summarize_asof_line_movement_snapshots tests
# ---------------------------------------------------------------------------


def test_summarize_asof_line_movement_snapshots_empty():
    summary = summarize_asof_line_movement_snapshots([])
    assert summary["ok"] is True
    assert "no_snapshots" in summary["warnings"]


def test_summarize_asof_line_movement_snapshots_counts_lists():
    snaps = [
        _make_snapshot(event_id="e1", snapshot_time="2024-06-15T10:00:00Z",
                       sport="soccer", bookmaker="bookA",
                       snapshot_label="decision"),
        _make_snapshot(event_id="e2", snapshot_time="2024-06-15T12:00:00Z",
                       sport="basketball", bookmaker="bookB",
                       snapshot_label="opening"),
    ]
    summary = summarize_asof_line_movement_snapshots(snaps)
    assert summary["snapshot_count"] == 2
    assert "soccer" in summary["sports"]
    assert "bookA" in summary["bookmakers"]
    assert "opening" in summary["snapshot_labels"]


# ---------------------------------------------------------------------------
# build_asof_line_movement_query_snapshot tests
# ---------------------------------------------------------------------------


def test_build_asof_line_movement_query_snapshot_empty():
    result = build_asof_line_movement_query_snapshot()
    assert result["ok"] is False  # because hypothetical_bet_time missing
    assert len(result["warnings"]) > 0


def test_build_asof_line_movement_query_snapshot_returns_query_snapshots():
    snaps = [
        _make_snapshot(event_id="e1", snapshot_time="2024-06-15T10:00:00Z",
                       snapshot_id="s1"),
        _make_snapshot(event_id="e1", snapshot_time="2024-06-15T12:00:00Z",
                       snapshot_id="s2"),
    ]
    result = build_asof_line_movement_query_snapshot(
        snapshots=snaps,
        hypothetical_bet_time="2024-06-15T12:00:00Z",
        limit=10,
    )
    assert result["ok"] is True
    assert result["selection"]["selected_snapshot_count"] == 1
    assert len(result["summary"]["sports"]) == 0  # no sport set in fixtures
    assert "messages" in result


# ---------------------------------------------------------------------------
# load_line_movement_snapshots_from_sqlite tests
# ---------------------------------------------------------------------------


def test_load_line_movement_snapshots_from_sqlite_missing_db(tmp_path):
    db_path = tmp_path / "nonexistent.db"
    result = load_line_movement_snapshots_from_sqlite(db_path)
    assert result["ok"] is False
    assert any("cannot_open_database" in w for w in result["warnings"])


def test_load_line_movement_snapshots_from_sqlite_reads_historical_line_snapshots(tmp_path):
    import sqlite3

    db_path = tmp_path / "test_load.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE historical_line_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            event_id TEXT,
            bookmaker TEXT,
            market_family TEXT,
            market TEXT,
            selection TEXT,
            snapshot_time TEXT
        )"""
    )
    conn.execute(
        """INSERT INTO historical_line_snapshots (snapshot_id, event_id, bookmaker,
            market_family, market, selection, snapshot_time)
           VALUES ('s1', 'e1', 'bookA', 'total', 'Over/Under', 'Over', '2024-06-15T10:00:00Z')"""
    )
    conn.commit()
    conn.close()
    result = load_line_movement_snapshots_from_sqlite(db_path)
    assert result["ok"] is True
    assert result["total_snapshots"] == 1
    assert result["snapshots"][0]["snapshot_id"] == "s1"


# ---------------------------------------------------------------------------
# build_asof_line_movement_query_snapshot_from_sqlite tests
# ---------------------------------------------------------------------------


def test_build_asof_line_movement_query_snapshot_from_sqlite_read_only(tmp_path):
    import sqlite3

    db_path = tmp_path / "read_only.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE historical_line_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            event_id TEXT,
            snapshot_time TEXT
        )"""
    )
    conn.execute("INSERT INTO historical_line_snapshots VALUES ('s1', 'e1', '2024-06-15T10:00:00Z')")
    conn.commit()
    conn.close()
    result = build_asof_line_movement_query_snapshot_from_sqlite(
        db_path, event_id="e1", hypothetical_bet_time="2024-06-15T12:00:00Z"
    )
    assert result["ok"] is True
    assert result["load"]["total_snapshots"] == 1
    assert result["query_snapshot"]["selection"]["selected_snapshot_count"] == 1


# ---------------------------------------------------------------------------
# describe_asof_line_movement_query_engine tests
# ---------------------------------------------------------------------------


def test_describe_asof_line_movement_query_engine_mentions_no_vendor_import():
    msgs = describe_asof_line_movement_query_engine()
    combined = " ".join(msgs)
    assert "does not connect to vendors" in combined


def test_describe_asof_line_movement_query_engine_mentions_lookahead_bias():
    msgs = describe_asof_line_movement_query_engine()
    combined = " ".join(msgs)
    assert "look-ahead bias" in combined


# ---------------------------------------------------------------------------
# ensure future snapshot never selected
# ---------------------------------------------------------------------------


def test_future_snapshot_is_never_selected():
    snaps = [
        _make_snapshot(event_id="e1", snapshot_time="2024-06-15T10:00:00Z"),
        _make_snapshot(event_id="e1", snapshot_time="2024-06-15T14:00:00Z"),
    ]
    result = select_latest_asof_snapshots(snaps, hypothetical_bet_time="2024-06-15T12:00:00Z")
    assert result["available_snapshots"] == 1
    assert result["latest_snapshots"][0]["snapshot_time"] == "2024-06-15T10:00:00Z"
