from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIW_FINAL_EXECUTION_BLOCKER_AUDIT.md",
    ROOT / "FINAL_EXECUTION_BLOCKER_OWNERSHIP_MAP_AFTER_10K8ZIW.md",
    ROOT / "FINAL_EXECUTION_BLOCKER_IMPORT_SCAN_AFTER_10K8ZIW.md",
    ROOT / "FINAL_EXECUTION_BLOCKER_TEST_SCAN_AFTER_10K8ZIW.md",
]


def test_final_execution_blocker_docs_exist_and_classify() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "Canonical execution path:",
        "src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary",
        "DELETE_READY_AFTER_PROOF",
        "ACTIVE_RUNTIME_DEPENDENCY",
        "ACTIVE_TEST_DEPENDENCY",
        "No deletion occurred during the audit step.",
    ]:
        assert phrase in text


def test_final_execution_blocker_canonical_path_imports_and_wrappers_are_removed() -> None:
    brokerage = importlib.import_module("src.brokerage")
    readiness = importlib.import_module("src.brokerage.readiness")
    decision_engine = importlib.import_module("src.services.decision_engine")
    paper_trade_ledger = importlib.import_module("automation_scheduler.paper_trade_ledger")
    paper_decision_ledger = importlib.import_module("automation_scheduler.paper_decision_ledger")

    plan = decision_engine.build_brokerage_execution_plan(
        {"ticker": "TEST", "stake": 10, "american_odds": -110, "decision_id": "d1", "provider": "demo"}
    )
    assert plan["readiness"]["ready"] is False
    assert plan["readiness"]["brokerage_boundary_disabled"] is True
    assert callable(brokerage.submit_order_disabled)
    assert callable(readiness.get_execution_readiness)
    assert callable(paper_trade_ledger.create_paper_entry)
    assert callable(paper_decision_ledger.create_paper_decision_record)
    assert not (ROOT / "automation_scheduler" / "execution_gatekeeper.py").exists()
    assert not (ROOT / "automation_scheduler" / "execution_authorization.py").exists()
