from pathlib import Path

from src.services.streamlit_dashboard_facade import validate_paper_only_fixture_rows
from src.automation_scheduler_legacy.streamlit_dashboard_data import build_paper_only_fixture_readiness_payload, build_paper_only_fixture_readiness_rows


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "PHASE10K8D_PAPER_ONLY_FIXTURE_READINESS_PAYLOAD_ADAPTER.md"
STREAMLIT_APP_PATH = REPO_ROOT / "streamlit_app.py"
DASHBOARD_DATA_PATH = REPO_ROOT / "src" / "automation_scheduler_legacy" / "streamlit_dashboard_data.py"
PHASE_10K6K_TEST_PATH = (
    REPO_ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_paper_only_fixture_adapter_round_trip():
    valid_row = {
        "fixture_id": "fixture-1",
        "sport_or_market": "Sports",
        "event_id": "event-1",
        "prediction_target": "home_team",
        "selection": "home_team",
        "model_probability": 0.61,
        "market_odds_american": -120,
        "implied_probability": 0.545,
        "expected_value": 0.11,
        "stake_units": 1.5,
        "bankroll_snapshot": 1000,
        "result_label": "win",
        "outcome_known": True,
        "source_type": "local_fixture",
        "execution_mode": "paper_only",
    }

    validation_result = validate_paper_only_fixture_rows([valid_row])
    assert validation_result["rows_tested"] == 1
    assert validation_result["rows_valid"] == 1
    assert validation_result["rows_invalid"] == 0
    assert validation_result["prediction_testing_started"] is False
    assert validation_result["live_connectors_enabled"] is False
    assert validation_result["api_calls_enabled"] is False
    assert validation_result["database_writes_enabled"] is False

    payload = build_paper_only_fixture_readiness_payload(validation_result)
    assert payload["rows_tested"] == 1
    assert payload["rows_valid"] == 1
    assert payload["rows_invalid"] == 0
    assert payload["validation_status"] == "valid"
    assert payload["prediction_testing_started"] is False
    assert payload["live_connectors_enabled"] is False
    assert payload["api_calls_enabled"] is False
    assert payload["database_writes_enabled"] is False

    rows = build_paper_only_fixture_readiness_rows(validation_result)
    assert rows
    assert all({"label", "value", "policy_note"} <= set(row) for row in rows)
    assert any(row["label"] == "Source type" for row in rows)
    assert any(row["label"] == "Execution mode" for row in rows)

    invalid_row = {
        "fixture_id": "fixture-2",
        "sport_or_market": "Sports",
        "event_id": "event-2",
        "prediction_target": "away_team",
        "model_probability": 0.42,
        "market_odds_american": 135,
        "implied_probability": 0.425,
        "expected_value": -0.03,
        "stake_units": 1.0,
        "bankroll_snapshot": 900,
        "result_label": "loss",
        "outcome_known": False,
        "source_type": "local_fixture",
        "execution_mode": "fixture_only",
    }
    invalid_validation = validate_paper_only_fixture_rows([invalid_row])
    invalid_payload = build_paper_only_fixture_readiness_payload(invalid_validation)
    assert invalid_payload["validation_status"] == "needs_review"
    assert invalid_payload["rows_invalid"] > 0
    assert invalid_payload["missing_field_reasons"]


def test_phase_report_and_source_guardrails():
    report_text = _read_text(REPORT_PATH)
    dashboard_text = _read_text(DASHBOARD_DATA_PATH)
    streamlit_text = _read_text(STREAMLIT_APP_PATH)
    phase_10k6k_text = _read_text(PHASE_10K6K_TEST_PATH)

    required_report_strings = [
        "Paper-Only Fixture Readiness Payload Adapter",
        "automation_scheduler/streamlit_dashboard_data.py",
        "automation_scheduler/backtest_dataset_builder.py",
        "validate_paper_only_fixture_rows",
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
        "source_type",
        "execution_mode",
        "prediction_testing_started",
        "live_connectors_enabled",
        "api_calls_enabled",
        "database_writes_enabled",
        "no prediction testing started in 10K8D",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no duplicate owner created",
        "no temporary git shim",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "user threshold review-only",
        "validity check only",
        "implementation reviewed in 10K8D",
    ]
    for text in required_report_strings:
        assert text in report_text, text

    required_dashboard_strings = [
        "build_paper_only_fixture_readiness_payload",
        "build_paper_only_fixture_readiness_rows",
        "build_readiness_display_payload",
        "build_readiness_display_rows",
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "missing_field_reasons",
        "warning_reasons",
        "prediction_testing_started",
        "live_connectors_enabled",
        "api_calls_enabled",
        "database_writes_enabled",
        "no prediction testing started in 10K8D",
        "no live connectors",
        "no API calls",
        "no database writes",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "user threshold review-only",
        "validity check only",
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


