from __future__ import annotations

from pathlib import Path

from automation_scheduler.streamlit_dashboard_data import (
    build_zero_dte_evaluation_readiness_payload,
    build_zero_dte_evaluation_readiness_rows,
)
from automation_scheduler.zero_dte_fixture_template import (
    build_zero_dte_fixture_template_row,
    evaluate_zero_dte_paper_fixture_rows,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8T_DEDICATED_0DTE_EVALUATION_READINESS_PAYLOAD.md"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8t_dedicated_0dte_evaluation_readiness_payload() -> None:
    assert REPORT.is_file(), "Expected the 10K8T review report to exist."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    report_text = read_text(REPORT)

    template_row = build_zero_dte_fixture_template_row()
    evaluation_result = evaluate_zero_dte_paper_fixture_rows([template_row])
    payload = build_zero_dte_evaluation_readiness_payload(evaluation_result)
    rows = build_zero_dte_evaluation_readiness_rows(payload)

    required_payload_keys = {
        "mode_key",
        "source_type",
        "execution_mode",
        "rows_tested",
        "rows_evaluated",
        "rows_invalid",
        "rows_pending",
        "paper_result_counts",
        "total_paper_ev",
        "total_paper_stake_units",
        "total_paper_arbitrage_percentage",
        "average_paper_arbitrage_percentage",
        "evaluation_rows",
        "guardrails",
        "review_only",
        "paper_only",
        "user_threshold_review_only",
        "quality_not_automatically_labeled",
        "low_sample_size_does_not_hide_valid_results",
        "prediction_testing_started",
        "live_connectors_enabled",
        "api_calls_enabled",
        "database_writes_enabled",
        "broker_execution_enabled",
        "real_trade_execution_enabled",
        "backend_gate",
        "threshold_mode",
        "quality_label",
        "readiness_summary",
    }
    assert required_payload_keys.issubset(payload.keys())
    assert payload["backend_gate"] == "paper_evaluation_review_only"
    assert payload["threshold_mode"] == "user_threshold_review_only"
    assert payload["quality_label"] == "not_automatically_labeled"
    assert payload["review_only"] is True
    assert payload["paper_only"] is True
    assert payload["user_threshold_review_only"] is True
    assert payload["quality_not_automatically_labeled"] is True
    assert payload["low_sample_size_does_not_hide_valid_results"] is True
    assert payload["prediction_testing_started"] is False
    assert payload["live_connectors_enabled"] is False
    assert payload["api_calls_enabled"] is False
    assert payload["database_writes_enabled"] is False
    assert payload["broker_execution_enabled"] is False
    assert payload["real_trade_execution_enabled"] is False
    assert set(payload["readiness_summary"].keys()) == {
        "rows_tested",
        "rows_evaluated",
        "rows_invalid",
        "rows_pending",
        "review_only",
        "paper_only",
    }

    assert isinstance(rows, list)
    assert rows
    assert all(set(item.keys()) == {"label", "value", "status", "detail"} for item in rows)

    row_labels = {item["label"] for item in rows}
    expected_row_labels = {
        "mode_key",
        "execution_mode",
        "source_type",
        "rows_tested",
        "rows_evaluated",
        "rows_invalid",
        "rows_pending",
        "total_paper_ev",
        "total_paper_stake_units",
        "total_paper_arbitrage_percentage",
        "average_paper_arbitrage_percentage",
        "backend_gate",
        "threshold_mode",
        "quality_label",
        "prediction_testing_started",
        "live_connectors_enabled",
        "api_calls_enabled",
        "database_writes_enabled",
        "broker_execution_enabled",
        "real_trade_execution_enabled",
        "review_only",
        "paper_only",
        "user_threshold_review_only",
        "quality_not_automatically_labeled",
        "low_sample_size_does_not_hide_valid_results",
    }
    assert expected_row_labels.issubset(row_labels)

    invalid_row = build_zero_dte_fixture_template_row().copy()
    invalid_row.pop("fixture_id", None)
    invalid_payload = build_zero_dte_evaluation_readiness_payload(
        evaluate_zero_dte_paper_fixture_rows([invalid_row])
    )
    invalid_rows = build_zero_dte_evaluation_readiness_rows(invalid_payload)
    assert any(item["label"] == "rows_invalid" and item["status"] == "blocked" for item in invalid_rows)

    pending_payload = build_zero_dte_evaluation_readiness_payload(evaluate_zero_dte_paper_fixture_rows([template_row]))
    pending_rows = build_zero_dte_evaluation_readiness_rows(pending_payload)
    assert any(item["label"] == "rows_pending" and item["status"] == "warning" for item in pending_rows)

    required_report_strings = [
        "Dedicated 0DTE Evaluation Readiness Payload",
        "automation_scheduler/streamlit_dashboard_data.py",
        "automation_scheduler/zero_dte_fixture_template.py",
        "streamlit_app.py",
        "quant_engine.py",
        "build_zero_dte_evaluation_readiness_payload",
        "build_zero_dte_evaluation_readiness_rows",
        "paper_evaluation_review_only",
        "user_threshold_review_only",
        "quality_not_automatically_labeled",
        "readiness rows do not calculate EV",
        "readiness rows do not calculate edge",
        "readiness rows do not calculate Kelly",
        "readiness rows do not calculate arbitrage",
        "readiness rows do not calculate paper_arbitrage_percentage",
        "paper-only prediction testing",
        "local fixture-backed testing",
        "readiness only",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no broker execution",
        "no real trade execution",
        "implementation reviewed in 10K8T",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

