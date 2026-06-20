from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZFE1_UNIVERSAL_PRODUCT_LANGUAGE_ALIGNMENT.md"
README = ROOT / "README.md"
APP = ROOT / "streamlit_app.py"
DATA_HELPERS = ROOT / "automation_scheduler" / "streamlit_dashboard_data.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8zfe1_universal_product_language_alignment() -> None:
    assert REPORT.exists()

    report = read_text(REPORT)
    app_text = read_text(APP)
    helpers_text = read_text(DATA_HELPERS)
    readme_text = read_text(README)

    required_sections = [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Streamlit Risk Preset Language",
        "Scenario-Based Backtest Language",
        "Compatibility Handling",
        "Files Changed",
        "Tests Run",
        "Acceptance Results",
        "Next Phase Recommendation",
    ]
    for section in required_sections:
        assert f"## {section}" in report

    required_strings = [
        "10K8ZFE1",
        "Universal Product Language Alignment",
        "Aggressive paper only",
        "Aggressive",
        "risk preset controls sizing",
        "scenario mode controls missing-data handling",
        "Baseline / Imputed",
        "Strict / Complete Cases Only",
        "Stress / Adverse Missing-Data Fill",
        "no AI integration",
        "no ML training",
        "no backtest runner",
        "no broker execution",
        "no real trade execution",
        "no files deleted",
        "Proceed to 10K8ZFE Duplicate Code / Math / Metrics / Signal Evidence Scan",
    ]
    for item in required_strings:
        assert item in report

    assert "Aggressive paper only" not in app_text
    assert 'list(RISK_PRESETS.keys())' in app_text
    assert "None - no risk preset adjustment" in app_text
    assert "Risk preset controls sizing. Scenario mode controls missing-data handling for backtests." in app_text
    assert "Scenario modes:" in app_text

    risk_block_match = re.search(
        r"RISK_PRESETS: dict\[str, dict\[str, Any\]\] = \{.*?\n\}\n\nLEGACY_RISK_PRESET_ALIASES",
        helpers_text,
        re.S,
    )
    assert risk_block_match is not None
    risk_block = risk_block_match.group(0)
    assert "Aggressive paper only" not in risk_block
    assert '"Aggressive": {' in risk_block
    assert "Aggressive paper only" in helpers_text
    assert "Baseline / Imputed" in helpers_text
    assert "Strict / Complete Cases Only" in helpers_text
    assert "Stress / Adverse Missing-Data Fill" in helpers_text
    assert "Risk preset controls sizing; scenario mode controls missing-data handling." in helpers_text

    assert "risk preset controls sizing" in report
    assert "scenario mode controls missing-data handling" in report

    assert "Aggressive paper only" not in readme_text
    assert re.search(r"AKIA[0-9A-Z]{16}", report) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", report) is None
    assert "your_real_secret" not in report
    assert re.search(r"AKIA[0-9A-Z]{16}", readme_text) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", readme_text) is None
    assert "your_real_secret" not in readme_text
    assert re.search(r"AKIA[0-9A-Z]{16}", app_text) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", app_text) is None
    assert "your_real_secret" not in app_text
    assert re.search(r"AKIA[0-9A-Z]{16}", helpers_text) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", helpers_text) is None
    assert "your_real_secret" not in helpers_text

    assert not any(ROOT.glob("pages/*.py"))
    assert not any(ROOT.glob("app/pages/*.py"))
    assert not any(ROOT.glob("frontend/*.py"))
    assert not any(ROOT.glob("frontend/pages/*.py"))
