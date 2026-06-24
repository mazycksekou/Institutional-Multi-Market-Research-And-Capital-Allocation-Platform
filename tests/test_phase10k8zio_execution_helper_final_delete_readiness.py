from __future__ import annotations

import importlib
from pathlib import Path


TARGET_DOCS = [
    "PHASE10K8ZIO_EXECUTION_HELPER_FINAL_DELETE_READINESS.md",
    "FINAL_EXECUTION_HELPER_IMPORT_SCAN_AFTER_10K8ZIO.md",
    "FINAL_EXECUTION_HELPER_TEST_SCAN_AFTER_10K8ZIO.md",
    "FINAL_EXECUTION_HELPER_DELETE_DECISION_AFTER_10K8ZIO.md",
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

    doc_text = Path("PHASE10K8ZIO_EXECUTION_HELPER_FINAL_DELETE_READINESS.md").read_text(encoding="utf-8")
    assert "No scheduler execution helper is classified `DELETE_READY_AFTER_PROOF`" in doc_text
    for relpath in [
        "src/brokerage/settlement.py",
        "src/services/settlement_service.py",
        "src/services/ledger_service.py",
        "src/services/execution_service.py",
    ]:
        assert Path(relpath).exists(), relpath


def test_execution_helper_no_delete_ready_queue() -> None:
    doc_text = Path("FINAL_EXECUTION_HELPER_DELETE_DECISION_AFTER_10K8ZIO.md").read_text(encoding="utf-8")
    assert "No file in the execution-helper batch is approved for deletion" in doc_text
    assert "src.brokerage.settlement" in doc_text
    assert "src.services.execution_service" in doc_text
