from __future__ import annotations

from pathlib import Path

from src.services.streamlit_dashboard_facade import validate_paper_only_fixture_rows


REPORT_PATH = Path("PHASE10K8C_PAPER_ONLY_FIXTURE_VALIDATION_HELPER.md")
STREAMLIT_APP_PATH = Path("streamlit_app.py")
DASHBOARD_DATA_PATH = Path("src/services/streamlit_dashboard_data.py")
BACKTEST_BUILDER_PATH = Path("src/backtesting/backtest_dataset_builder.py")
PHASE10K6K_TEST_PATH = Path("tests/test_phase10k6k_controlled_dashboard_shell_review.py")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_validate_paper_only_fixture_rows_accepts_valid_local_fixture_row() -> None:
    result = validate_paper_only_fixture_rows(
        [
            {
                "fixture_id": "fx-1",
                "sport_or_market": "Sports",
                "event_id": "evt-1",
                "prediction_target": "match_winner",
                "selection": "Team A",
                "model_probability": 0.62,
                "market_odds_american": -110,
                "implied_probability": 0.5238,
                "expected_value": 0.12,
                "stake_units": 1.5,
                "bankroll_snapshot": 1000.0,
                "result_label": "paper_win",
                "outcome_known": False,
                "source_type": "local_fixture",
                "execution_mode": "fixture_only",
            }
        ]
    )

    assert result["rows_tested"] == 1
    assert result["rows_valid"] == 1
    assert result["rows_invalid"] == 0
    assert result["prediction_testing_started"] is False
    assert result["live_connectors_enabled"] is False
    assert result["api_calls_enabled"] is False
    assert result["database_writes_enabled"] is False


def test_validate_paper_only_fixture_rows_flags_missing_fields() -> None:
    result = validate_paper_only_fixture_rows(
        [
            {
                "fixture_id": "fx-2",
                "sport_or_market": "Sports",
                "event_id": "evt-2",
                "prediction_target": "match_winner",
                "selection": "Team B",
                "model_probability": 0.4,
                "market_odds_american": 120,
                "implied_probability": 0.4545,
                "expected_value": -0.05,
                "stake_units": 1.0,
                "source_type": "local_fixture",
                "execution_mode": "paper_only",
            }
        ]
    )

    assert result["rows_tested"] == 1
    assert result["rows_valid"] == 0
    assert result["rows_invalid"] == 1
    assert result["missing_field_reasons"]
    assert "bankroll_snapshot" in result["missing_field_reasons"]
    assert "result_label" in result["missing_field_reasons"]
    assert "outcome_known" in result["missing_field_reasons"]


def test_backtest_dataset_builder_source_contains_required_strings() -> None:
    text = read_text(BACKTEST_BUILDER_PATH)

    required_strings = [
        "PAPER_ONLY_FIXTURE_REQUIRED_FIELDS",
        "PAPER_ONLY_FIXTURE_OPTIONAL_FIELDS",
        "validate_paper_only_fixture_rows",
        "paper_only",
        "fixture_only",
        "local_fixture",
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "missing_field_reasons",
        "warning_reasons",
        "prediction_testing_started",
        "live_connectors_enabled",
        "api_calls_enabled",
        "database_writes_enabled",
        "no prediction testing started in 10K8C",
        "no live connectors",
        "no API calls",
        "no database writes",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "user threshold review-only",
        "validity check only",
    ]

    for item in required_strings:
        assert item in text, f"Missing backtest_dataset_builder.py string: {item}"


def test_phase10k8c_report_exists_and_contains_required_strings() -> None:
    assert REPORT_PATH.exists(), "10K8C report is missing"

    report = read_text(REPORT_PATH)

    required_strings = [
        "Paper-Only Fixture Validation Helper",
        "automation_scheduler/backtest_dataset_builder.py",
        "PAPER_ONLY_FIXTURE_REQUIRED_FIELDS",
        "PAPER_ONLY_FIXTURE_OPTIONAL_FIELDS",
        "validate_paper_only_fixture_rows",
        "existing owner rule",
        "paper-only prediction testing",
        "local fixture-backed testing",
        "fixture_id",
        "sport_or_market",
        "event_id",
        "prediction_target",
        "selection",
        "model_probability",
        "market_odds_american",
        "implied_probability",
        "expected_value",
        "stake_units",
        "bankroll_snapshot",
        "result_label",
        "outcome_known",
        "source_type",
        "execution_mode",
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "missing_field_reasons",
        "warning_reasons",
        "no prediction testing started in 10K8C",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no duplicate owner created",
        "no temporary git shim",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "user threshold review-only",
        "validity check only",
        "implementation reviewed in 10K8C",
    ]

    for item in required_strings:
        assert item in report, f"Missing required report string: {item}"


def test_streamlit_app_keeps_shell_and_guardrail_strings() -> None:
    text = read_text(STREAMLIT_APP_PATH)

    required_strings = [
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

    for item in required_strings:
        assert item in text, f"Missing streamlit_app.py string: {item}"

    forbidden_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
    ]

    for item in forbidden_strings:
        assert item not in text, f"Forbidden streamlit_app.py string present: {item}"


def test_dashboard_data_keeps_readiness_display_helpers() -> None:
    text = read_text(DASHBOARD_DATA_PATH)

    required_strings = [
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "build_readiness_display_payload",
        "build_readiness_display_rows",
        "threshold_review_only",
        "validity_is_backend_gate",
        "low_sample_size_does_not_hide_valid_results",
        "quality_not_automatically_labeled",
    ]

    for item in required_strings:
        assert item in text, f"Missing readiness helper string: {item}"


def test_phase10k6k_guardrail_test_no_subprocess_git_checks() -> None:
    text = read_text(PHASE10K6K_TEST_PATH)

    forbidden_strings = [
        "subprocess",
        "git ls-files",
        "git status",
        "git shim",
    ]

    for item in forbidden_strings:
        assert item not in text, f"Forbidden string still present: {item}"


def test_no_separate_frontend_page_files_were_added() -> None:
    page_candidates = [
        *Path(".").glob("pages/*.py"),
        *Path(".").glob("app/pages/*.py"),
        *Path(".").glob("frontend/*.py"),
        *Path(".").glob("frontend/pages/*.py"),
    ]
    assert not page_candidates, f"Unexpected separate frontend page files found: {page_candidates}"

