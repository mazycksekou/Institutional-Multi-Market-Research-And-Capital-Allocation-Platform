from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZF0A_FROZEN_TEST_CONTRACT_RESET.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"
STREAMLIT_DATA_TEST = ROOT / "tests" / "test_streamlit_dashboard_data.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def test_phase10k8zf0a_frozen_test_contract_reset() -> None:
    assert REPORT.is_file(), "Expected the 10K8ZF0A report to exist."
    assert STREAMLIT_APP.is_file(), "Expected streamlit_app.py to exist."
    assert STREAMLIT_DATA_TEST.is_file(), "Expected the dashboard data test file to exist."

    report_text = read_text(REPORT)
    app_text = read_text(STREAMLIT_APP)
    data_test_text = read_text(STREAMLIT_DATA_TEST)

    required_report_strings = [
        "10K8ZF0A",
        "Frozen Test Contract Reset",
        "new product contract supersedes obsolete synthetic/fake-demo public-copy assertions",
        "Synthetic rows are fake demo data and must not be used as model evidence removed from streamlit_app.py",
        "Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.",
        "Data",
        "Validation",
        "Strategy Research",
        "Backtest",
        "Results / Metrics",
        "Later: Live Model Testing",
        "one canonical workflow",
        "no separate paper workflow",
        "paper is an execution-mode flag, not a product architecture",
        "backtest path must be the actual future implementation path",
        "internal compatibility aliases may remain temporarily",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no guaranteed profit language",
        "no assured profit language",
        "implementation reviewed in 10K8ZF0A",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    required_app_strings = [
        "Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.",
        "Data",
        "Validation",
        "Strategy Research",
        "Backtest",
        "Results / Metrics",
        "Research Mode",
        "Local Data",
    ]
    for needle in required_app_strings:
        assert needle in app_text, f"Missing streamlit_app.py string: {needle}"

    forbidden_app_strings = [
        "Synthetic rows are fake demo data and must not be used as model evidence.",
        "fake demo",
        "Paper Testing Room",
        "Testing Room",
        "paper evaluation adapter",
        "paper validation adapter",
        "one 0DTE paper pipeline",
        "guaranteed profit",
        "assured profit",
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
        "Execute Real Trade",
        "Send Broker Order",
        "Place Live Order",
    ]
    for needle in forbidden_app_strings:
        assert needle not in app_text, f"Forbidden streamlit_app.py string present: {needle}"

    assert "Research/backtest mode only. No broker orders, live connectors, " in data_test_text
    assert "API calls, or database writes." in data_test_text
    assert "Synthetic rows are fake demo data and must not be used as model evidence." not in data_test_text

    for legacy_text in [
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls",
        "no database writes",
    ]:
        assert legacy_text in data_test_text

    page_candidates = [
        *Path(".").glob("pages/*.py"),
        *Path(".").glob("app/pages/*.py"),
        *Path(".").glob("frontend/*.py"),
        *Path(".").glob("frontend/pages/*.py"),
    ]
    assert not page_candidates, f"Unexpected separate frontend page files found: {page_candidates}"
