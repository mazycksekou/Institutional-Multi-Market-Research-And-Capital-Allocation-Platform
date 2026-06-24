from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_execution_remediation_checkpoint_docs_state_disabled_boundary() -> None:
    text = (ROOT / "PHASE10K8ZIK_EXECUTION_REMEDIATION_CHECKPOINT.md").read_text(encoding="utf-8")
    for phrase in [
        "Canonical execution path",
        "Broker account creation remains disabled.",
        "Live trading remains disabled.",
        "No separate paper-only canonical path exists.",
    ]:
        assert phrase in text


def test_execution_remediation_checkpoint_status_is_local_only() -> None:
    brokerage = importlib.import_module("src.brokerage")
    plan = importlib.import_module("src.services.decision_engine").build_brokerage_execution_plan(
        {"ticker": "QQQ", "stake": 25, "american_odds": -115, "decision_id": "d3", "provider": "demo"}
    )
    assert brokerage.get_execution_readiness(plan["order_request"]).ready is False
    for relpath in [
        "automation_scheduler/paper_trade_ledger.py",
        "automation_scheduler/paper_decision_ledger.py",
        "src/brokerage/readiness.py",
    ]:
        assert (ROOT / relpath).exists()
    for relpath in [
        "automation_scheduler/execution_gatekeeper.py",
        "automation_scheduler/execution_authorization.py",
    ]:
        assert not (ROOT / relpath).exists()

