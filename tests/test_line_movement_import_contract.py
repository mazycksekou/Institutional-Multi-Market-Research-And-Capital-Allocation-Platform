"""
Tests for Phase 10H20 – Vendor‑Neutral Line Movement Import Contract.
"""

from __future__ import annotations

import json

from src.services.streamlit_dashboard_facade import LINE_MOVEMENT_IMPORT_CONTRACT_VERSION, build_canonical_line_movement_snapshot_row, build_line_movement_import_preview, build_vendor_neutral_line_movement_contract, describe_line_movement_import_contract, make_line_movement_snapshot_id, normalize_line_movement_import_value, normalize_line_movement_market_family, normalize_line_movement_snapshot_label, validate_line_movement_import_row


# ---------------------------------------------------------------------------
# Normalizers
# ---------------------------------------------------------------------------


def test_normalize_line_movement_import_value_handles_common_values():
    assert normalize_line_movement_import_value(None) == ""
    assert normalize_line_movement_import_value(True) == "Yes"
    assert normalize_line_movement_import_value(False) == "No"
    assert normalize_line_movement_import_value(5) == "5"
    assert normalize_line_movement_import_value(1.5) == "1.5"
    assert normalize_line_movement_import_value([1, 2]) == json.dumps([1, 2], sort_keys=True)
    d = {"a": 1}
    assert normalize_line_movement_import_value(d) == json.dumps(d, sort_keys=True)
    assert normalize_line_movement_import_value("hello") == "hello"


def test_normalize_line_movement_market_family_moneyline_two_way():
    assert normalize_line_movement_market_family("moneyline") == "two_way_moneyline"
    assert normalize_line_movement_market_family("ml") == "two_way_moneyline"
    assert normalize_line_movement_market_family("2-Way") == "two_way_moneyline"


def test_normalize_line_movement_market_family_1x2_three_way():
    assert normalize_line_movement_market_family("1x2") == "three_way_moneyline"
    assert (
        normalize_line_movement_market_family("three-way moneyline")
        == "three_way_moneyline"
    )


def test_normalize_line_movement_market_family_spread_total_props():
    assert normalize_line_movement_market_family("spread") == "spread_or_handicap"
    assert normalize_line_movement_market_family("Handicap") == "spread_or_handicap"
    assert normalize_line_movement_market_family("total") == "game_total"
    assert normalize_line_movement_market_family("Over/Under") == "game_total"
    assert normalize_line_movement_market_family("team total") == "team_total"
    assert normalize_line_movement_market_family("player prop") == "player_prop"


def test_normalize_line_movement_snapshot_label():
    assert normalize_line_movement_snapshot_label("open") == "opening"
    assert normalize_line_movement_snapshot_label("start") == "opening"
    assert normalize_line_movement_snapshot_label("live") == "current"
    assert normalize_line_movement_snapshot_label("now") == "current"
    assert normalize_line_movement_snapshot_label("bet") == "decision"
    assert normalize_line_movement_snapshot_label("dec") == "decision"
    assert normalize_line_movement_snapshot_label("close") == "closing"
    assert normalize_line_movement_snapshot_label("final") == "closing"
    assert normalize_line_movement_snapshot_label("unknown") == "unknown"
    assert normalize_line_movement_snapshot_label(None) == "unknown"


# ---------------------------------------------------------------------------
# Contract shape
# ---------------------------------------------------------------------------


def test_build_vendor_neutral_line_movement_contract_shape():
    c = build_vendor_neutral_line_movement_contract()
    assert c["ok"] is True
    assert c["version"] == LINE_MOVEMENT_IMPORT_CONTRACT_VERSION
    assert "source_name" in c["required_input_fields"]
    assert "source_key" in c["required_input_fields"]
    assert "sport" in c["required_input_fields"]
    assert "event_date" in c["required_input_fields"]
    assert "home_team" in c["required_input_fields"]
    assert "away_team" in c["required_input_fields"]
    assert "bookmaker" in c["required_input_fields"]
    assert "market" in c["required_input_fields"]
    assert "selection" in c["required_input_fields"]
    assert "snapshot_time" in c["required_input_fields"]
    assert "raw_payload" in c["optional_input_fields"]


# ---------------------------------------------------------------------------
# Validate row
# ---------------------------------------------------------------------------


def test_validate_line_movement_import_row_missing_required_fields():
    row = {"sport": "soccer", "source_name": "test"}
    result = validate_line_movement_import_row(row)
    assert result["ok"] is False
    assert "source_key" in result["missing_required_fields"]
    assert "event_date" in result["missing_required_fields"]
    assert "home_team" in result["missing_required_fields"]
    assert "away_team" in result["missing_required_fields"]
    assert "bookmaker" in result["missing_required_fields"]
    assert "market" in result["missing_required_fields"]
    assert "selection" in result["missing_required_fields"]
    assert "snapshot_time" in result["missing_required_fields"]


def test_validate_line_movement_import_row_valid_row():
    row = {
        "source_name": "test",
        "source_key": "test_key",
        "sport": "soccer",
        "event_date": "2023-01-01",
        "home_team": "A",
        "away_team": "B",
        "bookmaker": "book",
        "market": "1x2",
        "selection": "Home",
        "snapshot_time": "2023-01-01T12:00:00Z",
    }
    result = validate_line_movement_import_row(row)
    assert result["ok"] is True
    assert result["missing_required_fields"] == []


def test_validate_line_movement_import_row_non_dict():
    result = validate_line_movement_import_row("not_a_dict")
    assert result["ok"] is False
    assert "invalid_row_type" in result["warnings"]


# ---------------------------------------------------------------------------
# Snapshot ID
# ---------------------------------------------------------------------------


def test_make_line_movement_snapshot_id_uses_source_snapshot_id():
    row = {
        "source_name": "my_source",
        "source_snapshot_id": "abc123",
        "sport": "soccer",
    }
    sid = make_line_movement_snapshot_id(row)
    assert sid.startswith("lms_my_source_abc123") or sid.startswith("lms_my_source_abc123")


def test_make_line_movement_snapshot_id_is_deterministic_without_source_snapshot_id():
    row = {
        "source_name": "test",
        "source_key": "tk",
        "source_event_id": "",
        "sport": "soccer",
        "event_date": "2023-01-01",
        "home_team": "A",
        "away_team": "B",
        "bookmaker": "book",
        "market": "total",
        "selection": "Over",
        "snapshot_time": "2023-01-01T12:00:00Z",
    }
    sid1 = make_line_movement_snapshot_id(row)
    sid2 = make_line_movement_snapshot_id(row)
    assert sid1 == sid2


# ---------------------------------------------------------------------------
# Canonical row
# ---------------------------------------------------------------------------


def test_build_canonical_line_movement_snapshot_row_contains_target_fields():
    row = {
        "source_name": "test",
        "source_key": "tk",
        "sport": "soccer",
        "event_date": "2023-01-01",
        "home_team": "A",
        "away_team": "B",
        "bookmaker": "book",
        "market": "1x2",
        "selection": "Home",
        "snapshot_time": "2023-01-01T12:00:00Z",
    }
    result = build_canonical_line_movement_snapshot_row(row)
    assert result["ok"] is True
    snap = result["snapshot_row"]
    expected_fields = [
        "snapshot_id",
        "event_id",
        "odds_id",
        "source_key",
        "source_file",
        "sport",
        "league",
        "event_date",
        "home_team",
        "away_team",
        "bookmaker",
        "market",
        "market_family",
        "selection",
        "player_name",
        "team_name",
        "line_value",
        "odds_value",
        "implied_probability",
        "snapshot_label",
        "snapshot_time",
        "raw_market_name",
        "raw_selection_name",
        "created_at",
        "updated_at",
    ]
    for f in expected_fields:
        assert f in snap, f"Missing field {f}"


def test_build_canonical_line_movement_snapshot_row_allows_blank_event_id_for_phase_10h21():
    row = {
        "source_name": "test",
        "source_key": "tk",
        "sport": "soccer",
        "event_date": "2023-01-01",
        "home_team": "A",
        "away_team": "B",
        "bookmaker": "book",
        "market": "1x2",
        "selection": "Home",
        "snapshot_time": "2023-01-01T12:00:00Z",
        # no source_event_id
    }
    result = build_canonical_line_movement_snapshot_row(row)
    assert result["ok"] is True
    assert result["snapshot_row"]["event_id"] == ""  # blank for now


# ---------------------------------------------------------------------------
# Preview batch
# ---------------------------------------------------------------------------


def test_build_line_movement_import_preview_empty_rows():
    result = build_line_movement_import_preview([])
    assert result["ok"] is True
    assert result["total_rows"] == 0
    assert "no_rows" in result["warnings"]


def test_build_line_movement_import_preview_counts_valid_and_invalid_rows():
    rows = [
        {},  # invalid
        {
            "source_name": "test",
            "source_key": "tk",
            "sport": "soccer",
            "event_date": "2023-01-01",
            "home_team": "A",
            "away_team": "B",
            "bookmaker": "book",
            "market": "1x2",
            "selection": "Home",
            "snapshot_time": "2023-01-01T12:00:00Z",
        },  # valid
    ]
    result = build_line_movement_import_preview(rows)
    assert result["ok"] is True
    assert result["total_rows"] == 2
    assert result["valid_rows"] == 1
    assert len(result["invalid_rows"]) == 1
    assert result["invalid_rows"][0]["row_index"] == 0


def test_build_line_movement_import_preview_respects_limit():
    rows = [
        {
            "source_name": "test",
            "source_key": "tk",
            "sport": "soccer",
            "event_date": "2023-01-01",
            "home_team": "A",
            "away_team": "B",
            "bookmaker": "book",
            "market": "1x2",
            "selection": "Home",
            "snapshot_time": "2023-01-01T12:00:00Z",
        }
        for _ in range(50)
    ]
    result = build_line_movement_import_preview(rows, limit=5)
    assert result["ok"] is True
    assert len(result["preview_rows"]) <= 5


# ---------------------------------------------------------------------------
# Describe contract
# ---------------------------------------------------------------------------


def test_describe_line_movement_import_contract_mentions_no_vendor_import():
    lines = describe_line_movement_import_contract()
    combined = " ".join(lines)
    assert "does not connect to vendors" in combined


def test_describe_line_movement_import_contract_mentions_phase_10h21():
    lines = describe_line_movement_import_contract()
    combined = " ".join(lines)
    assert "Phase 10H21" in combined


def test_contract_does_not_use_moneyline_or_1x2_as_preferred_output():
    c = build_vendor_neutral_line_movement_contract()
    # The normalizer never uses moneyline_or_1x2 as output
    assert normalize_line_movement_market_family("moneyline") != "moneyline_or_1x2"
    assert normalize_line_movement_market_family("1x2") != "moneyline_or_1x2"
    # also ensure contract output fields don't contain that string
    for field_list in [c["required_input_fields"], c["optional_input_fields"]]:
        for f in field_list:
            assert "moneyline_or_1x2" not in f
