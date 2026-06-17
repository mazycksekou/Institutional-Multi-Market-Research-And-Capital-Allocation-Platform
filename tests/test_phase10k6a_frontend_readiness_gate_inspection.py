from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_APP = ROOT / "streamlit_app.py"
DASHBOARD_DATA = ROOT / "automation_scheduler" / "streamlit_dashboard_data.py"
REPORT = ROOT / "PHASE10K6A_FRONTEND_READINESS_GATE_INSPECTION.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k6a_report_exists_and_contains_required_strings():
    assert REPORT.exists()
    report = read_text(REPORT)

    required_strings = [
        "Frontend Readiness Gate Inspection",
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
    ]

    for needle in required_strings:
        assert needle in report


def test_streamlit_main_menu_remains_exact_and_no_forbidden_top_level_labels_were_added():
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


def test_dashboard_data_file_exists_and_is_text_inspectable():
    assert DASHBOARD_DATA.exists()
    text = read_text(DASHBOARD_DATA)
    assert len(text) > 0
    assert "Pure Python helper layer for the local operator dashboard." in text
