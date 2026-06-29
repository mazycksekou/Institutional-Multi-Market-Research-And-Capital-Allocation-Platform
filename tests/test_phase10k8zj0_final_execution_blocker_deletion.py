from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_final_execution_blocker_deletion_docs_and_file_state() -> None:
    for path in [
        ROOT / "PHASE10K8ZJ0_FINAL_EXECUTION_BLOCKER_DELETION.md",
        ROOT / "FINAL_EXECUTION_BLOCKER_DELETION_PROOF_AFTER_10K8ZJ0.md",
        ROOT / "POST_FINAL_EXECUTION_BLOCKER_DELETION_IMPORT_SCAN_AFTER_10K8ZJ0.md",
        ROOT / "FINAL_EXECUTION_BLOCKER_DELETION_COMPLETION_STATUS_AFTER_10K8ZJ0.md",
    ]:
        assert path.is_file(), path

    for path in [
        ROOT / "src" / "automation_scheduler_legacy" / "execution_gatekeeper.py",
        ROOT / "src" / "automation_scheduler_legacy" / "execution_authorization.py",
    ]:
        assert not path.exists()

    for path in [
        ROOT / "src" / "automation_scheduler_legacy" / "paper_trade_ledger.py",
        ROOT / "src" / "automation_scheduler_legacy" / "paper_decision_ledger.py",
    ]:
        assert path.exists()


def test_final_execution_blocker_deletion_canonical_boundary_imports_safe() -> None:
    brokerage = importlib.import_module("src.brokerage")
    readiness = importlib.import_module("src.brokerage.readiness")
    decision_engine = importlib.import_module("src.services.decision_engine")

    plan = decision_engine.build_brokerage_execution_plan(
        {"ticker": "GOOG", "stake": 6, "american_odds": -115, "decision_id": "d5", "provider": "demo"}
    )
    assert brokerage.get_execution_readiness(plan["order_request"]).ready is False
    assert callable(readiness.get_execution_readiness)
