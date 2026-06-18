from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "PHASE10K8L_CONTROLLED_MULTI_MARKET_TEST_MODE_UI.md"
STREAMLIT_APP_PATH = REPO_ROOT / "streamlit_app.py"
PHASE_10K6K_TEST_PATH = (
    REPO_ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase_report_and_source_guardrails():
    report_text = _read_text(REPORT_PATH)
    streamlit_text = _read_text(STREAMLIT_APP_PATH)
    phase_10k6k_text = _read_text(PHASE_10K6K_TEST_PATH)

    required_report_strings = [
        "Controlled Multi-Market Test Mode UI",
        "streamlit_app.py",
        "existing owner rule",
        "One Sport",
        "One Stock Market",
        "One Prediction Market",
        "All Ready",
        "Sports field groups",
        "Stock Market field groups",
        "Prediction Market field groups",
        "quote_fields",
        "line_data_fields",
        "price_action_fields",
        "volume_liquidity_fields",
        "options_chain_fields",
        "earnings_calendar_fields",
        "macro_context_fields",
        "sector_context_fields",
        "fundamentals_fields",
        "technical_indicator_fields",
        "contract_fields",
        "orderbook_fields",
        "price_probability_fields",
        "settlement_fields",
        "event_context_fields",
        "resolution_criteria_fields",
        "arbitrage_fields",
        "paper-only prediction testing",
        "local fixture-backed testing",
        "readiness only",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no duplicate owner created",
        "no temporary git shim",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "user threshold review-only",
        "validity check only",
        "implementation reviewed in 10K8L",
    ]
    for text in required_report_strings:
        assert text in report_text, text

    required_streamlit_strings = [
        "Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.",
        "One Sport",
        "One Stock Market",
        "One Prediction Market",
        "All Ready",
        "Sports field groups",
        "Stock Market field groups",
        "Prediction Market field groups",
        "quote_fields",
        "line_data_fields",
        "price_action_fields",
        "volume_liquidity_fields",
        "options_chain_fields",
        "earnings_calendar_fields",
        "macro_context_fields",
        "sector_context_fields",
        "fundamentals_fields",
        "technical_indicator_fields",
        "contract_fields",
        "orderbook_fields",
        "price_probability_fields",
        "settlement_fields",
        "event_context_fields",
        "resolution_criteria_fields",
        "arbitrage_fields",
        "Data",
        "Validation",
        "Strategy Research",
        "Backtest",
        "Results / Metrics",
        "Research Mode",
        "Local Data",
        "paper-only",
        "readiness only",
        "no live connectors",
        "no API calls",
        "no database writes",
        "user threshold review-only",
        "validity check only",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
    ]
    for text in required_streamlit_strings:
        assert text in streamlit_text, text

    required_existing_strings = [
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
        "Controlled Navigation Shell",
        "readiness display preview",
    ]
    for text in required_existing_strings:
        assert text in streamlit_text, text

    forbidden_connector_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
    ]
    for text in forbidden_connector_strings:
        assert text not in streamlit_text, text

    assert "subprocess" not in phase_10k6k_text
    assert "git ls-files" not in phase_10k6k_text
    assert "git status" not in phase_10k6k_text
    assert "git shim" not in phase_10k6k_text

    assert not list(REPO_ROOT.glob("pages/*.py"))
    assert not list(REPO_ROOT.glob("app/pages/*.py"))
    assert not list(REPO_ROOT.glob("frontend/*.py"))
    assert not list(REPO_ROOT.glob("frontend/pages/*.py"))
