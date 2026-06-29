from pathlib import Path

import src.automation_scheduler_legacy.zero_dte_fixture_template as zt
import src.automation_scheduler_legacy.streamlit_dashboard_data as sd


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZF2_PRODUCTION_SYMBOL_MIGRATION.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8zf2_production_symbol_migration() -> None:
    assert REPORT.is_file(), "Expected the 10K8ZF2 report to exist."

    report_text = _read_text(REPORT)
    app_text = _read_text(STREAMLIT_APP)

    required_report_strings = [
        "10K8ZF2",
        "Production Symbol Migration",
        "canonical research_backtest names are the primary workflow surface",
        "paper names remain temporarily as backward-compatible aliases",
        "no separate paper workflow",
        "one canonical workflow",
        "backtest path must be the actual future implementation path",
        "ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_REQUIRED_FIELDS",
        "ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_OPTIONAL_FIELDS",
        "build_zero_dte_research_backtest_fixture_template_row",
        "validate_zero_dte_research_backtest_fixture_rows",
        "build_zero_dte_research_backtest_validation_result",
        "build_zero_dte_research_backtest_evaluation_result",
        "build_zero_dte_research_backtest_pipeline_result",
        "build_research_backtest_fixture_readiness_payload",
        "build_research_backtest_fixture_readiness_rows",
        "build_research_backtest_evaluation_readiness_payload",
        "build_research_backtest_evaluation_readiness_rows",
        "Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no guaranteed profit language",
        "no assured profit language",
        "implementation reviewed in 10K8ZF2",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    assert zt.ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_REQUIRED_FIELDS == zt.ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS
    assert zt.ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_OPTIONAL_FIELDS == zt.ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS
    assert (
        zt.build_zero_dte_research_backtest_fixture_template_row()
        == zt.build_zero_dte_fixture_template_row()
    )

    rows = [zt.build_zero_dte_fixture_template_row()]
    assert (
        zt.build_zero_dte_research_backtest_pipeline_result(rows)
        == zt.build_zero_dte_paper_pipeline_result(rows)
    )

    assert zt.build_zero_dte_research_backtest_fixture_template_row is zt.build_zero_dte_fixture_template_row
    assert zt.validate_zero_dte_research_backtest_fixture_rows is zt.validate_zero_dte_fixture_rows
    assert (
        zt.build_zero_dte_research_backtest_validation_result
        is zt.validate_zero_dte_fixture_rows
    )
    assert (
        zt.build_zero_dte_research_backtest_evaluation_result
        is zt.evaluate_zero_dte_paper_fixture_rows
    )
    assert zt.build_zero_dte_research_backtest_pipeline_result is zt.build_zero_dte_paper_pipeline_result

    assert sd.build_research_backtest_fixture_readiness_payload is sd.build_paper_only_fixture_readiness_payload
    assert sd.build_research_backtest_fixture_readiness_rows is sd.build_paper_only_fixture_readiness_rows
    assert sd.build_research_backtest_evaluation_readiness_payload is sd.build_paper_only_evaluation_readiness_payload
    assert sd.build_research_backtest_evaluation_readiness_rows is sd.build_paper_only_evaluation_readiness_rows

    minimal_validation = {"rows_tested": 1, "rows_valid": 1, "rows_invalid": 0, "missing_field_reasons": [], "warning_reasons": []}
    assert sd.build_research_backtest_fixture_readiness_payload(minimal_validation) == sd.build_paper_only_fixture_readiness_payload(minimal_validation)

    minimal_evaluation = {
        "rows_tested": 1,
        "rows_valid": 1,
        "rows_invalid": 0,
        "missing_field_reasons": [],
        "warning_reasons": [],
        "evaluations": [],
    }
    assert sd.build_research_backtest_evaluation_readiness_payload(minimal_evaluation) == sd.build_paper_only_evaluation_readiness_payload(minimal_evaluation)

    for text in [
        "Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.",
        "Data",
        "Validation",
        "Strategy Research",
        "Backtest",
        "Results / Metrics",
        "Research Mode",
    ]:
        assert text in app_text

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

    page_candidates = [
        *Path(".").glob("pages/*.py"),
        *Path(".").glob("app/pages/*.py"),
        *Path(".").glob("frontend/*.py"),
        *Path(".").glob("frontend/pages/*.py"),
    ]
    assert not page_candidates, f"Unexpected separate frontend page files found: {page_candidates}"
