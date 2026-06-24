from __future__ import annotations

import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZII_EXECUTION_BLOCKER_FINAL_DELETE_READINESS.md",
    ROOT / "FINAL_EXECUTION_BLOCKER_IMPORT_SCAN_AFTER_10K8ZII.md",
    ROOT / "FINAL_EXECUTION_BLOCKER_TEST_SCAN_AFTER_10K8ZII.md",
    ROOT / "FINAL_EXECUTION_BLOCKER_DELETE_DECISION_AFTER_10K8ZII.md",
]


def test_execution_blocker_final_delete_readiness_docs_state_no_delete_ready() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "DELETE_READY_AFTER_PROOF: none",
        "ACTIVE_RUNTIME_DEPENDENCY",
        "ACTIVE_TEST_DEPENDENCY",
        "UNSAFE_TO_TOUCH",
        "Canonical execution path remains intact.",
        "Live trading remains disabled.",
        "Broker account creation remains disabled.",
        "No deletion occurred during the proof step.",
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
        "automation_scheduler.execution_gatekeeper",
        "automation_scheduler.execution_authorization",
        "automation_scheduler.paper_trade_ledger",
        "automation_scheduler.paper_decision_ledger",
        "bet_decision_engine",
        "bet_log",
    ]:
        assert importlib.import_module(module_name)

