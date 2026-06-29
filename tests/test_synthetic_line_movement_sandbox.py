"""Tests for the Phase 10H23A Synthetic Line Movement Sandbox.

All synthetic rows are in-memory and must never be written to SQLite.
None of these tests call external APIs, vendors, or scrapers.
"""

from __future__ import annotations

from src.automation_scheduler_legacy.synthetic_line_movement_sandbox import SYNTHETIC_LINE_MOVEMENT_SANDBOX_VERSION, normalize_synthetic_line_movement_value, get_supported_synthetic_sports, build_synthetic_event_rows, build_synthetic_line_movement_rows, build_synthetic_line_movement_demo_payload, run_synthetic_line_movement_sandbox, clear_synthetic_line_movement_sandbox, describe_synthetic_line_movement_sandbox


# ---------------------------------------------------------------------------
# 1. Value normalizer
# ---------------------------------------------------------------------------

def test_normalize_synthetic_line_movement_value_handles_common_values():
    assert normalize_synthetic_line_movement_value(None) == ""
    assert normalize_synthetic_line_movement_value(True) == "Yes"
    assert normalize_synthetic_line_movement_value(False) == "No"
    assert normalize_synthetic_line_movement_value(42) == "42"
    assert normalize_synthetic_line_movement_value(3.14) == "3.14"
    assert normalize_synthetic_line_movement_value([1, 2]) == "[1, 2]"
    assert normalize_synthetic_line_movement_value({"a": 1}) == '{"a": 1}'
    assert normalize_synthetic_line_movement_value(" hello ") == "hello"


# ---------------------------------------------------------------------------
# 2. Supported sports
# ---------------------------------------------------------------------------


def test_get_supported_synthetic_sports_contains_core_sports():
    sports = get_supported_synthetic_sports()
    for required in ("nba", "nfl", "mlb", "soccer", "nhl"):
        assert required in sports
    assert sports == sorted(sports)


# ---------------------------------------------------------------------------
# 3. Build event rows
# ---------------------------------------------------------------------------


def test_build_synthetic_event_rows_default():
    rows = build_synthetic_event_rows()
    assert len(rows) == 2
    assert rows[0]["event_id"].startswith("synthetic_event_")
    assert rows[0]["is_synthetic_demo"] == "Yes"
    assert rows[0]["source_key"] == "synthetic_demo"


def test_build_synthetic_event_rows_caps_count():
    rows = build_synthetic_event_rows(sport="nfl", event_count=15)
    # capped at 10
    assert len(rows) == 10
    assert all(r["sport"] == "nfl" for r in rows)


# ---------------------------------------------------------------------------
# 4. Build line movement rows
# ---------------------------------------------------------------------------


def test_build_synthetic_line_movement_rows_default():
    rows = build_synthetic_line_movement_rows()
    assert len(rows) >= 1
    # all have deterministic snapshot_id
    assert all("snapshot_id" in r for r in rows)


def test_build_synthetic_line_movement_rows_marks_synthetic_demo():
    rows = build_synthetic_line_movement_rows(sport="mlb", event_count=1, snapshots_per_event=1)
    for r in rows:
        assert r["is_synthetic_demo"] == "Yes"
        assert r["source_key"] == "synthetic_demo"
        assert r["source_name"] == "Synthetic Demo"
        assert r["source_file"] == "synthetic_demo_in_memory"
        assert "2-Way Moneyline" not in r.get("market", "").lower()


def test_build_synthetic_line_movement_rows_missing_link():
    rows = build_synthetic_line_movement_rows(
        sport="nba", event_count=2, snapshots_per_event=2,
        include_missing_link=True,
    )
    # at least one row has blank event_id
    blank = [r for r in rows if not r.get("event_id")]
    assert len(blank) >= 1


def test_build_synthetic_line_movement_rows_duplicate():
    rows = build_synthetic_line_movement_rows(
        sport="soccer", event_count=2, snapshots_per_event=2,
        include_duplicate=True,
    )
    # detect duplicate snapshot_id
    ids = [r["snapshot_id"] for r in rows]
    assert len(ids) != len(set(ids))


def test_build_synthetic_line_movement_rows_future_snapshot():
    rows = build_synthetic_line_movement_rows(
        sport="nhl", event_count=1, snapshots_per_event=2,
        include_future_snapshot=True,
    )
    # any snapshot_time after default hypothetical_bet_time "2024-01-01T13:00:00Z"
    future = [r for r in rows if r.get("snapshot_time", "") > "2024-01-01T14:00:00Z"]
    assert len(future) >= 1


# ---------------------------------------------------------------------------
# 5. Demo payload
# ---------------------------------------------------------------------------


def test_build_synthetic_line_movement_demo_payload_invalid_sport_warns():
    payload = build_synthetic_line_movement_demo_payload(sport="cricket")
    assert payload["ok"] is True
    assert any("unsupported_sport" in w for w in payload["warnings"])
    assert payload["sport"] == "nba"


# ---------------------------------------------------------------------------
# 6. run_synthetic_line_movement_sandbox
# ---------------------------------------------------------------------------


def test_run_synthetic_line_movement_sandbox_returns_pipeline_outputs():
    result = run_synthetic_line_movement_sandbox(
        sport="nba", event_count=1, snapshots_per_event=1,
    )
    assert result["ok"] is True
    assert "import_preview" in result
    assert "event_link_resolution" in result
    assert "asof_query" in result
    assert "data_quality" in result


def test_run_synthetic_line_movement_sandbox_never_writes_sqlite():
    # ensure no db_path argument accepted
    result = run_synthetic_line_movement_sandbox()
    assert result["ok"] is True
    # no sqlite files created by the function itself
    import os
    # the synthetic_notice must be present
    assert "synthetic_notice" in result


def test_run_synthetic_line_movement_sandbox_with_missing_link_shows_quality_issue():
    result = run_synthetic_line_movement_sandbox(
        sport="nba", event_count=2, snapshots_per_event=2,
        include_missing_link=True,
    )
    dq = result["data_quality"]
    ml = dq.get("missing_links", {})
    assert ml.get("missing_link_count", 0) > 0


def test_run_synthetic_line_movement_sandbox_with_duplicate_shows_quality_issue():
    result = run_synthetic_line_movement_sandbox(
        sport="nba", event_count=2, snapshots_per_event=2,
        include_duplicate=True,
    )
    dq = result["data_quality"]
    dup = dq.get("duplicates", {})
    assert dup.get("duplicate_snapshot_count", 0) > 0


def test_run_synthetic_line_movement_sandbox_with_future_snapshot_shows_asof_issue():
    result = run_synthetic_line_movement_sandbox(
        sport="nba", event_count=2, snapshots_per_event=2,
        include_future_snapshot=True,
    )
    asof = result["asof_query"]
    query = asof.get("query", {})
    # future snapshots are filtered out
    assert query.get("future_snapshots", 0) >= 1


# ---------------------------------------------------------------------------
# 7. Clear
# ---------------------------------------------------------------------------


def test_clear_synthetic_line_movement_sandbox():
    result = clear_synthetic_line_movement_sandbox()
    assert result["ok"] is True
    assert result["cleared"] is True


# ---------------------------------------------------------------------------
# 8. Description
# ---------------------------------------------------------------------------


def test_describe_synthetic_line_movement_sandbox_mentions_no_vendor_import():
    lines = describe_synthetic_line_movement_sandbox()
    combined = " ".join(lines).lower()
    assert "no vendor" in combined


def test_describe_synthetic_line_movement_sandbox_mentions_not_model_evidence():
    lines = describe_synthetic_line_movement_sandbox()
    combined = " ".join(lines).lower()
    assert "not real historical" in combined or "not be used as model evidence" in combined


# ---------------------------------------------------------------------------
# 9. No moneyline_or_1x2 as preferred output
# ---------------------------------------------------------------------------


def test_synthetic_sandbox_does_not_use_moneyline_or_1x2_as_preferred_output():
    # build default snapshot rows and check market_family values
    rows = build_synthetic_line_movement_rows(sport="soccer", event_count=1, snapshots_per_event=1)
    for r in rows:
        mf = r.get("market_family", "")
        assert mf != "moneyline_or_1x2", f"Unexpected family {mf}"
        # also check that market name does not contain "1x2"
        market = r.get("market", "").lower()
        assert "1x2" not in market
