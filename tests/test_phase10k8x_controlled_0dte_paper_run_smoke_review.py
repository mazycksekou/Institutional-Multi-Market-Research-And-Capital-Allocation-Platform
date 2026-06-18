from __future__ import annotations

from pathlib import Path

from automation_scheduler.streamlit_dashboard_data import (
    build_zero_dte_evaluation_readiness_payload,
    build_zero_dte_evaluation_readiness_rows,
    build_zero_dte_validation_readiness_payload,
    build_zero_dte_validation_readiness_rows,
)
from automation_scheduler.zero_dte_fixture_template import (
    build_zero_dte_fixture_template_row,
    build_zero_dte_paper_pipeline_result,
    evaluate_zero_dte_paper_fixture_rows,
    validate_zero_dte_fixture_rows,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8X_CONTROLLED_0DTE_PAPER_RUN_SMOKE_REVIEW.md"
APP = ROOT / "streamlit_app.py"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8x_controlled_0dte_paper_run_smoke_review() -> None:
    assert REPORT.is_file(), "Expected the 10K8X review report to exist."
    assert APP.is_file(), "Expected streamlit_app.py to remain present."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    app_text = read_text(APP)
    report_text = read_text(REPORT)

    pending_row = build_zero_dte_fixture_template_row()
    pending_row.update(
        {
            "outcome_known": False,
            "result_label": "pending",
            "model_probability": 0.0,
            "market_odds_american": 0,
            "premium": 0.0,
            "spread_percent": 0.0,
        }
    )
    win_row = dict(pending_row, outcome_known=True, result_label="win")
    loss_row = dict(pending_row, outcome_known=True, result_label="loss")
    invalid_row = dict(pending_row)
    invalid_row.pop("fixture_id", None)
    rows = [pending_row, win_row, loss_row, invalid_row]

    validation_result = validate_zero_dte_fixture_rows(rows)
    validation_payload = build_zero_dte_validation_readiness_payload(validation_result)
    validation_rows = build_zero_dte_validation_readiness_rows(validation_payload)
    evaluation_result = evaluate_zero_dte_paper_fixture_rows(rows)
    evaluation_payload = build_zero_dte_evaluation_readiness_payload(evaluation_result)
    evaluation_rows = build_zero_dte_evaluation_readiness_rows(evaluation_payload)
    pipeline_result = build_zero_dte_paper_pipeline_result(rows)

    assert validation_result["rows_tested"] == 4
    assert validation_result["rows_invalid"] >= 1
    assert validation_payload["low_sample_size_does_not_hide_valid_results"] is True
    assert validation_payload["quality_not_automatically_labeled"] is True
    assert validation_payload["user_threshold_review_only"] is True
    assert validation_payload["live_connectors_enabled"] is False
    assert validation_payload["api_calls_enabled"] is False
    assert validation_payload["database_writes_enabled"] is False
    assert validation_payload["broker_execution_enabled"] is False
    assert validation_payload["real_trade_execution_enabled"] is False
    assert any(item["label"] == "rows_invalid" for item in validation_rows)

    assert evaluation_result["rows_tested"] == 4
    assert evaluation_result["rows_invalid"] >= 1
    assert evaluation_result["paper_result_counts"].get("paper_pending", 0) >= 1
    assert evaluation_result["paper_result_counts"].get("paper_win", 0) >= 1
    assert evaluation_result["paper_result_counts"].get("paper_loss", 0) >= 1
    assert evaluation_payload["low_sample_size_does_not_hide_valid_results"] is True
    assert evaluation_payload["quality_not_automatically_labeled"] is True
    assert evaluation_payload["user_threshold_review_only"] is True
    assert evaluation_payload["live_connectors_enabled"] is False
    assert evaluation_payload["api_calls_enabled"] is False
    assert evaluation_payload["database_writes_enabled"] is False
    assert evaluation_payload["broker_execution_enabled"] is False
    assert evaluation_payload["real_trade_execution_enabled"] is False
    assert any(item["label"] == "rows_pending" for item in evaluation_rows)

    assert pipeline_result["rows_tested"] == 4
    assert pipeline_result["rows_invalid"] >= 1
    assert pipeline_result["pipeline_ready_for_review"] is False
    assert pipeline_result["low_sample_size_does_not_hide_valid_results"] is True
    assert pipeline_result["quality_not_automatically_labeled"] is True
    assert pipeline_result["user_threshold_review_only"] is True
    assert pipeline_result["live_connectors_enabled"] is False
    assert pipeline_result["api_calls_enabled"] is False
    assert pipeline_result["database_writes_enabled"] is False
    assert pipeline_result["broker_execution_enabled"] is False
    assert pipeline_result["real_trade_execution_enabled"] is False
    assert "paper_pending" in pipeline_result["paper_result_counts"]
    assert "paper_win" in pipeline_result["paper_result_counts"]
    assert "paper_loss" in pipeline_result["paper_result_counts"]

    forbidden_connector_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
        "Execute Real Trade",
        "Send Broker Order",
        "Place Live Order",
    ]
    for needle in forbidden_connector_strings:
        assert needle not in app_text

    required_report_strings = [
        "Controlled 0DTE Paper Run Smoke Review",
        "local fixture-backed testing",
        "paper-only",
        "review-only",
        "no broker execution",
        "no real trade execution",
        "no API calls",
        "no database writes",
        "implementation reviewed in 10K8X",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"
