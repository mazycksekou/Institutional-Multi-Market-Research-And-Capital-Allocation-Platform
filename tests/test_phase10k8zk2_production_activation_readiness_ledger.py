from __future__ import annotations

import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BLOCKERS = (
    "manual approval",
    "kill-switch clear state",
    "credential loading",
    "broker client creation",
    "broker account creation",
    "live order submission",
    "live position reconciliation",
    "live ledger persistence",
    "monitoring",
    "alerting",
    "rollback readiness",
    "production deployment approval",
)


def test_production_activation_readiness_ledger() -> None:
    docs = (
        "PRODUCTION_ACTIVATION_READINESS_LEDGER_AFTER_10K8ZK2.md",
        "PRODUCTION_ACTIVATION_BLOCKER_LEDGER_AFTER_10K8ZK2.md",
        "PRODUCTION_ACTIVATION_APPROVAL_LEDGER_AFTER_10K8ZK2.md",
        "PRODUCTION_ACTIVATION_KILL_SWITCH_LEDGER_AFTER_10K8ZK2.md",
    )
    for name in docs:
        assert (ROOT / name).exists(), name

    blocker_text = (ROOT / "PRODUCTION_ACTIVATION_BLOCKER_LEDGER_AFTER_10K8ZK2.md").read_text(encoding="utf-8")
    for phrase in EXPECTED_BLOCKERS:
        assert phrase in blocker_text or phrase in (ROOT / "PRODUCTION_ACTIVATION_READINESS_LEDGER_AFTER_10K8ZK2.md").read_text(encoding="utf-8"), phrase

    approval = importlib.import_module("src.brokerage.approval")
    kill_switch = importlib.import_module("src.brokerage.kill_switch")
    credentials = importlib.import_module("src.brokerage.credential_readiness")
    client_factory = importlib.import_module("src.brokerage.client_factory")
    accounts = importlib.import_module("src.brokerage.accounts")
    orders = importlib.import_module("src.brokerage.orders")
    live_submit = importlib.import_module("src.brokerage.live_submit")
    live_reconciliation = importlib.import_module("src.brokerage.live_reconciliation")
    live_ledger = importlib.import_module("src.brokerage.live_ledger")
    monitoring = importlib.import_module("src.brokerage.monitoring")
    rollback = importlib.import_module("src.brokerage.rollback")
    deployment = importlib.import_module("src.brokerage.deployment_readiness")

    approval_state = approval.ApprovalState(approval_id="approval_blocked", approved=False)
    assert approval.evaluate_approval_gate(approval_state).ready is False
    with pytest.raises(approval.ApprovalMissingError):
        approval.require_live_approval(approval_state)

    kill_state = kill_switch.build_default_kill_switch_state()
    assert kill_state.clear is False
    with pytest.raises(kill_switch.KillSwitchTriggeredError):
        kill_switch.require_kill_switch_clear(kill_state)

    credential_state = credentials.build_disabled_credential_readiness(broker_name="sandbox-broker")
    assert credential_state.ready is False

    descriptor = client_factory.BrokerClientDescriptor(
        broker_name="sandbox-broker",
        client_name="disabled",
        environment="disabled",
    )
    with pytest.raises(client_factory.DisabledBrokerClientError):
        client_factory.create_broker_client_disabled(approval_state, broker_name="sandbox-broker")

    with pytest.raises(accounts.DisabledAccountCreationError):
        accounts.create_account_disabled()

    order_request = orders.build_order_request({"instrument_id": "ABC", "quantity": 1, "side": "buy"})
    with pytest.raises(live_submit.LiveSubmitDisabledError):
        live_submit.submit_live_order_disabled(
            order_request,
            approval_state=approval_state,
            broker_client_descriptor=descriptor,
        )

    with pytest.raises(live_reconciliation.LiveReconciliationDisabledError):
        live_reconciliation.reconcile_live_positions_disabled(
            [],
            [],
            approval_state=approval_state,
            broker_client_descriptor=descriptor,
        )

    with pytest.raises(live_ledger.LiveLedgerPersistenceDisabledError):
        live_ledger.persist_live_ledger_disabled(
            approval_state=approval_state,
            broker_client_descriptor=descriptor,
        )

    monitoring_state = monitoring.build_monitoring_readiness()
    assert monitoring_state.ready is False
    rollback_plan = rollback.build_rollback_plan()
    assert rollback_plan.status == "metadata_only"
    deployment_state = deployment.build_disabled_deployment_readiness()
    assert deployment_state.ready is False
    with pytest.raises(deployment.ProductionDeploymentBlockedError):
        deployment.require_deployment_ready()
