from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIA_EXECUTION_SCHEDULER_AUDIT.md",
    ROOT / "EXECUTION_SCHEDULER_FILE_INVENTORY_AFTER_10K8ZIA.md",
    ROOT / "EXECUTION_SCHEDULER_OWNERSHIP_MAP_AFTER_10K8ZIA.md",
    ROOT / "EXECUTION_SCHEDULER_DELETE_CANDIDATE_QUEUE_AFTER_10K8ZIA.md",
]


def test_execution_audit_docs_exist_and_classify_candidates() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary",
        "MIGRATE_TO_SRC_BROKERAGE",
        "MIGRATE_TO_SRC_SERVICES",
        "MIGRATE_TO_SRC_CORE",
        "COMPATIBILITY_WRAPPER_ONLY",
        "DELETE_READY_AFTER_PROOF",
        "ACTIVE_RUNTIME_DEPENDENCY",
        "ACTIVE_TEST_DEPENDENCY",
        "UNSAFE_TO_TOUCH",
        "main.py is not a deletion candidate",
        "streamlit_app.py is not a deletion candidate",
        "DELETE_READY_AFTER_PROOF: none",
    ]:
        assert phrase in text


def test_execution_audit_modules_import_safely() -> None:
    for module_name in [
        "automation_scheduler.execution_gatekeeper",
        "automation_scheduler.execution_authorization",
        "src.brokerage.settlement",
        "src.services.settlement_service",
        "automation_scheduler.paper_trade_ledger",
        "automation_scheduler.paper_decision_ledger",
        "src.services.ledger_service",
        "src.services.execution_service",
        "bet_decision_engine",
        "bet_log",
        "src.services.action_betting_service",
        "src.services.decision_engine",
    ]:
        module = importlib.import_module(module_name)
        assert module.__name__ == module_name


def test_decision_engine_exposes_brokerage_execution_plan() -> None:
    decision_engine = importlib.import_module("src.services.decision_engine")
    plan = decision_engine.build_brokerage_execution_plan(
        {
            "ticker": "TEST",
            "stake": 25,
            "american_odds": -110,
            "decision_id": "decision-1",
            "provider": "demo",
        }
    )
    assert plan["order_request"]["instrument_id"] == "TEST"
    assert plan["execution_request"]["execution_mode"] == "disabled"
    assert plan["readiness"]["ready"] is False
