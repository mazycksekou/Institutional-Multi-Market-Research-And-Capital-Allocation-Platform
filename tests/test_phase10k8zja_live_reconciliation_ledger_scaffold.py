from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _fresh_import(name: str):
    for key in list(sys.modules):
        if key == name or key.startswith(f"{name}."):
            sys.modules.pop(key, None)
    return importlib.import_module(name)


def test_live_reconciliation_and_ledger_docs_exist_and_describe_disabled_behavior() -> None:
    docs = [
        ROOT / "PHASE10K8ZJA_LIVE_RECONCILIATION_LEDGER_SCAFFOLD.md",
        ROOT / "LIVE_RECONCILIATION_DISABLED_BEHAVIOR_AFTER_10K8ZJA.md",
        ROOT / "LIVE_LEDGER_PERSISTENCE_DISABLED_BEHAVIOR_AFTER_10K8ZJA.md",
    ]
    for path in docs:
        assert path.is_file(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs).lower()
    for phrase in [
        "live reconciliation remains disabled",
        "live ledger persistence remains disabled",
        "live reconciliation plans are local metadata only",
        "no external writes are performed.",
    ]:
        assert phrase.lower() in text


def test_live_reconciliation_and_ledger_scaffold_builds_plans_and_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    approval = _fresh_import("src.brokerage.approval")
    factory = _fresh_import("src.brokerage.client_factory")
    live_reconciliation = _fresh_import("src.brokerage.live_reconciliation")
    live_ledger = _fresh_import("src.brokerage.live_ledger")

    requirements = tuple(
        approval.ApprovalRequirement(name=item.name, required=item.required, satisfied=True, description=item.description)
        for item in approval.build_default_approval_requirements()
    )
    approval_state = approval.ApprovalState(approval_id="approval-satisfied", status="approved", approved=True, requirements=requirements)
    descriptor = factory.build_broker_client_descriptor(approval_state, broker_name="demo-broker", account_id="acct-1")
    current_positions = [brokerage.build_position_snapshot({"instrument_id": "TEST", "quantity": 1, "mark_price": 1.2})]
    target_positions = [brokerage.build_position_snapshot({"instrument_id": "TEST", "quantity": 2, "mark_price": 1.3})]

    recon_plan = live_reconciliation.build_live_reconciliation_plan(
        current_positions,
        target_positions,
        approval_state=approval_state,
        broker_client_descriptor=descriptor,
        account_id="acct-1",
        broker_name="demo-broker",
    )
    assert recon_plan.live_reconciliation_allowed is False
    assert recon_plan.approval_gate_status == "approved_local_only"
    assert recon_plan.reconciliation_request.account_id == "acct-1"

    ledger_plan = live_ledger.build_live_ledger_persistence_plan(
        approval_state=approval_state,
        broker_client_descriptor=descriptor,
        ledger_namespace="live_execution",
    )
    assert ledger_plan.live_persistence_allowed is False
    assert ledger_plan.approval_gate_status == "approved_local_only"
    assert ledger_plan.ledger_namespace == "live_execution"

    with pytest.raises(live_reconciliation.LiveReconciliationDisabledError):
        live_reconciliation.reconcile_live_positions_disabled(
            current_positions,
            target_positions,
            approval_state=approval_state,
            broker_client_descriptor=descriptor,
            account_id="acct-1",
            broker_name="demo-broker",
        )
    with pytest.raises(live_ledger.LiveLedgerPersistenceDisabledError):
        live_ledger.persist_live_ledger_disabled(
            approval_state=approval_state,
            broker_client_descriptor=descriptor,
            ledger_namespace="live_execution",
        )
