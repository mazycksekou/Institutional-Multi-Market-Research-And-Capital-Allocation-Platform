"""Tests for experiment_history_store.py (Phase 10H17).

Backend-only tests that do not require Streamlit.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from automation_scheduler.experiment_history_store import (
    EXPERIMENT_HISTORY_STORE_VERSION,
    ABLATION_NEVER_FEATURE_FIELDS,
    initialize_experiment_history_store,
    normalize_experiment_history_run_type,
    make_experiment_run_id,
    extract_experiment_history_metrics,
    sanitize_experiment_history_result,
    save_experiment_history_run,
    list_experiment_history_runs,
    get_experiment_history_run,
    compare_experiment_history_runs,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    return str(tmp_path / "test_history.db")


def _sample_ablation_result() -> dict:
    return {
        "ok": True,
        "version": "10H15",
        "mode": "single_sport",
        "sport_key": "basketball_nba",
        "market_family": "moneyline_or_1x2",
        "selected_groups": ["odds_fields"],
        "selected_fields": [],
        "removed_fields": ["line_movement_fields"],
        "active_fields": ["odds_at_decision_time", "market_implied_probability"],
        "included_sports": ["basketball_nba"],
        "excluded_sports": [],
        "included_market_families": ["moneyline_or_1x2"],
        "excluded_market_families": [],
        "performance": {
            "total_rows": 100,
            "included_row_count": 80,
            "excluded_row_count": 20,
            "eligible_rows": 70,
            "skipped_rows": 10,
            "settled_count": 50,
            "wins": 25,
            "losses": 20,
            "pushes": 5,
            "net_result": 15.5,
            "roi_percent": 3.2,
            "win_rate_percent": 55.0,
            "roi_by_sport": {"basketball_nba": {"rows": 80, "net_result": 15.5, "roi_percent": 3.2}},
            "roi_by_market_family": {"moneyline_or_1x2": {"rows": 80, "net_result": 15.5, "roi_percent": 3.2}},
            "warnings": [],
        },
        "warnings": [],
        "config": {"profile": "custom"},
    }


def _sample_calibration_result() -> dict:
    return {
        "ok": True,
        "version": "10H16",
        "mode": "all_sports",
        "sport_key": "all_sports",
        "market_family": "mixed",
        "included_sports": ["basketball_nba", "american_football_nfl"],
        "excluded_sports": [{"sport_key": "soccer_general", "reason": "not_ready"}],
        "included_market_families": ["moneyline_or_1x2", "spread_or_runline"],
        "excluded_market_families": [],
        "active_fields": ["odds_at_decision_time", "market_implied_probability"],
        "removed_fields": [],
        "selected_groups": [],
        "selected_fields": [],
        "performance": {
            "total_rows": 500,
            "included_row_count": 400,
            "excluded_row_count": 100,
            "eligible_rows": 350,
            "skipped_rows": 50,
            "settled_count": 200,
            "wins": 110,
            "losses": 80,
            "pushes": 10,
            "net_result": 25.0,
            "roi_percent": 2.5,
            "win_rate_percent": 57.89,
            "roi_by_sport": {},
            "roi_by_market_family": {},
            "warnings": ["Excluded 1 sport."],
        },
        "warnings": ["Excluded 1 sport."],
        "config": {"min_required_coverage_percent": 80.0},
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_initialize_experiment_history_store_creates_table(db_path: str) -> None:
    result = initialize_experiment_history_store(db_path)
    assert result["ok"] is True
    assert result["table"] == "experiment_history_runs"
    assert result["status"] == "created_or_exists"
    # second call should not fail
    result2 = initialize_experiment_history_store(db_path)
    assert result2["ok"] is True


def test_normalize_experiment_history_run_type_defaults() -> None:
    assert normalize_experiment_history_run_type("feature_ablation") == "feature_ablation"
    assert normalize_experiment_history_run_type("calibration_strategy_filter") == "calibration_strategy_filter"
    assert normalize_experiment_history_run_type("unknown") == "feature_ablation"
    assert normalize_experiment_history_run_type(None) == "feature_ablation"
    assert normalize_experiment_history_run_type(123) == "feature_ablation"


def test_make_experiment_run_id_unique() -> None:
    id1 = make_experiment_run_id()
    id2 = make_experiment_run_id()
    assert id1 != id2
    assert id1.startswith("exp_")
    assert "_" in id1


def test_extract_experiment_history_metrics_from_feature_ablation_result() -> None:
    result = _sample_ablation_result()
    metrics = extract_experiment_history_metrics(result)
    assert metrics["total_rows"] == 100
    assert metrics["included_row_count"] == 80
    assert metrics["excluded_row_count"] == 20
    assert metrics["eligible_rows"] == 70
    assert metrics["skipped_rows"] == 10
    assert metrics["settled_count"] == 50
    assert metrics["wins"] == 25
    assert metrics["losses"] == 20
    assert metrics["pushes"] == 5
    assert metrics["net_result"] == 15.5
    assert metrics["roi_percent"] == 3.2
    assert metrics["win_rate_percent"] == 55.0
    assert "roi_by_sport" in metrics
    assert "roi_by_market_family" in metrics
    assert metrics["warnings"] == []


def test_extract_experiment_history_metrics_from_calibration_result() -> None:
    result = _sample_calibration_result()
    metrics = extract_experiment_history_metrics(result)
    assert metrics["total_rows"] == 500
    assert metrics["included_row_count"] == 400
    assert metrics["excluded_row_count"] == 100


def test_sanitize_experiment_history_result_removes_leakage_active_fields() -> None:
    result = _sample_ablation_result()
    result["active_fields"] = [
        "odds_at_decision_time",
        "final_result",
        "winner",
        "profit_loss",
        "clv",
    ]
    sanitized = sanitize_experiment_history_result(result)
    safe_active = sanitized["active_fields"]
    for leak in ("final_result", "winner", "profit_loss", "clv"):
        assert leak not in safe_active
    assert "odds_at_decision_time" in safe_active
    # warns about removal
    assert any("leakage" in str(w).lower() for w in sanitized.get("warnings", []))


def test_save_experiment_history_run_inserts_row(db_path: str) -> None:
    result = _sample_ablation_result()
    saved = save_experiment_history_run(db_path, result, run_label="test_label", notes="first run")
    assert saved["ok"] is True
    assert saved["saved"] is True
    assert saved["run_id"] != ""
    assert saved["run_type"] == "feature_ablation"
    assert saved["run_label"] == "test_label"


def test_list_experiment_history_runs_empty_store(db_path: str) -> None:
    listing = list_experiment_history_runs(db_path, limit=10)
    assert listing["ok"] is True
    assert listing["runs"] == []
    assert listing["total"] == 0


def test_list_experiment_history_runs_returns_recent_runs(db_path: str) -> None:
    save_experiment_history_run(db_path, _sample_ablation_result(), run_label="first")
    save_experiment_history_run(db_path, _sample_calibration_result(), run_label="second")
    listing = list_experiment_history_runs(db_path, limit=10)
    assert listing["ok"] is True
    assert listing["total"] == 2
    assert listing["runs"][0]["run_label"] == "second"  # newest first
    assert listing["runs"][1]["run_label"] == "first"


def test_get_experiment_history_run_returns_full_result(db_path: str) -> None:
    saved = save_experiment_history_run(db_path, _sample_ablation_result(), run_label="get_test")
    run_id = saved["run_id"]
    retrieved = get_experiment_history_run(db_path, run_id)
    assert retrieved["ok"] is True
    assert retrieved["found"] is True
    run = retrieved["run"]
    assert run["run_id"] == run_id
    assert run["run_type"] == "feature_ablation"
    # decode JSON fields
    active = run.get("active_fields_json")
    assert isinstance(active, list) or active is None
    perf = run.get("performance_json")
    assert isinstance(perf, dict) or perf is None


def test_get_experiment_history_run_missing_returns_not_found(db_path: str) -> None:
    retrieved = get_experiment_history_run(db_path, "nonexistent")
    assert retrieved["ok"] is True
    assert retrieved["found"] is False
    assert "not found" in " ".join(retrieved.get("warnings", [])).lower()


def test_compare_experiment_history_runs_returns_baseline_and_deltas(db_path: str) -> None:
    r1 = save_experiment_history_run(db_path, _sample_ablation_result(), run_label="baseline")
    res2 = _sample_calibration_result()
    res2["performance"]["roi_percent"] = 5.0
    res2["performance"]["win_rate_percent"] = 60.0
    res2["performance"]["included_row_count"] = 300
    r2 = save_experiment_history_run(db_path, res2, run_label="comparison")
    comp = compare_experiment_history_runs(db_path, [r1["run_id"], r2["run_id"]])
    assert comp["ok"] is True
    rows = comp["comparison_rows"]
    assert len(rows) == 2
    # baseline
    assert rows[0]["roi_delta_vs_baseline"] == 0.0
    assert rows[1]["roi_delta_vs_baseline"] == round(5.0 - 3.2, 2)
    assert rows[1]["win_rate_delta_vs_baseline"] == round(60.0 - 55.0, 2)
    assert rows[1]["included_row_delta_vs_baseline"] == 300 - 80


def test_compare_experiment_history_runs_handles_empty_ids(db_path: str) -> None:
    comp = compare_experiment_history_runs(db_path, [])
    assert comp["ok"] is False
    assert "no run ids" in " ".join(comp.get("warnings", [])).lower()


def test_history_does_not_mutate_input_result(db_path: str) -> None:
    result = _sample_ablation_result()
    original_deep = json.loads(json.dumps(result))
    save_experiment_history_run(db_path, result)
    assert result == original_deep


def test_history_json_fields_round_trip(db_path: str) -> None:
    result = _sample_ablation_result()
    saved = save_experiment_history_run(db_path, result)
    run_id = saved["run_id"]
    retrieved = get_experiment_history_run(db_path, run_id)
    active = retrieved.get("run", {}).get("active_fields_json")
    parsed = json.loads(json.dumps(active)) if isinstance(active, str) else active
    assert parsed == result["active_fields"]
