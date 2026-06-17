from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_APP = ROOT / "streamlit_app.py"
REPORT = ROOT / "PHASE10K6B_DASHBOARD_NAVIGATION_PLAN_CONTRACT.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k6b_report_exists_and_contains_required_strings():
    assert REPORT.exists()
    report = read_text(REPORT)

    required_strings = [
        "Dashboard Navigation Plan Contract",
        "Current Streamlit main menu remains unchanged",
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
        "Settings / Instructions",
        "readiness gate display contract",
        "low backend gate",
        "validity check only",
        "user threshold review-only",
        "row counts",
        "missing field reasons",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "no prediction testing",
        "no live connectors",
        "no frontend pages added",
        "implementation deferred to 10K6C",
    ]

    for needle in required_strings:
        assert needle in report


def test_streamlit_main_menu_remains_exact_and_future_labels_are_not_added_to_menu():
    source = read_text(STREAMLIT_APP)

    assert "Feature Ablation Lab" in source
    assert "Bankroll Settings" in source
    assert "Instructions" in source

    menu_match = re.search(
        r'st\.sidebar\.radio\(\s*"Main Menu",\s*\[(.*?)\],\s*\)',
        source,
        flags=re.S,
    )
    assert menu_match, "Main Menu radio block not found"

    menu_block = menu_match.group(1)
    menu_labels = re.findall(r'"([^"]+)"', menu_block)
    assert menu_labels == ["Feature Ablation Lab", "Bankroll Settings", "Instructions"]

    forbidden_labels = [
        "Sports",
        "0DTE Options",
        "Prediction Markets",
        "Data Warehouse",
        "Backtest Lab",
        "Model Diagnostics",
        "Arbitrage Lab",
    ]
    for label in forbidden_labels:
        assert label not in menu_block


def test_streamlit_app_does_not_contain_forbidden_connector_or_action_strings():
    source = read_text(STREAMLIT_APP)

    forbidden_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
    ]
    for needle in forbidden_strings:
        assert needle not in source


def test_report_says_no_frontend_pages_added_and_no_prediction_testing():
    report = read_text(REPORT)
    assert "No frontend pages added." in report
    assert "no prediction testing is permitted in this phase." in report
    assert "implementation deferred to 10K6C." in report
