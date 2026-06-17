from __future__ import annotations

from pathlib import Path


REPORT_PATH = Path("PHASE10K8B_PAPER_ONLY_FIXTURE_TESTING_CONTRACT.md")
STREAMLIT_APP_PATH = Path("streamlit_app.py")
DASHBOARD_DATA_PATH = Path("automation_scheduler/streamlit_dashboard_data.py")
PHASE10K6K_TEST_PATH = Path("tests/test_phase10k6k_controlled_dashboard_shell_review.py")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8b_report_exists_and_contains_required_strings() -> None:
    assert REPORT_PATH.exists(), "10K8B report is missing"

    report = read_text(REPORT_PATH)

    required_strings = [
        "Paper-Only Fixture Testing Contract",
        "existing owner rule",
        "paper-only prediction testing",
        "local fixture-backed testing",
        "source-text guardrails",
        "readiness display evidence",
        "no live money",
        "no production execution",
        "Sports",
        "0DTE Options",
        "Prediction Markets",
        "Backtest Lab",
        "Model Diagnostics",
        "Arbitrage Lab",
        "Data Warehouse",
        "Streamlit shell",
        "readiness display",
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
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "missing_field_reasons",
        "warning_reasons",
        "source_type",
        "execution_mode",
        "quant_engine.py",
        "risk_engine.py",
        "src/core/opportunity_scanner.py",
        "src/core/math_utils.py",
        "automation_scheduler/backtest_dataset_builder.py",
        "automation_scheduler/backtesting_engine.py",
        "automation_scheduler/model_performance_report.py",
        "automation_scheduler/experiment_report_exporter.py",
        "automation_scheduler/experiment_history_store.py",
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "build_readiness_display_payload",
        "build_readiness_display_rows",
        "Controlled Navigation Shell",
        "readiness display preview",
        "no prediction testing started in 10K8B",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no duplicate owner created",
        "no temporary git shim",
        "implementation reviewed in 10K8B",
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

