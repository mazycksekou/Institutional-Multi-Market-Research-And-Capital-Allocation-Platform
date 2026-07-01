from __future__ import annotations

import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_execution_blocker_wrapper_deletion_docs_state_no_deletion() -> None:
    text = (ROOT / "PHASE10K8ZIJ_EXECUTION_BLOCKER_WRAPPER_DELETION.md").read_text(encoding="utf-8")
    assert "No execution blocker wrapper files were deleted." in text
    assert "DELETE_READY_AFTER_PROOF: none" in (ROOT / "PHASE10K8ZII_EXECUTION_BLOCKER_FINAL_DELETE_READINESS.md").read_text(encoding="utf-8")


def test_execution_blocker_wrapper_deletion_keeps_files_present() -> None:
    for relpath in [
        'src/brokerage/paper_trade_ledger.py',
        'src/brokerage/paper_decision_ledger.py',
        "src/services/bet_decision_engine.py",
        "src/services/bet_log.py",
    ]:
        assert (ROOT / relpath).exists()
    for relpath in [
        'src/automation_scheduler_legacy/execution_gatekeeper.py',
        'src/automation_scheduler_legacy/execution_authorization.py',
    ]:
        assert not (ROOT / relpath).exists()


def test_execution_blocker_wrapper_deletion_canonical_boundary_imports_safe() -> None:
    brokerage = importlib.import_module("src.brokerage")
    execution = importlib.import_module("src.brokerage.execution")
    plan = importlib.import_module("src.services.decision_engine").build_brokerage_execution_plan(
        {"ticker": "XYZ", "stake": 5, "american_odds": -110, "decision_id": "d2", "provider": "demo"}
    )
    assert brokerage.get_execution_readiness(plan["order_request"]).ready is False
    with pytest.raises(Exception):
        execution.submit_order_disabled(plan["execution_request"])
