from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_APP = ROOT / "streamlit_app.py"
REPORT = ROOT / "PHASE10K6I_CONTROLLED_NAVIGATION_SHELL.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k6i_report_exists_and_contains_required_strings():
    assert REPORT.exists()
    report = read_text(REPORT)

    required_strings = [
        "Controlled Navigation Shell",
        "earlier future-label guardrails were temporary",
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
        "readiness/navigation shell",
        "no prediction testing",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no frontend page files added",
        "old tests updated to allow controlled navigation labels",
        "connector guardrails remain active",
        "implementation controlled in 10K6I",
    ]

    for needle in required_strings:
        assert needle in report


def test_streamlit_app_contains_controlled_navigation_shell_labels_and_guardrails():
    source = read_text(STREAMLIT_APP)

    for needle in [
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
        "shell-only",
        "no prediction testing",
        "no live connectors",
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


