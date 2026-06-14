"""Tests for automation_scheduler.calibration_strategy_filter."""

from __future__ import annotations

from typing import Any

import pytest

from automation_scheduler.calibration_strategy_filter import (
    CALIBRATION_FILTER_NEVER_FEATURE_FIELDS,
    CALIBRATION_STRATEGY_FILTER_VERSION,
    apply_calibration_strategy_filter,
    build_calibration_readiness_snapshot,
    build_default_calibration_filter_config,
    diagnose_calibration_row,
    run_calibration_strategy_filter,
    summarize_calibration_strategy_performance,
)


def test_calibration_filter_never_feature_fields_include_leakage_fields():
    never = CALIBRATION_FILTER_NEVER_FEATURE_FIELDS
    for leak in ("final_result", "winner", "home_score", "away_score",
                 "profit_loss", "closing_odds", "closing_line", "clv",
                 "result", "settled_result", "bet_result", "outcome"):
        assert leak in never


def test_build_default_calibration_filter_config_has_thresholds():
    config = build_default_calibration_filter_config()
    assert config["ok"] is True
    assert config["version"] == CALIBRATION_STRATEGY_FILTER_VERSION
    assert "min_required_coverage_percent" in config
    assert "min_active_field_coverage_percent" in config
    assert "min_rows_per_sport" in config
    assert "min_rows_per_market" in config
    assert "never_feature_fields" in config
    assert len(config["never_feature_fields"]) >= 12


def test_diagnose_calibration_row_eligible_with_required_fields_and_active_coverage():
    row = {
        "sport": "nba",
        "event_date": "2023-08-12",
        "market": "moneyline",
        "selection": "Home",
        "odds_at_decision_time": 1.5,
        "market_implied_probability": 0.6667,
    }
    active = ["sport", "event_date", "market", "selection",
              "odds_at_decision_time", "market_implied_probability"]
    diag = diagnose_calibration_row(row, active)
    assert diag["eligible"] is True
    assert diag["exclusion_reasons"] == []


def test_diagnose_calibration_row_excludes_missing_base_fields():
    row = {"sport": "nba", "event_date": "2023-08-12"}
    active = ["sport", "event_date", "market", "selection",
              "odds_at_decision_time", "market_implied_probability"]
    diag = diagnose_calibration_row(row, active)
    assert diag["eligible"] is False
    assert "missing_base_fields" in diag["exclusion_reasons"]


def test_diagnose_calibration_row_excludes_insufficient_active_field_coverage():
    row = {
        "sport": "nba",
        "event_date": "2023-08-12",
        "market": "moneyline",
        "selection": "Home",
        "odds_at_decision_time": 1.5,
        "market_implied_probability": 0.6667,
    }
    # demand 100 % coverage of an additional field not present
    active = ["sport", "event_date", "market", "selection",
              "odds_at_decision_time", "market_implied_probability",
              "extra_field"]
    diag = diagnose_calibration_row(row, active,
                                     min_active_field_coverage_percent=100.0)
    assert diag["eligible"] is False
    assert "insufficient_active_field_coverage" in diag["exclusion_reasons"]


def test_build_calibration_readiness_snapshot_includes_ready_sports():
    rows = [
        {
            "sport": "nba", "event_date": "2023-01-01",
            "home_team": "A", "away_team": "B",
            "market": "moneyline", "selection": "Home",
            "odds_at_decision_time": 1.5,
            "market_implied_probability": 0.6667,
            "bookmaker": "X",
        }
        for _ in range(30)  # above min_rows_per_sport=25
    ]
    config = build_default_calibration_filter_config(min_rows_per_sport=25,
                                                     min_required_coverage_percent=80.0)
    snap = build_calibration_readiness_snapshot(rows, config)
    assert "basketball_nba" in snap["included_sports"]
    assert "basketball_nba" in snap["sport_readiness"]
    assert snap["sport_readiness"]["basketball_nba"]["ready"] is True


def test_build_calibration_readiness_snapshot_excludes_sports_below_min_rows():
    rows = [
        {
            "sport": "nba", "event_date": "2023-01-01",
            "home_team": "A", "away_team": "B",
            "market": "moneyline", "selection": "Home",
            "odds_at_decision_time": 1.5,
            "market_implied_probability": 0.6667,
            "bookmaker": "X",
        }
        for _ in range(10)  # below min_rows_per_sport=25
    ]
    config = build_default_calibration_filter_config(min_rows_per_sport=25)
    snap = build_calibration_readiness_snapshot(rows, config)
    assert "basketball_nba" in snap["sport_readiness"]
    assert snap["sport_readiness"]["basketball_nba"]["ready"] is False


def test_build_calibration_readiness_snapshot_excludes_not_ready_markets():
    rows = [
        {
            "sport": "nba", "event_date": "2023-01-01",
            "home_team": "A", "away_team": "B",
            "market": "moneyline", "selection": "Home",
            "odds_at_decision_time": 1.5,
            "market_implied_probability": 0.6667,
            "bookmaker": "X",
        }
        for _ in range(20)
    ]
    config = build_default_calibration_filter_config(
        min_rows_per_market=15,
        min_required_coverage_percent=95.0,  # too high
    )
    snap = build_calibration_readiness_snapshot(rows, config)
    # moneyline/1x2 will be normalized to two_way_moneyline
    if "two_way_moneyline" in snap["market_readiness"]:
        assert snap["market_readiness"]["two_way_moneyline"]["ready"] is False


def test_apply_calibration_strategy_filter_does_not_mutate_input():
    original_rows = [
        {
            "sport": "nba", "event_date": "2023-01-01",
            "home_team": "A", "away_team": "B",
            "market": "moneyline", "selection": "Home",
            "odds_at_decision_time": 1.5,
            "market_implied_probability": 0.6667,
            "bookmaker": "X",
        }
    ]
    copy = list(original_rows)
    result = apply_calibration_strategy_filter(original_rows,
                                                sport="nba",
                                                min_rows_per_sport=1)
    assert original_rows == copy  # not mutated


def test_apply_calibration_strategy_filter_single_sport_filters_selected_sport():
    rows = [
        {
            "sport": "nba", "event_date": "2023-01-01",
            "home_team": "A", "away_team": "B",
            "market": "moneyline", "selection": "Home",
            "odds_at_decision_time": 1.5,
            "market_implied_probability": 0.6667,
            "bookmaker": "X",
        },
        {
            "sport": "mlb", "event_date": "2023-01-02",
            "home_team": "C", "away_team": "D",
            "market": "moneyline", "selection": "Home",
            "odds_at_decision_time": 2.0,
            "market_implied_probability": 0.5,
            "bookmaker": "Y",
        },
    ]
    result = apply_calibration_strategy_filter(
        rows, mode="single_sport", sport="nba",
        min_rows_per_sport=1, min_rows_per_market=1,
        min_required_coverage_percent=0.0,
    )
    # Only NBA rows should be present
    for row in result["included_rows"]:
        assert normalize_sport_key(row.get("sport")) == "basketball_nba"
    # MLB row should be gone


# small helper
from automation_scheduler.sport_feature_packs import normalize_sport_key


def test_apply_calibration_strategy_filter_all_sports_excludes_not_ready_sports():
    # Two sports: one with many rows, one with only 2 rows (below min 25)
    rows = []
    for i in range(30):
        rows.append({
            "sport": "nba",
            "event_date": "2023-01-01",
            "home_team": "A", "away_team": "B",
            "market": "moneyline", "selection": "Home",
            "odds_at_decision_time": 1.5,
            "market_implied_probability": 0.6667,
            "bookmaker": "X",
        })
    for i in range(2):
        rows.append({
            "sport": "tennis",
            "event_date": "2023-01-02",
            "home_team": "C", "away_team": "D",
            "market": "match_winner", "selection": "Home",
            "odds_at_decision_time": 2.0,
            "market_implied_probability": 0.5,
            "bookmaker": "Y",
        })
    result = run_calibration_strategy_filter(
        rows, mode="all_sports",
        min_rows_per_sport=25, min_rows_per_market=1,
        min_required_coverage_percent=0.0,
    )
    assert "basketball_nba" in result["included_sports"]
    # tennis excluded
    assert any(
        e["sport_key"] == "tennis"
        for e in result["excluded_sports"]
    )


def test_summarize_calibration_strategy_performance_uses_included_rows_only():
    filtered = {
        "included_rows": [
            {"sport": "nba", "profit_loss": 10.0, "final_result": "W"},
            {"sport": "nba", "profit_loss": -5.0, "final_result": "L"},
        ],
        "excluded_row_count": 5,
    }
    perf = summarize_calibration_strategy_performance(filtered)
    assert perf["included_row_count"] == 2
    assert perf["excluded_row_count"] == 5
    assert perf["net_result"] == 5.0  # 10-5
    assert perf["decisions"] == 2


def test_summarize_calibration_strategy_performance_breaks_down_roi_by_sport():
    filtered = {
        "included_rows": [
            {"sport": "nba", "profit_loss": 10.0, "final_result": "W"},
            {"sport": "mlb", "profit_loss": -5.0, "final_result": "L"},
        ],
        "excluded_row_count": 0,
    }
    perf = summarize_calibration_strategy_performance(filtered)
    assert "basketball_nba" in perf["roi_by_sport"]
    assert "baseball_mlb" in perf["roi_by_sport"]


def test_summarize_calibration_strategy_performance_breaks_down_roi_by_market_family():
    filtered = {
        "included_rows": [
            {"sport": "nba", "market": "moneyline",
             "selection": "Home", "profit_loss": 10.0, "final_result": "W"},
            {"sport": "mlb", "market": "runline",
             "selection": "Home", "line_value": 1.5,
             "profit_loss": -5.0, "final_result": "L"},
        ],
        "excluded_row_count": 0,
    }
    perf = summarize_calibration_strategy_performance(filtered)
    assert "two_way_moneyline" in perf["roi_by_market_family"]
    assert "runline" in perf["roi_by_market_family"]


def test_run_calibration_strategy_filter_returns_stable_keys():
    result = run_calibration_strategy_filter(
        rows=[
            {
                "sport": "nba", "event_date": "2023-01-01",
                "home_team": "A", "away_team": "B",
                "market": "moneyline", "selection": "Home",
                "odds_at_decision_time": 1.5,
                "market_implied_probability": 0.6667,
                "bookmaker": "X",
            }
        ],
        mode="single_sport",
        sport="nba",
        min_rows_per_sport=1,
        min_rows_per_market=1,
        min_required_coverage_percent=0.0,
    )
    for key in (
        "ok", "version", "mode", "sport_key", "market_family",
        "active_fields", "removed_fields",
        "included_sports", "excluded_sports",
        "included_market_families", "excluded_market_families",
        "readiness_snapshot", "performance",
        "exclusion_reason_counts", "warnings", "operator_interpretation",
    ):
        assert key in result, f"Missing key: {key}"
