from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZD_ORB_STRATEGY_RESEARCH_INTEGRATION_AUDIT.md"
APP = ROOT / "streamlit_app.py"
ORB_BACKTEST = ROOT / "orb_backtest.py"
ZERO_DTE_ORB = ROOT / "zero_dte_orb.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8zd_orb_strategy_research_integration_audit() -> None:
    assert REPORT.is_file(), "Expected the 10K8ZD report to exist."
    assert APP.is_file(), "Expected streamlit_app.py to remain present."
    assert not ORB_BACKTEST.exists(), "orb_backtest.py should remain absent in this branch."
    assert not ZERO_DTE_ORB.exists(), "zero_dte_orb.py should remain absent in this branch."

    report_text = read_text(REPORT)
    app_text = read_text(APP)

    required_report_strings = [
        "ORB Strategy Research Integration Audit",
        "orb_backtest.py",
        "zero_dte_orb.py",
        "existing owner rule",
        "Stocks / 0DTE",
        "underlying signal framework",
        "not a standalone 0DTE options strategy",
        "Total Trades",
        "Win Rate",
        "Loss Rate",
        "Avg Win",
        "Avg Loss",
        "Profit Factor",
        "Expectancy",
        "Average R",
        "Total R",
        "Starting Equity",
        "Ending Equity",
        "Net Profit",
        "Net Return %",
        "Max Drawdown",
        "Largest Winning Day",
        "Largest Losing Day",
        "Opening Range Width",
        "Breakout Distance",
        "VWAP Distance",
        "Volume Relative To OR Volume",
        "Time To Breakout",
        "Time In Trade",
        "Profitable Day %",
        "Profitable Week %",
        "Profitable Month %",
        "Parameter Sweep",
        "Top Configurations",
        "Saved Strategy Versions",
        "Profitable Period Rate is useful but not sufficient alone",
        "expectancy, profit factor, drawdown, trade count, and return",
        "no live trading",
        "no broker execution",
        "no API calls",
        "no database writes",
        "no guaranteed profit language",
        "no assured profit language",
        "implementation reviewed in 10K8ZD",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    assert "ORB Strategy Research" in app_text
    branch_match = re.search(r'elif mode == "One 0DTE Options Trade":(.*?)(?:\n        elif |\n        else:)', app_text, re.S)
    assert branch_match, "Expected the 0DTE branch to remain present in streamlit_app.py."
    branch_text = branch_match.group(1)
    assert "ORB Strategy Research" in branch_text
    assert "Stocks / 0DTE" in app_text
    assert "controlled research wording" not in app_text or "ORB Strategy Research" in app_text

    forbidden_connector_strings = [
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
    for needle in forbidden_connector_strings:
        assert needle not in app_text

    assert not any(ROOT.glob("pages/*.py")), "Unexpected frontend page files were added."
    assert not any(ROOT.glob("app/pages/*.py")), "Unexpected app/pages/*.py files were added."
    assert not any(ROOT.glob("frontend/*.py")), "Unexpected frontend/*.py files were added."
    assert not any(ROOT.glob("frontend/pages/*.py")), "Unexpected frontend/pages/*.py files were added."
