from __future__ import annotations

from pathlib import Path


REPORT_PATH = Path("PHASE10K7A_FULL_SUITE_READINESS_OWNERSHIP_MAP.md")
STREAMLIT_APP_PATH = Path("streamlit_app.py")
DASHBOARD_DATA_PATH = Path("automation_scheduler/streamlit_dashboard_data.py")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k7a_report_exists_and_contains_required_strings() -> None:
    assert REPORT_PATH.exists(), "10K7A report is missing"

    report = read_text(REPORT_PATH)

    required_strings = [
        "Full Suite Readiness Ownership Map",
        "Executive Summary",
        "Sports Ownership",
        "0DTE Options Ownership",
        "Prediction Markets Ownership",
        "Data Warehouse Ownership",
        "Backtest Lab Ownership",
        "Model Diagnostics Ownership",
        "Arbitrage Lab Ownership",
        "Streamlit Shell Ownership",
        "Readiness Display Ownership",
        "Known Deferred Work",
        "Prediction Testing Boundary",
        "Connector Boundary",
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
        "unified research warehouse",
        "raw_option_chains",
        "raw_option_quotes",
        "features_0dte_options",
        "option_backtest_trades",
        "cross-sport odds snapshot",
        "runtime CSV migration deferred",
        "two-way arbitrage",
        "three-way arbitrage",
        "prediction-market yes/no arbitrage",
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_payload",
        "build_readiness_display_rows",
        "Controlled Navigation Shell",
        "no prediction testing",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no duplicate owner created",
        "implementation reviewed in 10K7A",
    ]

    for item in required_strings:
        assert item in report, f"Missing required report string: {item}"


def test_streamlit_app_keeps_shell_contract_strings_and_forbidden_actions_absent() -> None:
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
        assert item in text, f"Missing required streamlit_app.py string: {item}"

    forbidden_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
    ]

    for item in forbidden_strings:
        assert item not in text, f"Forbidden streamlit_app.py string present: {item}"


def test_dashboard_data_keeps_readiness_display_contract_helpers() -> None:
    text = read_text(DASHBOARD_DATA_PATH)

    required_strings = [
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "build_readiness_display_payload",
        "build_readiness_display_rows",
    ]

    for item in required_strings:
        assert item in text, f"Missing required dashboard data string: {item}"


def test_no_separate_frontend_page_files_were_added() -> None:
    page_candidates = [
        *Path(".").glob("pages/*.py"),
        *Path(".").glob("app/pages/*.py"),
        *Path(".").glob("frontend/*.py"),
        *Path(".").glob("frontend/pages/*.py"),
    ]
    assert not page_candidates, f"Unexpected separate frontend page files found: {page_candidates}"

