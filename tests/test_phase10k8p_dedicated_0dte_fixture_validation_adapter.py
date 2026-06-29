from __future__ import annotations

from pathlib import Path

from src.services.streamlit_dashboard_facade import TECHNICAL_SIGNAL_FIELDS, TECHNICAL_SIGNAL_FIELDS_BY_MARKET
from src.automation_scheduler_legacy.zero_dte_fixture_template import ZERO_DTE_FIXTURE_VALIDATION_GUARDRAILS, ZERO_DTE_FIXTURE_VALIDATION_STATUS_VALUES, ZERO_DTE_MODE_KEY, ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS, ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS, ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS, ZERO_DTE_PAPER_TEMPLATE_GUARDRAILS, build_zero_dte_fixture_template_row, validate_zero_dte_fixture_rows


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8P_DEDICATED_0DTE_FIXTURE_VALIDATION_ADAPTER.md"
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


def test_phase10k8p_dedicated_0dte_fixture_validation_adapter() -> None:
    assert REPORT.is_file(), "Expected the 10K8P review report to exist."
    assert STREAMLIT_APP.is_file(), "Expected streamlit_app.py to exist."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    report_text = read_text(REPORT)
    streamlit_text = read_text(STREAMLIT_APP)
    legacy_text = read_text(LEGACY_PHASE_TEST)

    assert ZERO_DTE_MODE_KEY == "one_0dte_options_trade"
    assert ZERO_DTE_FIXTURE_VALIDATION_STATUS_VALUES == ("valid", "invalid", "warning")

    required_validation_guardrails = {
        "paper-only",
        "readiness only",
        "local fixture-backed testing",
        "validity check only",
        "user threshold review-only",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no broker execution",
        "no real trade execution",
    }
    assert required_validation_guardrails.issubset(set(ZERO_DTE_FIXTURE_VALIDATION_GUARDRAILS))

    valid_template_row = build_zero_dte_fixture_template_row()
    validation_result = validate_zero_dte_fixture_rows([valid_template_row])
    assert validation_result["execution_mode"] == "paper_only"
    assert validation_result["source_type"] == "local_fixture"
    assert validation_result["mode_key"] == ZERO_DTE_MODE_KEY
    assert validation_result["rows_tested"] == 1
    assert validation_result["rows_invalid"] == 0
    assert validation_result["prediction_testing_started"] is False
    assert validation_result["live_connectors_enabled"] is False
    assert validation_result["api_calls_enabled"] is False
    assert validation_result["database_writes_enabled"] is False
    assert validation_result["broker_execution_enabled"] is False
    assert validation_result["real_trade_execution_enabled"] is False
    assert validation_result["validity_check_only"] is True
    assert validation_result["user_threshold_review_only"] is True
    assert validation_result["quality_not_automatically_labeled"] is True
    assert validation_result["low_sample_size_does_not_hide_valid_results"] is True
    assert validation_result["required_fields"] == list(ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS)
    assert validation_result["optional_fields"] == list(ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS)
    assert validation_result["review_output_fields"] == list(ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS)
    assert validation_result["guardrails"] == list(ZERO_DTE_FIXTURE_VALIDATION_GUARDRAILS)
    assert "ev" not in validation_result
    assert "expected_value" not in validation_result
    assert "edge" not in validation_result
    assert "kelly_fraction" not in validation_result
    assert "paper_arbitrage_percentage" not in validation_result

    statuses = [status["status"] for status in validation_result["row_statuses"]]
    assert statuses[0] in {"valid", "warning"}
    if statuses[0] == "warning":
        assert validation_result["rows_warning"] == 1
    else:
        assert validation_result["rows_warning"] == 0
    status_entry = validation_result["row_statuses"][0]
    assert set(status_entry.keys()) == {
        "row_index",
        "status",
        "missing_required_fields",
        "missing_optional_fields",
        "warning_reasons",
    }
    assert status_entry["row_index"] == 0
    assert status_entry["missing_required_fields"] == []
    assert isinstance(status_entry["missing_optional_fields"], list)
    assert isinstance(status_entry["warning_reasons"], list)
    assert validation_result["rows_valid"] + validation_result["rows_invalid"] + validation_result["rows_warning"] == 1

    complete_row = build_zero_dte_fixture_template_row().copy()
    for field in ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS:
        complete_row[field] = "present"
    complete_result = validate_zero_dte_fixture_rows([complete_row])
    assert complete_result["rows_invalid"] == 0
    assert complete_result["rows_warning"] == 0
    assert complete_result["row_statuses"][0]["status"] == "valid"

    for missing_field in list(ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS[:3]):
        row = build_zero_dte_fixture_template_row().copy()
        row.pop(missing_field, None)
        result = validate_zero_dte_fixture_rows([row])
        assert result["rows_invalid"] == 1
        assert result["row_statuses"][0]["status"] == "invalid"
        assert missing_field in result["row_statuses"][0]["missing_required_fields"]

    for field, replacement in [
        (ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS[0], None),
        (ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS[1], ""),
    ]:
        row = build_zero_dte_fixture_template_row().copy()
        row[field] = replacement
        result = validate_zero_dte_fixture_rows([row])
        assert result["rows_invalid"] == 1
        assert result["row_statuses"][0]["status"] == "invalid"
        assert field in result["row_statuses"][0]["missing_required_fields"]

    optional_missing_row = build_zero_dte_fixture_template_row().copy()
    for field in ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS[:5]:
        optional_missing_row.pop(field, None)
    optional_result = validate_zero_dte_fixture_rows([optional_missing_row])
    assert optional_result["rows_invalid"] == 0
    assert optional_result["row_statuses"][0]["status"] == "warning"
    assert optional_result["row_statuses"][0]["missing_optional_fields"]
    assert optional_result["row_statuses"][0]["warning_reasons"]

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

    assert ZERO_DTE_PAPER_TEMPLATE_GUARDRAILS

    required_report_strings = [
        "Dedicated 0DTE Fixture Validation Adapter",
        "automation_scheduler/zero_dte_fixture_template.py",
        "streamlit_app.py",
        "quant_engine.py",
        "existing owner rule",
        "One 0DTE Options Trade",
        "0DTE is the primary active trading lane",
        "validate_zero_dte_fixture_rows",
        "ZERO_DTE_FIXTURE_VALIDATION_GUARDRAILS",
        "ZERO_DTE_FIXTURE_VALIDATION_STATUS_VALUES",
        "ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS",
        "ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS",
        "ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS",
        "paper_arbitrage_percentage",
        "paper arbitrage percentage within tested timeframe",
        "paper arbitrage outputs are review-only",
        "validation does not calculate EV",
        "validation does not calculate edge",
        "validation does not calculate Kelly",
        "validation does not calculate arbitrage",
        "validation does not calculate paper_arbitrage_percentage",
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
        "implementation reviewed in 10K8P",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    required_streamlit_strings = [
        "Dedicated 0DTE fixture validation adapter",
        "validate_zero_dte_fixture_rows",
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
