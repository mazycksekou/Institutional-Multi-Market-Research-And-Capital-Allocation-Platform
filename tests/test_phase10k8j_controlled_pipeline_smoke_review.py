from pathlib import Path

from src.automation_scheduler_legacy.streamlit_dashboard_data import build_paper_only_fixture_pipeline_result


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "PHASE10K8J_CONTROLLED_PIPELINE_SMOKE_REVIEW.md"
QUANT_ENGINE_PATH = REPO_ROOT / "src" / "core" / "quant_engine.py"
BACKTEST_DATASET_BUILDER_PATH = REPO_ROOT / "src" / "automation_scheduler_legacy" / "backtest_dataset_builder.py"
DASHBOARD_DATA_PATH = REPO_ROOT / "src" / "automation_scheduler_legacy" / "streamlit_dashboard_data.py"
STREAMLIT_APP_PATH = REPO_ROOT / "streamlit_app.py"
PHASE_10K6K_TEST_PATH = (
    REPO_ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_controlled_pipeline_smoke_review_round_trip():
    valid_row = {
        "fixture_id": "fixture-1",
        "sport_or_market": "Sports",
        "event_id": "event-1",
        "prediction_target": "home_team",
        "selection": "home_team",
        "model_probability": 0.61,
        "market_odds_american": -110,
        "implied_probability": 0.55,
        "expected_value": 0.12,
        "stake_units": 1.25,
        "bankroll_snapshot": 1000,
        "result_label": "pending",
        "outcome_known": False,
        "source_type": "local_fixture",
        "execution_mode": "paper_only",
    }

    valid_result = build_paper_only_fixture_pipeline_result([valid_row])
    assert valid_result["rows_tested"] == 1
    assert valid_result["rows_valid"] == 1
    assert valid_result["rows_invalid"] == 0
    assert valid_result["validation_status"] == "valid"
    assert valid_result["evaluations_count"] == 1
    assert valid_result["readiness_payload"]
    assert valid_result["readiness_rows"]
    assert valid_result["prediction_testing_started"] is False
    assert valid_result["live_connectors_enabled"] is False
    assert valid_result["api_calls_enabled"] is False
    assert valid_result["database_writes_enabled"] is False

    invalid_row = dict(valid_row)
    invalid_row.pop("selection")
    invalid_result = build_paper_only_fixture_pipeline_result([invalid_row])
    assert invalid_result["rows_invalid"] > 0
    assert invalid_result["validation_status"] == "needs_review"
    assert invalid_result["missing_field_reasons"]
    assert invalid_result["readiness_rows"]
    assert all({"label", "value", "policy_note"} <= set(row) for row in invalid_result["readiness_rows"])


def test_phase_report_and_source_guardrails():
    report_text = _read_text(REPORT_PATH)
    quant_text = _read_text(QUANT_ENGINE_PATH)
    backtest_text = _read_text(BACKTEST_DATASET_BUILDER_PATH)
    dashboard_text = _read_text(DASHBOARD_DATA_PATH)
    streamlit_text = _read_text(STREAMLIT_APP_PATH)
    phase_10k6k_text = _read_text(PHASE_10K6K_TEST_PATH)

    required_report_strings = [
        "Controlled Pipeline Smoke Review",
        "existing owner rule",
        "paper-only prediction testing",
        "local fixture-backed testing",
        "no live money",
        "no production execution",
        "automation_scheduler/streamlit_dashboard_data.py",
        "build_paper_only_fixture_pipeline_result",
        "automation_scheduler/backtest_dataset_builder.py",
        "validate_paper_only_fixture_rows",
        "quant_engine.py",
        "evaluate_paper_only_fixture_rows",
        "build_paper_only_evaluation_readiness_payload",
        "build_paper_only_evaluation_readiness_rows",
        "validation_result",
        "evaluation_result",
        "readiness_payload",
        "readiness_rows",
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "missing_field_reasons",
        "warning_reasons",
        "evaluations_count",
        "paper_result_counts",
        "total_paper_ev",
        "total_paper_stake_units",
        "validation_status",
        "prediction_testing_started",
        "live_connectors_enabled",
        "api_calls_enabled",
        "database_writes_enabled",
        "valid fixture smoke",
        "invalid fixture smoke",
        "source-text guardrails",
        "no prediction testing started in 10K8J",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no duplicate owner created",
        "no temporary git shim",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "user threshold review-only",
        "validity check only",
        "implementation reviewed in 10K8J",
    ]
    for text in required_report_strings:
        assert text in report_text, text

    required_quant_strings = [
        "PAPER_ONLY_EVALUATION_REQUIRED_FIELDS",
        "evaluate_paper_only_fixture_rows",
        "paper_edge",
        "paper_ev",
        "paper_stake_units",
        "paper_result",
        "prediction_testing_started",
        "live_connectors_enabled",
        "api_calls_enabled",
        "database_writes_enabled",
    ]
    for text in required_quant_strings:
        assert text in quant_text, text

    required_backtest_strings = [
        "PAPER_ONLY_FIXTURE_REQUIRED_FIELDS",
        "PAPER_ONLY_FIXTURE_OPTIONAL_FIELDS",
        "validate_paper_only_fixture_rows",
        "prediction_testing_started",
        "live_connectors_enabled",
        "api_calls_enabled",
        "database_writes_enabled",
    ]
    for text in required_backtest_strings:
        assert text in backtest_text, text

    required_dashboard_strings = [
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "build_readiness_display_payload",
        "build_readiness_display_rows",
        "build_paper_only_fixture_readiness_payload",
        "build_paper_only_fixture_readiness_rows",
        "build_paper_only_evaluation_readiness_payload",
        "build_paper_only_evaluation_readiness_rows",
        "build_paper_only_fixture_pipeline_result",
        "threshold_review_only",
        "validity_is_backend_gate",
        "low_sample_size_does_not_hide_valid_results",
        "quality_not_automatically_labeled",
    ]
    for text in required_dashboard_strings:
        assert text in dashboard_text, text

    required_streamlit_strings = [
        "Feature Ablation Lab",
        "Bankroll Settings",
        "Instructions",
        "Sports",
        "0DTE Options",
        "Prediction Markets",
        "Data Warehouse",
        "Backtest Lab",
        "Model Diagnostics",
        "Arbitrage Lab",
        "Controlled Navigation Shell",
        "readiness display preview",
        "no prediction testing",
        "no live connectors",
        "no API calls",
        "no database writes",
    ]
    for text in required_streamlit_strings:
        assert text in streamlit_text, text

    forbidden_connector_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
    ]
    for text in forbidden_connector_strings:
        assert text not in streamlit_text, text

    assert "subprocess" not in phase_10k6k_text
    assert "git ls-files" not in phase_10k6k_text
    assert "git status" not in phase_10k6k_text
    assert "git shim" not in phase_10k6k_text

    assert not list(REPO_ROOT.glob("pages/*.py"))
    assert not list(REPO_ROOT.glob("app/pages/*.py"))
    assert not list(REPO_ROOT.glob("frontend/*.py"))
    assert not list(REPO_ROOT.glob("frontend/pages/*.py"))


