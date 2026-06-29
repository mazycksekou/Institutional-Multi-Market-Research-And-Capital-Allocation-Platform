from __future__ import annotations

from pathlib import Path


REPORT_PATH = Path("PHASE10K7C_FULL_SUITE_READINESS_GATE_MATRIX.md")
STREAMLIT_APP_PATH = Path("streamlit_app.py")
DASHBOARD_DATA_PATH = Path("src/automation_scheduler_legacy/streamlit_dashboard_data.py")
PHASE10K6K_TEST_PATH = Path("tests/test_phase10k6k_controlled_dashboard_shell_review.py")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k7c_report_exists_and_contains_required_strings() -> None:
    assert REPORT_PATH.exists(), "10K7C report is missing"

    report = read_text(REPORT_PATH)

    required_strings = [
        "Full Suite Readiness Gate Matrix",
        "Executive Summary",
        "Readiness Gate Matrix",
        "Sports Gate",
        "0DTE Options Gate",
        "Prediction Markets Gate",
        "Data Warehouse Gate",
        "Backtest Lab Gate",
        "Model Diagnostics Gate",
        "Arbitrage Lab Gate",
        "Streamlit Shell Gate",
        "Readiness Display Gate",
        "10K8 Entry Criteria",
        "Blocking Conditions",
        "Prediction Testing Boundary",
        "Connector Boundary",
        "API Boundary",
        "Database Write Boundary",
        "Next Phase Recommendation",
        "Sports",
        "0DTE Options",
        "Prediction Markets",
        "Data Warehouse",
        "Backtest Lab",
        "Model Diagnostics",
        "Arbitrage Lab",
        "Streamlit shell",
        "readiness display",
        "10K8 entry criteria",
        "low backend gate",
        "validity check only",
        "user threshold review-only",
        "row counts",
        "rows tested",
        "rows valid",
        "rows invalid",
        "missing field reasons",
        "warning reasons",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "build_readiness_display_payload",
        "build_readiness_display_rows",
        "Controlled Navigation Shell",
        "readiness display preview",
        "no prediction testing",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no duplicate owner created",
        "no temporary git shim",
        "implementation reviewed in 10K7C",
    ]

    for item in required_strings:
        assert item in report, f"Missing required report string: {item}"


def test_streamlit_app_keeps_shell_and_readiness_strings() -> None:
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

