from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZF0_CANONICAL_RESEARCH_BACKTEST_WORKFLOW_MIGRATION_PLAN.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8zf0_canonical_research_backtest_workflow_migration_plan() -> None:
    assert REPORT.is_file(), "Expected the 10K8ZF0 migration report to exist."
    assert STREAMLIT_APP.is_file(), "Expected streamlit_app.py to exist."

    report_text = _read_text(REPORT)
    app_text = _read_text(STREAMLIT_APP)

    required_report_strings = [
        "Canonical Research/Backtest Workflow Migration Plan",
        "10K8ZF0",
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
        "compatibility aliases may remain temporarily",
        "public UI should not lead with paper, fake, synthetic demo, or testing room language",
        "internal safety flags may remain temporarily",
        "hidden compatibility/source-text blocks are transitional only",
        "local_research_backtest_mode",
        "research_backtest_validation",
        "research_backtest_evaluation",
        "research_backtest_pipeline",
        "research_backtest_fixture",
        "legacy paper names must migrate before controlled backtest runner UI",
        "migration must happen before footprint metric implementation",
        "migration must happen before 10K9 cleanup",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no guaranteed profit language",
        "no assured profit language",
        "implementation reviewed in 10K8ZF0",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    mapping_pairs = [
        "paper_only -> local_research_backtest_mode",
        "paper fixture -> research_backtest_fixture",
        "paper validation -> research_backtest_validation",
        "paper evaluation -> research_backtest_evaluation",
        "paper pipeline -> research_backtest_pipeline",
        "paper_result -> research_backtest_result",
        "paper_edge -> research_backtest_edge",
        "paper_ev -> research_backtest_ev",
        "paper_stake_units -> research_backtest_stake_units",
        "paper_arbitrage_percentage -> research_backtest_arbitrage_percentage",
        "fake demo -> remove from product UI",
        "synthetic rows are fake demo -> remove from product UI",
        "Testing Room -> Research Mode / Backtest",
        "readiness only -> Validation / Research Mode where public-facing",
        "review-only -> Research Mode where public-facing",
        "hidden legacy source-text blocks -> compatibility aliases only",
    ]
    for needle in mapping_pairs:
        assert needle in report_text, f"Missing mapping string: {needle}"

    assert "controlled backtest runner UI" in report_text
    assert "footprint metric implementation" in report_text
    assert "10K9 cleanup" in report_text

    required_app_strings = [
        "Data",
        "Validation",
        "Strategy Research",
        "Backtest",
        "Results / Metrics",
        "Research Mode",
        "Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.",
    ]
    for needle in required_app_strings:
        assert needle in app_text, f"Missing streamlit_app.py string: {needle}"

    forbidden_app_strings = [
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

    page_candidates = [
        *Path(".").glob("pages/*.py"),
        *Path(".").glob("app/pages/*.py"),
        *Path(".").glob("frontend/*.py"),
        *Path(".").glob("frontend/pages/*.py"),
    ]
    assert not page_candidates, f"Unexpected separate frontend page files found: {page_candidates}"
