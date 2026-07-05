from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_APP = ROOT / "streamlit_app.py"
REPORT = ROOT / "PHASE10K6D_READINESS_GATE_DISPLAY_CONTRACT.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k6d_report_exists_and_contains_required_strings():
    assert REPORT.exists()
    report = read_text(REPORT)

    required_strings = [
        "Readiness Gate Display Contract",
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
        "Sports",
        "0DTE Options",
        "Prediction Markets",
        "Data Warehouse",
        "Backtest Lab",
        "Model Diagnostics",
        "Arbitrage Lab",
        "no prediction testing",
        "no live connectors",
        "no frontend pages added",
        "Current Streamlit main menu remains unchanged",
        "Feature Ablation Lab",
        "Bankroll Settings",
        "Instructions",
        "implementation deferred beyond 10K6D",
    ]

    for needle in required_strings:
        assert needle in report


def test_report_contains_full_future_readiness_display_field_list():
    report = read_text(REPORT)

    expected_fields = [
        "market name",
        "data source name",
        "validation status",
        "row counts",
        "rows tested",
        "rows valid",
        "rows invalid",
        "missing field reasons",
        "warning reasons",
        "user threshold value",
        "whether user threshold was met",
        "clear text that threshold is review-only",
        "clear text that validity is the backend gate",
        "clear text that low sample size does not hide valid results",
        "clear text that quality is not automatically labeled",
    ]

    for field in expected_fields:
        assert field in report


def test_streamlit_main_menu_remains_exact_and_forbidden_connector_strings_absent():
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

    forbidden_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
    ]
    for needle in forbidden_strings:
        assert needle not in source


def test_report_says_no_prediction_testing_no_live_connectors_no_frontend_pages_and_deferred():
    report = read_text(REPORT)
    assert "no prediction testing" in report
    assert "no live connectors" in report
    assert "no frontend pages added" in report
    assert "implementation deferred beyond 10K6D" in report
