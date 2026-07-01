from pathlib import Path

from src.services.streamlit_dashboard_facade import validate_paper_only_fixture_rows
from src.services.streamlit_dashboard_data import build_paper_only_evaluation_readiness_payload, build_paper_only_evaluation_readiness_rows
from src.core.quant_engine import evaluate_paper_only_fixture_rows


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "PHASE10K8G_PAPER_ONLY_EVALUATION_READINESS_ADAPTER.md"
QUANT_ENGINE_PATH = REPO_ROOT / "src" / "core" / "quant_engine.py"
BACKTEST_DATASET_BUILDER_PATH = REPO_ROOT / "src" / "backtesting" / "backtest_dataset_builder.py"
DASHBOARD_DATA_PATH = REPO_ROOT / "src" / "services" / "streamlit_dashboard_data.py"
STREAMLIT_APP_PATH = REPO_ROOT / "streamlit_app.py"
PHASE_10K6K_TEST_PATH = (
    REPO_ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_paper_only_evaluation_readiness_adapter_round_trip():
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

    validation_result = validate_paper_only_fixture_rows([valid_row])
    assert validation_result["rows_valid"] == 1
    evaluation_result = evaluate_paper_only_fixture_rows([valid_row])
    payload = build_paper_only_evaluation_readiness_payload(evaluation_result)

    assert payload["rows_tested"] == 1
    assert payload["rows_valid"] == 1
    assert payload["rows_invalid"] == 0
    assert payload["validation_status"] == "valid"
    assert payload["evaluations_count"] == 1
    assert "pending" in payload["paper_result_counts"]
    assert payload["total_paper_ev"] == valid_row["expected_value"]
    assert payload["total_paper_stake_units"] == valid_row["stake_units"]
    assert payload["prediction_testing_started"] is False
    assert payload["live_connectors_enabled"] is False
    assert payload["api_calls_enabled"] is False
    assert payload["database_writes_enabled"] is False

    rows = build_paper_only_evaluation_readiness_rows(evaluation_result)
    assert rows
    assert all({"label", "value", "policy_note"} <= set(row) for row in rows)
    assert any(row["label"] == "Evaluations count" for row in rows)
    assert any(row["label"] == "Paper result counts" for row in rows)

    invalid_row = dict(valid_row)
    invalid_row.pop("selection")
    invalid_result = evaluate_paper_only_fixture_rows([invalid_row])
    invalid_payload = build_paper_only_evaluation_readiness_payload(invalid_result)
    assert invalid_payload["validation_status"] == "needs_review"
    assert invalid_payload["rows_invalid"] > 0
    assert invalid_payload["missing_field_reasons"]


def test_phase_report_and_source_guardrails():
    report_text = _read_text(REPORT_PATH)
    quant_text = _read_text(QUANT_ENGINE_PATH)
    backtest_text = _read_text(BACKTEST_DATASET_BUILDER_PATH)
    dashboard_text = _read_text(DASHBOARD_DATA_PATH)
    streamlit_text = _read_text(STREAMLIT_APP_PATH)
    phase_10k6k_text = _read_text(PHASE_10K6K_TEST_PATH)

    required_report_strings = [
        "Paper-Only Evaluation Readiness Adapter",
        "automation_scheduler/streamlit_dashboard_data.py",
        "quant_engine.py",
        "evaluate_paper_only_fixture_rows",
        "build_paper_only_evaluation_readiness_payload",
        "build_paper_only_evaluation_readiness_rows",
        "build_paper_only_fixture_readiness_payload",
        "build_paper_only_fixture_readiness_rows",
        "build_readiness_display_payload",
        "build_readiness_display_rows",
        "existing owner rule",
        "paper-only prediction testing",
        "local fixture-backed testing",
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "missing_field_reasons",
        "warning_reasons",
        "evaluations",
        "evaluations_count",
        "paper_result_counts",
        "total_paper_ev",
        "total_paper_stake_units",
        "source_type",
        "execution_mode",
        "prediction_testing_started",
        "live_connectors_enabled",
        "api_calls_enabled",
        "database_writes_enabled",
        "no prediction testing started in 10K8G",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no duplicate owner created",
        "no temporary git shim",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "user threshold review-only",
        "validity check only",
        "implementation reviewed in 10K8G",
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



