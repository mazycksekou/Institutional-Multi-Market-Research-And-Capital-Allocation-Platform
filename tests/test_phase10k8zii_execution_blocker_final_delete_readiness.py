from __future__ import annotations

import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "docs" / "archive" / "milestones" / "LEGACY_CLEANUP_SUMMARY.md"
RETENTION_INDEX = ROOT / "docs" / "DOCUMENT_RETENTION_INDEX.md"


def test_execution_blocker_final_delete_readiness_docs_state_no_delete_ready() -> None:
    text = "\n".join(
        [
            SUMMARY.read_text(encoding="utf-8"),
            RETENTION_INDEX.read_text(encoding="utf-8"),
        ]
    )
    for phrase in [
        "PHASE10K8ZII_EXECUTION_BLOCKER_FINAL_DELETE_READINESS.md",
        "FINAL_EXECUTION_BLOCKER_IMPORT_SCAN_AFTER_10K8ZII.md",
        "Execution cleanup snapshots",
        "KEEP ARCHIVE",
    ]:
        assert phrase in text


def test_execution_blocker_final_delete_readiness_modules_import_safe() -> None:
    for module_name in [
        "src.brokerage",
        "src.brokerage.orders",
        "src.brokerage.execution",
        "src.brokerage.ledger",
        "src.brokerage.readiness",
        "src.services.decision_engine",
        "src.brokerage.settlement",
        "src.services.settlement_service",
        "src.services.ledger_service",
        "src.services.execution_service",
        "src.brokerage.paper_trade_ledger",
        "src.brokerage.paper_decision_ledger",
        "bet_decision_engine",
        "bet_log",
    ]:
        assert importlib.import_module(module_name)
