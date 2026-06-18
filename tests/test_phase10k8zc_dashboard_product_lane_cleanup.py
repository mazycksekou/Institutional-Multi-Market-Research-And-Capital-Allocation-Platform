from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZC_DASHBOARD_PRODUCT_LANE_CLEANUP.md"
APP = ROOT / "streamlit_app.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8zc_dashboard_product_lane_cleanup() -> None:
    assert REPORT.is_file(), "Expected the 10K8ZC report to exist."
    assert APP.is_file(), "Expected streamlit_app.py to remain present."

    report_text = read_text(REPORT)
    app_text = read_text(APP)

    required_report_strings = [
        "Dashboard Product Lane Cleanup",
        "streamlit_app.py",
        "PRODUCT_MARKET_LANES",
        "LEGACY_INTERNAL_MODE_ALIASES",
        "internal_model_mode_for_product_lane",
        "Sports",
        "Stocks / 0DTE",
        "Predictions",
        "Testing / Readiness Lab",
        "Internal Research Lab",
        "Kalshi",
        "Polymarket",
        "ORB Strategy Research",
        "local fixture-backed testing",
        "paper-only",
        "readiness only",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls",
        "no database writes",
        "implementation reviewed in 10K8ZC",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    assert "PRODUCT_MARKET_LANES" in app_text
    lane_match = re.search(r'PRODUCT_MARKET_LANES = \((.*?)\)', app_text, re.S)
    assert lane_match, "Expected PRODUCT_MARKET_LANES to be defined."
    lane_body = lane_match.group(1)
    lane_labels = re.findall(r'"([^"]+)"', lane_body)
    assert lane_labels == ["Sports", "Stocks / 0DTE", "Predictions"], lane_labels
    assert "One Sport" not in lane_body
    assert "One Stock Market" not in lane_body
    assert "One Crypto Market" not in lane_body
    assert "One Prediction Market" not in lane_body
    assert "One 0DTE Options Trade" not in lane_body

    required_app_strings = [
        "Sports",
        "Stocks / 0DTE",
        "Predictions",
        "Testing / Readiness Lab",
        "Internal Research Lab",
        "internal_model_mode_for_product_lane",
        "one_sport",
        "one_0dte_options_trade",
        "one_prediction_market",
        "Kalshi",
        "Polymarket",
        "ORB Strategy Research",
        "local fixture-backed testing",
        "paper-only",
        "readiness only",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls",
        "no database writes",
    ]
    for needle in required_app_strings:
        assert needle in app_text, f"Missing streamlit_app.py string: {needle}"

    assert "Controlled synthetic fixture rows are internal-only" in app_text

    forbidden_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
        "Execute Real Trade",
        "Send Broker Order",
        "Place Live Order",
        "guaranteed profit",
        "assured profit",
    ]
    for needle in forbidden_strings:
        assert needle not in app_text

    assert not any(ROOT.glob("pages/*.py")), "Unexpected pages/*.py files were added."
    assert not any(ROOT.glob("app/pages/*.py")), "Unexpected app/pages/*.py files were added."
    assert not any(ROOT.glob("frontend/*.py")), "Unexpected frontend/*.py files were added."
    assert not any(ROOT.glob("frontend/pages/*.py")), "Unexpected frontend/pages/*.py files were added."
