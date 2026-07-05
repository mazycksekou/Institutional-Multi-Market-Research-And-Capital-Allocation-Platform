from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZF3_PRODUCT_UI_LANGUAGE_FINALIZATION.md"
APP = ROOT / "streamlit_app.py"

UPDATED_TESTS = [
    ROOT / "tests" / "test_phase10k8u_dedicated_0dte_evaluation_ui.py",
    ROOT / "tests" / "test_phase10k8v_full_0dte_paper_pipeline_adapter.py",
    ROOT / "tests" / "test_phase10k8w_full_0dte_paper_pipeline_ui.py",
    ROOT / "tests" / "test_phase10k8m_strict_model_field_baseline_by_market_and_sport.py",
    ROOT / "tests" / "test_phase10k8n_controlled_field_catalog_ui_review.py",
    ROOT / "tests" / "test_phase10k8o_dedicated_0dte_paper_fixture_template.py",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8zf3_product_ui_language_finalization() -> None:
    assert REPORT.is_file(), "Expected the 10K8ZF3 report to exist."
    assert APP.is_file(), "Expected streamlit_app.py to remain present."

    report_text = read_text(REPORT)
    app_text = read_text(APP)
    updated_test_text = "\n".join(read_text(path) for path in UPDATED_TESTS if path.is_file())

    required_report_strings = [
        "10K8ZF3",
        "Product UI Language Finalization",
        "hidden legacy source-text blocks retired",
        "obsolete fake/paper/testing-room product copy removed",
        "canonical research_backtest wording is the visible product surface",
        "paper names may remain only as backward-compatible helper aliases",
        "no separate paper workflow",
        "one canonical workflow",
        "Data",
        "Validation",
        "Strategy Research",
        "Backtest",
        "Results / Metrics",
        "Later: Live Model Testing",
        "Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.",
        "pre-backtest cleanup must happen before controlled data loader or backtest runner",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no guaranteed profit language",
        "no assured profit language",
        "implementation reviewed in 10K8ZF3",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    required_app_strings = [
        "Data",
        "Validation",
        "Strategy Research",
        "Backtest",
        "Results / Metrics",
        "Research Mode",
        "Local Data",
        "Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.",
        "build_zero_dte_research_backtest_pipeline_result",
        "build_zero_dte_research_backtest_evaluation_result",
        "research_backtest_edge",
        "research_backtest_ev",
        "research_backtest_stake_units",
        "research_backtest_result",
        "research_backtest_arbitrage_percentage",
        "total_research_backtest_ev",
        "total_research_backtest_stake_units",
        "total_research_backtest_arbitrage_percentage",
        "average_research_backtest_arbitrage_percentage",
        "research_backtest_evaluation_review_only",
        "research_backtest_pipeline_review_only",
    ]
    for needle in required_app_strings:
        assert needle in app_text, f"Missing app string: {needle}"

    forbidden_app_strings = [
        "Synthetic rows are fake demo data and must not be used as model evidence.",
        "Synthetic Line Movement Sandbox is fake demo line movement data and is not model evidence.",
        "Test One Sport is a paper test flow.",
        "Paper Testing Room",
        "Testing Room",
        "fake demo",
        "one 0DTE paper pipeline",
        "paper evaluation adapter",
        "paper validation adapter",
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
        assert needle not in app_text, f"Unexpected legacy token in streamlit_app.py: {needle}"

    canonical_markers = [
        "research_backtest",
        "Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.",
        "Data",
        "Validation",
        "Strategy Research",
        "Backtest",
        "Results / Metrics",
        "Research Mode",
        "Local Data",
    ]
    for path in UPDATED_TESTS:
        text = read_text(path)
        assert any(marker in text for marker in canonical_markers), (
            f"Expected canonical product wording in updated test: {path.name}"
        )

    assert "Synthetic rows are fake demo data and must not be used as model evidence." not in updated_test_text
    assert "Paper Testing Room" not in updated_test_text
    assert "Testing Room" not in updated_test_text
    assert "fake demo" not in updated_test_text
    assert "one 0DTE paper pipeline" not in updated_test_text
    assert "paper evaluation adapter" not in updated_test_text
    assert "paper validation adapter" not in updated_test_text

    for forbidden in [
        "guaranteed profit",
        "assured profit",
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
        "Execute Real Trade",
        "Send Broker Order",
        "Place Live Order",
    ]:
        assert forbidden not in app_text

    frontend_globs = [
        "pages/*.py",
        "app/pages/*.py",
        "frontend/*.py",
        "frontend/pages/*.py",
    ]
    for pattern in frontend_globs:
        assert not list(ROOT.glob(pattern)), f"Unexpected frontend page files matching {pattern}"
