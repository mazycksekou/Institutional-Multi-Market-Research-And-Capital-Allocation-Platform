from __future__ import annotations

from pathlib import Path

from automation_scheduler.streamlit_dashboard_data import (
    build_zero_dte_evaluation_readiness_payload,
    build_zero_dte_evaluation_readiness_rows,
    build_zero_dte_validation_readiness_payload,
    build_zero_dte_validation_readiness_rows,
)
from automation_scheduler.technical_signal_fields import TECHNICAL_SIGNAL_FIELDS
from automation_scheduler.zero_dte_fixture_template import (
    build_zero_dte_fixture_template_row,
    build_zero_dte_paper_pipeline_result,
    evaluate_zero_dte_paper_fixture_rows,
    validate_zero_dte_fixture_rows,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8Y_0DTE_PREDICTION_TESTING_READINESS_REVIEW.md"
APP = ROOT / "streamlit_app.py"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8y_0dte_prediction_testing_readiness_review() -> None:
    assert REPORT.is_file(), "Expected the 10K8Y review report to exist."
    assert APP.is_file(), "Expected streamlit_app.py to remain present."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    app_text = read_text(APP)
    report_text = read_text(REPORT)

    assert "show_zero_dte_validation_readiness_preview" in app_text
    assert "show_zero_dte_paper_evaluation_preview" in app_text
    assert "show_zero_dte_paper_pipeline_preview" in app_text

    row = build_zero_dte_fixture_template_row()
    row.update(
        {
            "outcome_known": False,
            "result_label": "pending",
            "model_probability": 0.0,
            "market_odds_american": 0,
            "premium": 0.0,
            "spread_percent": 0.0,
        }
    )
    validation_result = validate_zero_dte_fixture_rows([row])
    validation_payload = build_zero_dte_validation_readiness_payload(validation_result)
    validation_rows = build_zero_dte_validation_readiness_rows(validation_payload)
    evaluation_result = evaluate_zero_dte_paper_fixture_rows([row])
    evaluation_payload = build_zero_dte_evaluation_readiness_payload(evaluation_result)
    evaluation_rows = build_zero_dte_evaluation_readiness_rows(evaluation_payload)
    pipeline_result = build_zero_dte_paper_pipeline_result([row])

    assert validation_payload["validity_check_only"] is True
    assert validation_payload["user_threshold_review_only"] is True
    assert validation_payload["quality_not_automatically_labeled"] is True
    assert validation_payload["low_sample_size_does_not_hide_valid_results"] is True

    assert evaluation_payload["review_only"] is True
    assert evaluation_payload["paper_only"] is True
    assert evaluation_payload["user_threshold_review_only"] is True
    assert evaluation_payload["quality_not_automatically_labeled"] is True
    assert evaluation_payload["low_sample_size_does_not_hide_valid_results"] is True

    assert pipeline_result["review_only"] is True
    assert pipeline_result["paper_only"] is True
    assert pipeline_result["local_fixture_backed"] is True
    assert pipeline_result["user_threshold_review_only"] is True
    assert pipeline_result["quality_not_automatically_labeled"] is True
    assert pipeline_result["low_sample_size_does_not_hide_valid_results"] is True

    for result in (validation_payload, evaluation_payload, pipeline_result):
        assert result["prediction_testing_started"] is False
        assert result["live_connectors_enabled"] is False
        assert result["api_calls_enabled"] is False
        assert result["database_writes_enabled"] is False
        assert result["broker_execution_enabled"] is False
        assert result["real_trade_execution_enabled"] is False

    assert validation_rows and evaluation_rows
    assert "paper_arbitrage_percentage" not in TECHNICAL_SIGNAL_FIELDS

    required_report_strings = [
        "0DTE Prediction Testing Readiness Review",
        "structurally ready for controlled paper-only prediction testing",
        "not ready for live trading",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls",
        "no database writes",
        "implementation reviewed in 10K8Y",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"
