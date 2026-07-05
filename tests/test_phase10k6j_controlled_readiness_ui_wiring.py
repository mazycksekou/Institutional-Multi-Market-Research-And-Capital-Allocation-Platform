from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_APP = ROOT / "streamlit_app.py"
REPORT = ROOT / "PHASE10K6J_CONTROLLED_READINESS_UI_WIRING.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k6j_report_exists_and_contains_required_strings():
    assert REPORT.exists()
    report = read_text(REPORT)

    required_strings = [
        "Controlled Readiness UI Wiring",
        "streamlit_app.py",
        "automation_scheduler.streamlit_dashboard_data",
        "build_readiness_display_payload",
        "build_readiness_display_rows",
        "Sports",
        "0DTE Options",
        "Prediction Markets",
        "Data Warehouse",
        "Backtest Lab",
        "Model Diagnostics",
        "Arbitrage Lab",
        "shell-only",
        "readiness display preview",
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
        "implementation controlled in 10K6J",
    ]

    for needle in required_strings:
        assert needle in report


def test_streamlit_app_contains_controlled_readiness_wiring_and_guardrails():
    source = read_text(STREAMLIT_APP)

    for needle in [
        "build_readiness_display_payload",
        "build_readiness_display_rows",
        "Sports",
        "0DTE Options",
        "Prediction Markets",
        "Data Warehouse",
        "Backtest Lab",
        "Model Diagnostics",
        "Arbitrage Lab",
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
    ]:
        assert needle in source

    for needle in [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
    ]:
        assert needle not in source

    assert not any((ROOT / "pages").glob("*.py"))

