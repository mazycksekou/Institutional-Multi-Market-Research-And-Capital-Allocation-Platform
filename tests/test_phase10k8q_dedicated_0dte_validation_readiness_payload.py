from __future__ import annotations

from pathlib import Path

from src.automation_scheduler_legacy.streamlit_dashboard_data import build_zero_dte_validation_readiness_payload, build_zero_dte_validation_readiness_rows
from src.services.streamlit_dashboard_facade import TECHNICAL_SIGNAL_FIELDS, TECHNICAL_SIGNAL_FIELDS_BY_MARKET
from src.automation_scheduler_legacy.zero_dte_fixture_template import ZERO_DTE_MODE_KEY, build_zero_dte_fixture_template_row, validate_zero_dte_fixture_rows


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8Q_DEDICATED_0DTE_VALIDATION_READINESS_PAYLOAD.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flatten_market_fields() -> set[str]:
    flattened: set[str] = set()
    for market_spec in TECHNICAL_SIGNAL_FIELDS_BY_MARKET.values():
        flattened.update(market_spec.get("required", []))
        flattened.update(market_spec.get("optional", []))
    return flattened


def test_phase10k8q_dedicated_0dte_validation_readiness_payload() -> None:
    assert REPORT.is_file(), "Expected the 10K8Q review report to exist."
    assert STREAMLIT_APP.is_file(), "Expected streamlit_app.py to exist."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    report_text = read_text(REPORT)
    streamlit_text = read_text(STREAMLIT_APP)
    legacy_text = read_text(LEGACY_PHASE_TEST)

    validation_result = validate_zero_dte_fixture_rows([build_zero_dte_fixture_template_row()])
    payload = build_zero_dte_validation_readiness_payload(validation_result)
    rows = build_zero_dte_validation_readiness_rows(payload)

    required_payload_keys = {
        "mode_key",
        "source_type",
        "execution_mode",
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "rows_warning",
        "missing_field_reasons",
        "warning_reasons",
        "row_statuses",
        "required_fields",
        "optional_fields",
        "review_output_fields",
        "paper_arbitrage_output_fields",
        "guardrails",
        "backend_gate",
        "threshold_mode",
        "quality_label",
        "readiness_summary",
    }
    assert required_payload_keys.issubset(payload.keys())
    assert payload["mode_key"] == ZERO_DTE_MODE_KEY
    assert payload["execution_mode"] == "paper_only"
    assert payload["source_type"] == "local_fixture"
    assert payload["backend_gate"] == "validity_check_only"
    assert payload["threshold_mode"] == "user_threshold_review_only"
    assert payload["quality_label"] == "not_automatically_labeled"
    assert payload["prediction_testing_started"] is False
    assert payload["live_connectors_enabled"] is False
    assert payload["api_calls_enabled"] is False
    assert payload["database_writes_enabled"] is False
    assert payload["broker_execution_enabled"] is False
    assert payload["real_trade_execution_enabled"] is False
    assert payload["validity_check_only"] is True
    assert payload["user_threshold_review_only"] is True
    assert payload["quality_not_automatically_labeled"] is True
    assert payload["low_sample_size_does_not_hide_valid_results"] is True
    assert set(payload["readiness_summary"].keys()) == {
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "rows_warning",
        "validity_check_only",
        "low_sample_size_does_not_hide_valid_results",
    }

    row_labels = {row["label"] for row in rows}
    expected_row_labels = {
        "mode_key",
        "execution_mode",
        "source_type",
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "rows_warning",
        "backend_gate",
        "threshold_mode",
        "quality_label",
        "prediction_testing_started",
        "live_connectors_enabled",
        "api_calls_enabled",
        "database_writes_enabled",
        "broker_execution_enabled",
        "real_trade_execution_enabled",
        "validity_check_only",
        "user_threshold_review_only",
        "quality_not_automatically_labeled",
        "low_sample_size_does_not_hide_valid_results",
    }
    assert expected_row_labels.issubset(row_labels)
    for row in rows:
        assert set(row.keys()) == {"label", "value", "status", "detail"}

    warning_validation_result = validate_zero_dte_fixture_rows([build_zero_dte_fixture_template_row()])
    warning_payload = build_zero_dte_validation_readiness_payload(warning_validation_result)
    warning_rows = build_zero_dte_validation_readiness_rows(warning_payload)
    assert warning_payload["rows_warning"] >= 0
    assert any(row["label"] == "rows_warning" and row["status"] == "warning" for row in warning_rows)

    invalid_row = build_zero_dte_fixture_template_row().copy()
    invalid_row.pop("fixture_id", None)
    invalid_payload = build_zero_dte_validation_readiness_payload(validate_zero_dte_fixture_rows([invalid_row]))
    invalid_rows = build_zero_dte_validation_readiness_rows(invalid_payload)
    assert any(row["label"] == "rows_invalid" and row["status"] == "blocked" for row in invalid_rows)

    valid_row = build_zero_dte_fixture_template_row().copy()
    for field in valid_row.keys():
        if valid_row[field] is None:
            valid_row[field] = "present"
    valid_payload = build_zero_dte_validation_readiness_payload(validate_zero_dte_fixture_rows([valid_row]))
    valid_rows = build_zero_dte_validation_readiness_rows(valid_payload)
    assert any(row["label"] == "rows_invalid" and row["status"] == "ok" for row in valid_rows)

    assert "ev" not in payload
    assert "expected_value" not in payload
    assert "edge" not in payload
    assert "kelly_fraction" not in payload
    assert "paper_arbitrage_percentage" not in payload

    required_signal_fields = {
        "ev",
        "expected_value",
        "edge",
        "arbitrage",
        "kelly",
        "fair_odds",
        "implied_probability",
        "bankroll",
        "confidence",
        "no_bet",
        "no-bet",
        "paper_arbitrage_percentage",
    }
    assert "paper_arbitrage_percentage" not in TECHNICAL_SIGNAL_FIELDS
    assert not required_signal_fields.intersection(TECHNICAL_SIGNAL_FIELDS)
    assert not required_signal_fields.intersection(flatten_market_fields())

    required_report_strings = [
        "Dedicated 0DTE Validation Readiness Payload",
        "automation_scheduler/streamlit_dashboard_data.py",
        "automation_scheduler/zero_dte_fixture_template.py",
        "streamlit_app.py",
        "quant_engine.py",
        "existing owner rule",
        "One 0DTE Options Trade",
        "0DTE is the primary active trading lane",
        "validate_zero_dte_fixture_rows",
        "build_zero_dte_validation_readiness_payload",
        "build_zero_dte_validation_readiness_rows",
        "backend_gate",
        "validity_check_only",
        "user_threshold_review_only",
        "quality_not_automatically_labeled",
        "low_sample_size_does_not_hide_valid_results",
        "paper_arbitrage_percentage",
        "paper arbitrage percentage within tested timeframe",
        "paper arbitrage outputs are review-only",
        "readiness rows do not calculate EV",
        "readiness rows do not calculate edge",
        "readiness rows do not calculate Kelly",
        "readiness rows do not calculate arbitrage",
        "readiness rows do not calculate paper_arbitrage_percentage",
        "EV stays in quant_engine.py",
        "edge stays in quant_engine.py",
        "Kelly stays in quant_engine.py",
        "arbitrage stays out of TECHNICAL_SIGNAL_FIELDS",
        "technical signals are not universal math outputs",
        "validity check only",
        "user threshold review-only",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "paper-only prediction testing",
        "local fixture-backed testing",
        "readiness only",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no broker execution",
        "no real trade execution",
        "no duplicate owner created",
        "no temporary git shim",
        "implementation reviewed in 10K8Q",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    required_streamlit_strings = [
        "Dedicated 0DTE validation readiness payload",
        "build_zero_dte_validation_readiness_payload",
        "build_zero_dte_validation_readiness_rows",
        "validity check only",
        "user threshold review-only",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "local fixture-backed testing",
        "paper-only",
        "readiness only",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls",
        "no database writes",
    ]
    for needle in required_streamlit_strings:
        assert needle in streamlit_text, f"Missing streamlit_app.py string: {needle}"

    forbidden_streamlit_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
        "Execute Real Trade",
        "Send Broker Order",
        "Place Live Order",
    ]
    for needle in forbidden_streamlit_strings:
        assert needle not in streamlit_text, f"Forbidden string unexpectedly present: {needle}"

    page_candidates = [
        *Path(".").glob("pages/*.py"),
        *Path(".").glob("app/pages/*.py"),
        *Path(".").glob("frontend/*.py"),
        *Path(".").glob("frontend/pages/*.py"),
    ]
    assert not page_candidates, f"Unexpected separate frontend page files found: {page_candidates}"

    for needle in ["subprocess", "git ls-files", "git status", "git shim"]:
        assert needle not in legacy_text
