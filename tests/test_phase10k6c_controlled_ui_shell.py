from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_APP = ROOT / "streamlit_app.py"
REPORT = ROOT / "PHASE10K6C_CONTROLLED_UI_SHELL.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k6c_report_exists_and_contains_required_strings():
    assert REPORT.exists()
    report = read_text(REPORT)

    required_strings = [
        "Controlled UI Shell",
        "Current Streamlit main menu remains unchanged",
        "Feature Ablation Lab",
        "Bankroll Settings",
        "Instructions",
        "Future dashboard navigation is planned but not active",
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
        "implementation deferred beyond 10K6C",
    ]

    for needle in required_strings:
        assert needle in report


def test_streamlit_main_menu_remains_exact_and_instructions_shell_strings_exist():
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

    instructions_match = re.search(
        r'elif menu == "Instructions":(.*?)(?=\n\n# Phase 10H23C complete source-text compatibility contracts\.)',
        source,
        flags=re.S,
    )
    assert instructions_match, "Instructions branch not found"
    instructions_block = instructions_match.group(1)

    for needle in [
        "Controlled Dashboard Shell",
        "Future dashboard navigation is planned but not active in this phase.",
        "No prediction testing is enabled from this shell.",
        "Current menu remains unchanged.",
        "Controlled Navigation Shell",
        "shell-only",
        "readiness/navigation shell",
        "no live connectors",
    ]:
        assert needle in instructions_block

    for label in [
        "Sports",
        "0DTE Options",
        "Prediction Markets",
        "Data Warehouse",
        "Backtest Lab",
        "Model Diagnostics",
        "Arbitrage Lab",
    ]:
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
