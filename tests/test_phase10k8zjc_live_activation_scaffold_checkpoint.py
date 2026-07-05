from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _fresh_import(name: str):
    for key in list(sys.modules):
        if key == name or key.startswith(f"{name}."):
            sys.modules.pop(key, None)
    return importlib.import_module(name)


def test_live_activation_scaffold_checkpoint_docs_exist_and_describe_status() -> None:
    docs = [
        ROOT / "PHASE10K8ZJC_LIVE_ACTIVATION_SCAFFOLD_CHECKPOINT.md",
        ROOT / "POST_LIVE_ACTIVATION_SCAFFOLD_ARCHITECTURE_MAP_AFTER_10K8ZJC.md",
        ROOT / "REMAINING_LIVE_ACTIVATION_BLOCKERS_AFTER_10K8ZJC.md",
        ROOT / "NEXT_CONTROLLED_LIVE_ACTIVATION_PLAN_AFTER_10K8ZJC.md",
    ]
    for path in docs:
        assert path.is_file(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs).lower()
    for phrase in [
        "approval gate status",
        "broker client factory status",
        "live submit status",
        "reconciliation/ledger status",
        "kill-switch/rollback status",
        "live trading still disabled",
        "remaining blockers before controlled live activation",
    ]:
        assert phrase.lower() in text


def test_live_activation_scaffold_checkpoint_imports_safely_and_keeps_live_disabled(monkeypatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    approval = _fresh_import("src.brokerage.approval")
    factory = _fresh_import("src.brokerage.client_factory")
    live_submit = _fresh_import("src.brokerage.live_submit")
    live_reconciliation = _fresh_import("src.brokerage.live_reconciliation")
    live_ledger = _fresh_import("src.brokerage.live_ledger")
    kill_switch = _fresh_import("src.brokerage.kill_switch")
    rollback = _fresh_import("src.brokerage.rollback")

    assert brokerage.ApprovalState.__module__ == "src.brokerage.approval"
    assert brokerage.BrokerClientDescriptor.__module__ == "src.brokerage.client_factory"
    assert brokerage.LiveSubmitRequest.__module__ == "src.brokerage.live_submit"
    assert brokerage.LiveReconciliationPlan.__module__ == "src.brokerage.live_reconciliation"
    assert brokerage.LiveLedgerPersistencePlan.__module__ == "src.brokerage.live_ledger"
    assert brokerage.KillSwitchState.__module__ == "src.brokerage.kill_switch"
    assert brokerage.RollbackPlan.__module__ == "src.brokerage.rollback"

    requirements = tuple(
        approval.ApprovalRequirement(name=item.name, required=item.required, satisfied=True, description=item.description)
        for item in approval.build_default_approval_requirements()
    )
    approval_state = approval.ApprovalState(approval_id="approval-satisfied", status="approved", approved=True, requirements=requirements)
    descriptor = factory.build_broker_client_descriptor(approval_state, broker_name="demo-broker", account_id="acct-1")
    order_request = brokerage.build_order_request({"ticker": "TEST", "stake": 10, "provider": "demo"})
    execution_request = brokerage.build_execution_request(order_request)
    submit_request = live_submit.build_live_submit_request(
        order_request,
        execution_request=execution_request,
        approval_state=approval_state,
        broker_client_descriptor=descriptor,
    )
    recon_plan = live_reconciliation.build_live_reconciliation_plan(
        [brokerage.build_position_snapshot({"instrument_id": "TEST", "quantity": 1})],
        [brokerage.build_position_snapshot({"instrument_id": "TEST", "quantity": 2})],
        approval_state=approval_state,
        broker_client_descriptor=descriptor,
        broker_name="demo-broker",
    )
    ledger_plan = live_ledger.build_live_ledger_persistence_plan(
        approval_state=approval_state,
        broker_client_descriptor=descriptor,
    )
    kill_state = kill_switch.build_default_kill_switch_state()
    rollback_plan = rollback.build_rollback_plan(rollback_id="rollback-1")

    assert submit_request.live_submit_allowed is False
    assert recon_plan.live_reconciliation_allowed is False
    assert ledger_plan.live_persistence_allowed is False
    assert kill_state.clear is False
    assert rollback_plan.status == "metadata_only"
    assert all(
        name in brokerage.__all__
        for name in [
            "ApprovalState",
            "BrokerClientDescriptor",
            "LiveSubmitRequest",
            "LiveReconciliationPlan",
            "LiveLedgerPersistencePlan",
            "KillSwitchState",
            "RollbackPlan",
        ]
    )
