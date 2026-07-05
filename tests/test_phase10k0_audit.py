"""Verify that Phase 10K0 audit report exists and contains required headings."""

from pathlib import Path

import pytest


REPORT_PATH = Path(__file__).resolve().parents[1] / "PHASE10K0_INSTITUTIONAL_REPO_AUDIT_AND_0DTE_SPECIFICITY_MAP.md"


@pytest.fixture
def report_text() -> str:
    """Load the audit report Markdown content."""
    if not REPORT_PATH.exists():
        pytest.fail(f"Audit report not found at {REPORT_PATH}")
    return REPORT_PATH.read_text(encoding="utf-8")


class TestPhase10K0AuditReportExists:
    """Phase 10K0 must produce the audit report."""

    def test_report_file_exists(self) -> None:
        assert REPORT_PATH.exists(), f"Missing {REPORT_PATH}"

    def test_contains_institutional_repo_audit(self, report_text: str) -> None:
        assert "Institutional Repo Audit" in report_text

    def test_contains_0DTE_specificity_map(self, report_text: str) -> None:
        assert "0DTE Specificity Map" in report_text

    def test_contains_duplicate_register(self, report_text: str) -> None:
        assert "Duplicate / Overlapping Functionality Register" in report_text

    def test_contains_dead_unwired_register(self, report_text: str) -> None:
        assert "Dead / Unwired Functionality Register" in report_text

    def test_contains_warehouse_readiness_map(self, report_text: str) -> None:
        assert "Warehouse Readiness Map" in report_text

    def test_contains_arbitrage_readiness_map(self, report_text: str) -> None:
        assert "Arbitrage Readiness Map" in report_text

    def test_contains_no_duplicate_build_rules(self, report_text: str) -> None:
        assert "No-Duplicate Build Rules" in report_text

    def test_contains_sports_prediction_deferred(self, report_text: str) -> None:
        assert "sports prediction testing is deferred" in report_text

    def test_contains_0DTE_prediction_deferred(self, report_text: str) -> None:
        assert "0DTE prediction testing is deferred" in report_text

    def test_contains_do_not_implement_warehouse(self, report_text: str) -> None:
        assert "Do not implement the warehouse in this phase" in report_text

    def test_contains_do_not_implement_arbitrage(self, report_text: str) -> None:
        assert "Do not implement arbitrage in this phase" in report_text

    def test_contains_do_not_delete_duplicates(self, report_text: str) -> None:
        assert "Do not delete duplicates in this phase" in report_text

    def test_contains_file_by_file_change_map(self, report_text: str) -> None:
        assert "File-by-File Change Map" in report_text
