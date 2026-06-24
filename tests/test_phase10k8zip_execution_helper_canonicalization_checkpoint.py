from __future__ import annotations

import importlib
from pathlib import Path


def test_execution_helper_checkpoint_docs_and_architecture() -> None:
    for relpath in [
        "PHASE10K8ZIP_EXECUTION_HELPER_CANONICALIZATION_CHECKPOINT.md",
        "POST_EXECUTION_HELPER_ARCHITECTURE_MAP_AFTER_10K8ZIP.md",
        "REMAINING_EXECUTION_HELPER_BLOCKERS_AFTER_10K8ZIP.md",
        "NEXT_EXECUTION_HELPER_DELETION_PLAN_AFTER_10K8ZIP.md",
    ]:
        assert Path(relpath).exists(), relpath

    settlement = importlib.import_module("src.brokerage.settlement")
    settlement_service = importlib.import_module("src.services.settlement_service")
    ledger_service = importlib.import_module("src.services.ledger_service")
    execution_service = importlib.import_module("src.services.execution_service")

    assert settlement.compare_settlement_rules([{"void_on_push": False}, {"void_on_push": False}])["material_mismatch"] is False
    assert settlement_service.build_outcome_completion_report(pending_rows=[], imported_rows=[], read_only_records=[], use_kalshi_snapshot=False)["completion_candidates_count"] == 0
    assert ledger_service.load_audit_records(base_data_dir="data")["provider_write"] is False
    assert execution_service.build_broker_quality_report()["provider_write"] is False

    checkpoint = Path("PHASE10K8ZIP_EXECUTION_HELPER_CANONICALIZATION_CHECKPOINT.md").read_text(encoding="utf-8")
    assert "Settlement canonicalization is complete" in checkpoint
    assert "Ledger canonicalization is complete" in checkpoint
    assert "Strategy / execution helper canonicalization is complete" in checkpoint
    assert "Live trading remains disabled" in checkpoint
