from __future__ import annotations

import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_final_live_trading_disabled_proof() -> None:
    docs = (
        "FINAL_LIVE_TRADING_DISABLED_PROOF_AFTER_10K8ZK2.md",
        "FINAL_ACCOUNT_CREATION_DISABLED_PROOF_AFTER_10K8ZK2.md",
        "FINAL_ORDER_SUBMISSION_DISABLED_PROOF_AFTER_10K8ZK2.md",
        "FINAL_DEPLOYMENT_DISABLED_PROOF_AFTER_10K8ZK2.md",
    )
    for name in docs:
        assert (ROOT / name).exists(), name

    proof_text = (ROOT / "FINAL_LIVE_TRADING_DISABLED_PROOF_AFTER_10K8ZK2.md").read_text(encoding="utf-8")
    assert "Live trading remains impossible in this phase." in proof_text

    approval = importlib.import_module("src.brokerage.approval")
    kill_switch = importlib.import_module("src.brokerage.kill_switch")
    credentials = importlib.import_module("src.brokerage.credentials")
    credential_loader = importlib.import_module("src.brokerage.credential_loader")
    client_factory = importlib.import_module("src.brokerage.client_factory")
    accounts = importlib.import_module("src.brokerage.accounts")
    orders = importlib.import_module("src.brokerage.orders")
    live_submit = importlib.import_module("src.brokerage.live_submit")
    live_reconciliation = importlib.import_module("src.brokerage.live_reconciliation")
    live_ledger = importlib.import_module("src.brokerage.live_ledger")
    deployment = importlib.import_module("src.brokerage.deployment_readiness")

    approval_state = approval.ApprovalState(approval_id="approval_blocked", approved=False)
    kill_state = kill_switch.build_default_kill_switch_state()
    descriptor = client_factory.BrokerClientDescriptor(
        broker_name="sandbox-broker",
        client_name="disabled",
        environment="disabled",
    )

    assert kill_state.clear is False
    with pytest.raises(kill_switch.KillSwitchTriggeredError):
        kill_switch.require_kill_switch_clear(kill_state)

    with pytest.raises(credentials.DisabledBrokerCredentialError):
        credentials.validate_broker_credentials_disabled(
            policy=credentials.BrokerCredentialPolicy(broker_name="sandbox-broker"),
        )

    with pytest.raises(credential_loader.DisabledCredentialLoadError):
        credential_loader.load_credentials_disabled(
            approval_state,
            kill_state,
            broker_name="sandbox-broker",
            required_credentials=("api_key", "api_secret"),
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

    deployment_state = deployment.build_disabled_deployment_readiness()
    assert deployment_state.ready is False
    with pytest.raises(deployment.ProductionDeploymentBlockedError):
        deployment.require_deployment_ready()
