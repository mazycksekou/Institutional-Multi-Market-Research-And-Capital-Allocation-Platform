from __future__ import annotations

from pathlib import Path
import re

from automation_scheduler.zero_dte_fixture_template import (
    build_zero_dte_fixture_template_row,
    build_zero_dte_paper_pipeline_result,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8W_FULL_0DTE_PAPER_PIPELINE_UI.md"
APP = ROOT / "streamlit_app.py"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8w_full_0dte_paper_pipeline_ui() -> None:
    assert REPORT.is_file(), "Expected the 10K8W review report to exist."
    assert APP.is_file(), "Expected streamlit_app.py to remain present."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    app_text = read_text(APP)
    report_text = read_text(REPORT)

    assert "Full 0DTE paper pipeline UI" in app_text
    assert "show_zero_dte_paper_pipeline_preview" in app_text
    assert "build_zero_dte_paper_pipeline_result" in app_text
    assert "paper_pipeline_review_only" in app_text
    assert "pipeline_ready_for_review" in app_text
    assert "pipeline_steps" in app_text
    assert "validation_row_statuses" in app_text
    assert "evaluation_rows" in app_text
    assert "rows_tested" in app_text
    assert "rows_valid" in app_text
    assert "rows_invalid" in app_text
    assert "rows_warning" in app_text
    assert "rows_evaluated" in app_text
    assert "rows_pending" in app_text
    assert "total_paper_ev" in app_text
    assert "total_paper_stake_units" in app_text
    assert "total_paper_arbitrage_percentage" in app_text
    assert "average_paper_arbitrage_percentage" in app_text
    assert "backend_gate" in app_text
    assert "threshold_mode" in app_text
    assert "quality_label" in app_text
    assert "local fixture-backed testing" in app_text
    assert "paper-only" in app_text
    assert "readiness only" in app_text
    assert "review-only pipeline" in app_text
    assert "no broker execution" in app_text
    assert "no real trade execution" in app_text
    assert "no live connectors" in app_text
    assert "no API calls" in app_text
    assert "no database writes" in app_text
    assert "One 0DTE Options Trade" in app_text
    assert "0DTE is the primary active trading lane" in app_text

    branch_match = re.search(r"elif mode == \"One 0DTE Options Trade\":(.*?)(?:\n        elif |\n        else:)", app_text, re.S)
    assert branch_match, "Expected a dedicated One 0DTE Options Trade branch in streamlit_app.py."
    branch_text = branch_match.group(1)
    assert "show_zero_dte_paper_pipeline_preview()" in branch_text

    assert "st.file_uploader" not in app_text
    assert "pd.read_csv" not in app_text
    assert "pandas.read_csv" not in app_text

    forbidden_connector_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
        "Execute Real Trade",
        "Send Broker Order",
        "Place Live Order",
    ]
    for needle in forbidden_connector_strings:
        assert needle not in app_text

    pipeline_result = build_zero_dte_paper_pipeline_result([build_zero_dte_fixture_template_row()])
    assert pipeline_result["pipeline_ready_for_review"] in {True, False}
    assert pipeline_result["review_only"] is True
    assert pipeline_result["paper_only"] is True

    required_report_strings = [
        "Full 0DTE Paper Pipeline UI",
        "show_zero_dte_paper_pipeline_preview",
        "build_zero_dte_paper_pipeline_result",
        "paper_pipeline_review_only",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no broker execution",
        "no real trade execution",
        "implementation reviewed in 10K8W",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"
