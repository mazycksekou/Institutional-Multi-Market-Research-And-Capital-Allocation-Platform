from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIZ_FINAL_EXECUTION_BLOCKER_DELETE_PROOF.md",
    ROOT / "FINAL_EXECUTION_BLOCKER_IMPORT_SCAN_AFTER_10K8ZIZ.md",
    ROOT / "FINAL_EXECUTION_BLOCKER_TEST_SCAN_AFTER_10K8ZIZ.md",
    ROOT / "FINAL_EXECUTION_BLOCKER_DELETE_DECISION_AFTER_10K8ZIZ.md",
]


def test_final_execution_blocker_delete_proof_docs_exist_and_classify() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "DELETE_READY_AFTER_PROOF",
        "automation_scheduler/execution_gatekeeper.py",
        "automation_scheduler/execution_authorization.py",
        "automation_scheduler/paper_trade_ledger.py",
        "automation_scheduler/paper_decision_ledger.py",
        "Canonical execution path remains intact and disabled.",
    ]:
        assert phrase in text


def test_final_execution_blocker_delete_proof_canonical_imports_safe() -> None:
    readiness = importlib.import_module("src.brokerage.readiness")
    decision_engine = importlib.import_module("src.services.decision_engine")
    paper_trade_ledger = importlib.import_module('src.automation_scheduler_legacy.paper_trade_ledger')
    paper_decision_ledger = importlib.import_module('src.automation_scheduler_legacy.paper_decision_ledger')

    plan = decision_engine.build_brokerage_execution_plan(
        {"ticker": "MSFT", "stake": 8, "american_odds": -105, "decision_id": "d4", "provider": "demo"}
    )
    assert readiness.get_execution_readiness(plan["order_request"]).ready is False
    assert callable(paper_trade_ledger.create_paper_entry)
    assert callable(paper_decision_ledger.create_paper_decision_record)
