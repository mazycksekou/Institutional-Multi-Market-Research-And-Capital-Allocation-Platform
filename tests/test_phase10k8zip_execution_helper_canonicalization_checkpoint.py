from __future__ import annotations

import importlib
from pathlib import Path


def test_execution_helper_checkpoint_docs_and_architecture() -> None:
    summary_path = Path("docs/archive/milestones/LEGACY_CLEANUP_SUMMARY.md")
    retention_path = Path("docs/DOCUMENT_RETENTION_INDEX.md")
    assert summary_path.exists()
    assert retention_path.exists()

    settlement = importlib.import_module("src.brokerage.settlement")
    settlement_service = importlib.import_module("src.services.settlement_service")
    ledger_service = importlib.import_module("src.services.ledger_service")
    execution_service = importlib.import_module("src.services.execution_service")

    assert settlement.compare_settlement_rules([{"void_on_push": False}, {"void_on_push": False}])["material_mismatch"] is False
    assert settlement_service.build_outcome_completion_report(pending_rows=[], imported_rows=[], read_only_records=[], use_kalshi_snapshot=False)["completion_candidates_count"] == 0
    assert ledger_service.load_audit_records(base_data_dir="data")["provider_write"] is False
    assert execution_service.build_broker_quality_report()["provider_write"] is False

    summary = summary_path.read_text(encoding="utf-8")
    retention = retention_path.read_text(encoding="utf-8")
    assert "PHASE10K8ZIP_EXECUTION_HELPER_CANONICALIZATION_CHECKPOINT.md" in retention
    assert "REMAINING_EXECUTION_HELPER_BLOCKERS_AFTER_10K8ZIP.md" in summary
    assert "Execution cleanup snapshots" in summary
