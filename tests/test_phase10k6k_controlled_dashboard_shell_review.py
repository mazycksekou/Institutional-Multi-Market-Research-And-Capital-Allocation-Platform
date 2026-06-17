from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K6K_CONTROLLED_DASHBOARD_SHELL_REVIEW.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"
READINESS_DATA = ROOT / "automation_scheduler" / "streamlit_dashboard_data.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k6k_controlled_dashboard_shell_review():
    assert REPORT.is_file(), "Expected the 10K6K review report to exist."
    assert STREAMLIT_APP.is_file(), "Expected streamlit_app.py to exist."
    assert READINESS_DATA.is_file(), "Expected readiness helper source to exist."

    report_text = read_text(REPORT)
    streamlit_text = read_text(STREAMLIT_APP)
    readiness_text = read_text(READINESS_DATA)

    required_report_strings = [
        "Controlled Dashboard Shell Review",
        "streamlit_app.py",
        "automation_scheduler/streamlit_dashboard_data.py",
        "Controlled Navigation Shell",
        "readiness display preview",
        "build_readiness_display_payload",
        "build_readiness_display_rows",
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "Sports",
        "0DTE Options",
        "Prediction Markets",
        "Data Warehouse",
        "Backtest Lab",
        "Model Diagnostics",
        "Arbitrage Lab",
        "Feature Ablation Lab",
        "Bankroll Settings",
        "Instructions",
        "shell-only",
        "no prediction testing",
        "no live connectors",
        "no API calls",
        "no database writes",
        "user threshold review-only",
        "validity check only",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "no frontend page files added",
        "connector guardrails remain active",
        "implementation reviewed in 10K6K",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    required_streamlit_strings = [
        "Controlled Navigation Shell",
        "readiness display preview",
        "shell-only",
        "no prediction testing",
        "no live connectors",
        "no API calls",
        "no database writes",
        "user threshold review-only",
        "validity check only",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
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
        "build_readiness_display_payload",
        "build_readiness_display_rows",
    ]
    for needle in required_streamlit_strings:
        assert needle in streamlit_text, f"Missing streamlit_app.py string: {needle}"

    required_readiness_strings = [
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "build_readiness_display_payload",
        "build_readiness_display_rows",
        "threshold_review_only",
        "validity_is_backend_gate",
        "low_sample_size_does_not_hide_valid_results",
        "quality_not_automatically_labeled",
    ]
    for needle in required_readiness_strings:
        assert needle in readiness_text, f"Missing readiness helper string: {needle}"

    forbidden_streamlit_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
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

    assert "no frontend page files added" in report_text
    assert "connector guardrails remain active" in report_text
    assert "implementation reviewed in 10K6K" in report_text
