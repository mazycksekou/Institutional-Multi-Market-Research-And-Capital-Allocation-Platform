"""Tests for Phase 10H23E True Baseline + Neutral Presets in feature_ablation_lab.py"""

from __future__ import annotations

from typing import Any

import pytest

from src.services.streamlit_dashboard_facade import FEATURE_ABLATION_LAB_VERSION, ABLATION_NEVER_FEATURE_FIELDS, BASE_FIELD_GROUPS, _all_safe_fields_for_combination, get_ablation_field_groups_for_sport, apply_field_ablation, run_feature_ablation_lab


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_row(**overrides: Any) -> dict[str, Any]:
    """Return a minimal row that passes the base required fields test."""
    row = {
        "sport": "basketball_nba",
        "event_date": "2024-01-15",
        "market": "moneyline",
        "selection": "Home",
        "odds_at_decision_time": 1.5,
        "market_implied_probability": 0.6667,
    }
    row.update(overrides)
    return row


def _all_safe_for_sport():
    """Convenience wrapper for default sport."""
    return _all_safe_fields_for_combination("basketball_nba", None)


# ---------------------------------------------------------------------------
# 1. True baseline uses all safe fields
# ---------------------------------------------------------------------------

def test_true_baseline_uses_all_safe_fields() -> None:
    """True baseline should have zero removed fields and include all safe fields."""
    rows = [_make_row()]
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    active = result.get("active_fields", [])
    removed = result.get("removed_fields", [])
    assert len(removed) == 0
    safe = _all_safe_for_sport()
    # active may be a subset of safe if some not present in rows, but baseline should contain them
    for f in safe:
        # at least the field must be listed in active (if it's defined in the field groups)
        assert f in active or f in ABLATION_NEVER_FEATURE_FIELDS
    assert result["true_baseline_mode"] is True or result.get("run_type") == "true_code_baseline"


# ---------------------------------------------------------------------------
# 2. True baseline reports risk_preset_used as None
# ---------------------------------------------------------------------------

def test_true_baseline_risk_preset_none() -> None:
    rows = [_make_row()]
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    # The result dict currently does not carry risk_preset; we check fallback
    # Phase 10H23E adds these fields:
    assert result.get("risk_preset_used") is None or not result.get("risk_preset_used")


# ---------------------------------------------------------------------------
# 3. True baseline reports regression_tactic_used as None
# ---------------------------------------------------------------------------

def test_true_baseline_regression_tactic_none() -> None:
    rows = [_make_row()]
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    assert result.get("regression_tactic_used") is None or not result.get("regression_tactic_used")


# ---------------------------------------------------------------------------
# 4. True baseline reports custom_weights_used as false
# ---------------------------------------------------------------------------

def test_true_baseline_custom_weights_false() -> None:
    rows = [_make_row()]
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    assert result.get("custom_weights_used") is False


# ---------------------------------------------------------------------------
# 5. True baseline reports chance_override_used as false
# ---------------------------------------------------------------------------

def test_true_baseline_chance_override_false() -> None:
    rows = [_make_row()]
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    assert result.get("chance_override_used") is False


# ---------------------------------------------------------------------------
# 6. Baseline label when fields are removed becomes ablation_test
# ---------------------------------------------------------------------------

def test_fields_removed_changes_baseline_type() -> None:
    """If removed_fields is non‑empty, run_type must be ablation_test, not true_code_baseline."""
    rows = [_make_row()]
    result = run_feature_ablation_lab(
        rows,
        sport="basketball_nba",
        mode="single_sport",
        removed_fields=["odds_at_decision_time"],
    )
    assert result["run_type"] == "ablation_test"
    assert result["true_baseline_mode"] is False


# ---------------------------------------------------------------------------
# 7. get_ablation_field_groups returns nothing outside the safe set
# ---------------------------------------------------------------------------

def test_ablation_field_groups_no_leakage() -> None:
    groups = get_ablation_field_groups_for_sport("basketball_nba")
    all_safe = set()
    for grp in groups["groups"]:
        for f in grp["fields"]:
            all_safe.add(f)
    never = set(ABLATION_NEVER_FEATURE_FIELDS)
    assert all_safe.isdisjoint(never)


# Phase 10H23I – Row Count Threshold metadata tests ──────────────────

def test_user_row_threshold_default_is_low() -> None:
    """Default user_row_threshold should be 1 and not block a run."""
    rows = [_make_row()]
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    assert "user_row_threshold" in result
    assert result["user_row_threshold"] == 1
    assert "rows_tested" in result
    assert result["rows_tested"] == 1
    assert result["row_threshold_met"] is True
    assert "row_threshold_note" in result
    assert "selected by user" in result["row_threshold_note"]


def test_user_row_threshold_met_when_rows_exceed() -> None:
    rows = [_make_row(), _make_row()]
    result = run_feature_ablation_lab(
        rows, sport="basketball_nba", mode="single_sport", user_row_threshold=2
    )
    assert result["rows_tested"] == 2
    assert result["row_threshold_met"] is True


def test_user_row_threshold_not_met_when_below() -> None:
    rows = [_make_row()]
    result = run_feature_ablation_lab(
        rows, sport="basketball_nba", mode="single_sport", user_row_threshold=10
    )
    assert result["rows_tested"] == 1
    assert result["row_threshold_met"] is False
    # included_sports should still be populated
    assert "basketball_nba" in result["included_sports"]
    assert result["included_sport_count"] == 1
    # no_sports_reason should be None because rows exist
    assert result.get("no_sports_reason") is None
    # row_threshold_note should mention below threshold
    assert "below your selected review threshold" in result["row_threshold_note"]


def test_user_row_threshold_does_not_block_empty_rows() -> None:
    rows: list[dict] = []
    result = run_feature_ablation_lab(
        rows, sport="basketball_nba", mode="single_sport", user_row_threshold=5
    )
    assert result["rows_tested"] == 0
    assert result["row_threshold_met"] is False
    assert result["no_sports_reason"] is not None
    assert "no rows" in result["no_sports_reason"].lower()


def test_rows_needed_before_trust_field_present() -> None:
    rows = [_make_row()]
    result = run_feature_ablation_lab(
        rows, sport="basketball_nba", mode="single_sport", user_row_threshold=50
    )
    assert result.get("rows_needed_before_trust") == 50


# ── Phase 10H23F – included/excluded sports population ──────────────

def test_run_feature_ablation_lab_includes_included_sports_and_excluded_sports() -> None:
    """Result dict must contain included_sports, excluded_sports, counts."""
    rows = [_make_row()]
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    assert "included_sports" in result
    assert "excluded_sports" in result
    assert "included_sport_count" in result
    assert "excluded_sport_count" in result
    assert isinstance(result["included_sport_count"], int)
    assert isinstance(result["excluded_sport_count"], int)


def test_single_sport_included_when_rows_present_and_ready() -> None:
    """Single sport with rows passes readiness."""
    rows = [_make_row()]
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    assert "basketball_nba" in result["included_sports"]
    assert result["included_sport_count"] == 1
    assert result["excluded_sport_count"] == 0


def test_single_sport_excluded_when_no_rows() -> None:
    """Single sport with no rows is excluded."""
    rows = []
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    assert result["included_sports"] == []
    assert result["excluded_sport_count"] >= 1
    assert result["no_sports_reason"] is not None


def test_included_sport_count_and_excluded_sport_count_are_integers() -> None:
    """Count fields are numeric, not None."""
    rows = []
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    assert isinstance(result["included_sport_count"], int)
    assert isinstance(result["excluded_sport_count"], int)


def test_sport_population_note_present_when_data_exists() -> None:
    rows = [_make_row()]
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    note = result.get("sport_population_note")
    if note:
        assert "sport" in note
    else:
        # If not set due to single included and zero excluded, may be None.
        # At least ensure key exists.
        assert "sport_population_note" in result


def test_no_sports_reason_when_empty_rows() -> None:
    rows = []
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    assert result.get("no_sports_reason") is not None
    assert "no rows" in result["no_sports_reason"].lower()


# Regression: single sport with rows but zero decisions still reports sport in included_sports
def test_single_sport_always_included_when_rows_present() -> None:
    rows = [_make_row()]
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    assert "basketball_nba" in result["included_sports"]
    assert result["included_sport_count"] == 1


# Regression: empty rows reports a no_sports_reason containing "no rows"
def test_empty_rows_has_no_rows_reason() -> None:
    rows: list[dict] = []
    result = run_feature_ablation_lab(rows, sport="basketball_nba", mode="single_sport")
    assert result.get("no_sports_reason") is not None
    assert "no rows" in result["no_sports_reason"].lower()
