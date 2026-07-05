from __future__ import annotations

import importlib
from pathlib import Path


TARGET_DOCS = [
    "docs/archive/milestones/LEGACY_CLEANUP_SUMMARY.md",
    "docs/DOCUMENT_RETENTION_INDEX.md",
]


def test_execution_helper_final_delete_readiness_docs_and_modules() -> None:
    for relpath in TARGET_DOCS:
        assert Path(relpath).exists(), relpath

    canonical_settlement = importlib.import_module("src.brokerage.settlement")
    canonical_ledger = importlib.import_module("src.services.ledger_service")
    canonical_execution = importlib.import_module("src.services.execution_service")

    assert canonical_settlement.compare_settlement_rules([{"includes_overtime": True}, {"includes_overtime": True}])["material_mismatch"] is False
    assert canonical_ledger.STRATEGY_PERFORMANCE_SCHEMA_VERSION.endswith("strategy_performance_ledger.v1")
    assert canonical_execution.ExecutionDeskRejected.__module__ == "src.services.execution_service"

    summary_text = Path("docs/archive/milestones/LEGACY_CLEANUP_SUMMARY.md").read_text(encoding="utf-8")
    retention_text = Path("docs/DOCUMENT_RETENTION_INDEX.md").read_text(encoding="utf-8")
    assert "FINAL_EXECUTION_HELPER_IMPORT_SCAN_AFTER_10K8ZIO.md" in summary_text
    assert "FINAL_EXECUTION_HELPER_TEST_SCAN_AFTER_10K8ZIO.md" in summary_text
    assert "PHASE10K8ZIO_EXECUTION_HELPER_FINAL_DELETE_READINESS.md" in retention_text
    assert "LEGACY_CLEANUP_SUMMARY.md" in retention_text
    for relpath in [
        "src/brokerage/settlement.py",
        "src/services/settlement_service.py",
        "src/services/ledger_service.py",
        "src/services/execution_service.py",
    ]:
        assert Path(relpath).exists(), relpath


def test_execution_helper_no_delete_ready_queue() -> None:
    summary_text = Path("docs/archive/milestones/LEGACY_CLEANUP_SUMMARY.md").read_text(encoding="utf-8")
    assert "REMAINING_EXECUTION_HELPER_BLOCKERS_AFTER_10K8ZIP.md" in summary_text
    assert "Execution cleanup snapshots" in summary_text
