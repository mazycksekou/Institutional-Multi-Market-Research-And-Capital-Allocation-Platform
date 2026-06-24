from __future__ import annotations

import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_execution_scheduler_wrapper_deletion_docs_state_no_deletion() -> None:
    text = (ROOT / "PHASE10K8ZIE_EXECUTION_SCHEDULER_WRAPPER_DELETION.md").read_text(encoding="utf-8")
    assert "No execution scheduler wrapper was deleted in this phase." in text
    assert "DELETE_READY_AFTER_PROOF" in (ROOT / "PHASE10K8ZID_EXECUTION_FINAL_DELETE_READINESS.md").read_text(encoding="utf-8")


def test_execution_scheduler_wrappers_still_exist() -> None:
    for relpath in [
        "automation_scheduler/execution_gatekeeper.py",
        "automation_scheduler/execution_authorization.py",
        "automation_scheduler/paper_trade_ledger.py",
        "automation_scheduler/paper_decision_ledger.py",
    ]:
        assert (ROOT / relpath).exists()


def test_execution_scheduler_canonical_boundary_remains_disabled() -> None:
    execution = importlib.import_module("src.brokerage.execution")
    brokerage = importlib.import_module("src.brokerage")
    with pytest.raises(Exception):
        execution.submit_order_disabled({"execution_mode": "disabled"})
    with pytest.raises(Exception):
        brokerage.submit_order_disabled({"execution_mode": "disabled"})

