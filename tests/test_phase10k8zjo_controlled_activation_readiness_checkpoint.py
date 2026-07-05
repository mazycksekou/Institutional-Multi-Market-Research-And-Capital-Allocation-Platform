from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path

import pytest


FORBIDDEN_IMPORTS = {"requests", "httpx", "websocket", "yfinance", "selenium", "playwright", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"}


def _clear_brokerage_modules() -> None:
    for name in list(sys.modules):
        if name == "src.brokerage" or name.startswith("src.brokerage."):
            sys.modules.pop(name, None)


def _fresh_import(name: str, monkeypatch: pytest.MonkeyPatch):
    _clear_brokerage_modules()

    def _forbidden_getenv(*args, **kwargs):
        raise AssertionError("os.getenv must not be called at import time")

    monkeypatch.setattr(os, "getenv", _forbidden_getenv)
    return importlib.import_module(name)


def _assert_no_forbidden_imports(module) -> None:
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports.isdisjoint(FORBIDDEN_IMPORTS), imports & FORBIDDEN_IMPORTS


def test_controlled_activation_readiness_checkpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    brokerage = _fresh_import("src.brokerage", monkeypatch)
    activation = importlib.import_module("src.brokerage.activation")
    adapter_readiness = importlib.import_module("src.brokerage.adapter_readiness")
    credential_readiness = importlib.import_module("src.brokerage.credential_readiness")
    submit_readiness = importlib.import_module("src.brokerage.submit_readiness")
    monitoring = importlib.import_module("src.brokerage.monitoring")
    deployment = importlib.import_module("src.brokerage.deployment_readiness")
    approval = importlib.import_module("src.brokerage.approval")
    kill_switch = importlib.import_module("src.brokerage.kill_switch")
    rollback = importlib.import_module("src.brokerage.rollback")
    live_submit = importlib.import_module("src.brokerage.live_submit")
    live_reconciliation = importlib.import_module("src.brokerage.live_reconciliation")
    live_ledger = importlib.import_module("src.brokerage.live_ledger")
    accounts = importlib.import_module("src.brokerage.accounts")
    credentials = importlib.import_module("src.brokerage.credentials")
    reconciliation = importlib.import_module("src.brokerage.reconciliation")
    client_factory = importlib.import_module("src.brokerage.client_factory")
    orders = importlib.import_module("src.brokerage.orders")
    execution = importlib.import_module("src.brokerage.execution")
    ledger = importlib.import_module("src.brokerage.ledger")
    readiness = importlib.import_module("src.brokerage.readiness")

    for module in (brokerage, activation, adapter_readiness, credential_readiness, submit_readiness, monitoring, deployment):
        _assert_no_forbidden_imports(module)

    assert hasattr(brokerage, "build_disabled_activation_state")
    assert hasattr(brokerage, "build_broker_adapter_readiness")
    assert hasattr(brokerage, "build_disabled_credential_readiness")
    assert hasattr(brokerage, "build_disabled_submit_readiness")
    assert hasattr(brokerage, "build_monitoring_readiness")
    assert hasattr(brokerage, "build_disabled_deployment_readiness")
    assert hasattr(brokerage, "build_disabled_broker_client_status")
    assert hasattr(brokerage, "build_disabled_adapter_status")

    execution_readiness = readiness.get_execution_readiness({"instrument_id": "ABC", "quantity": 1, "side": "buy"})
    assert execution_readiness.brokerage_boundary_disabled is True
    assert execution_readiness.live_trading_allowed is False

    default_activation = activation.build_disabled_activation_state()
    assert default_activation.live_activation_allowed is False
    with pytest.raises(activation.ActivationBlockedError):
        activation.require_activation_ready(default_activation)

    default_approval = approval.ApprovalState(approval_id="approval-default")
    with pytest.raises(approval.ApprovalMissingError):
        approval.require_live_approval(default_approval)

    assert kill_switch.build_default_kill_switch_state().clear is False
    with pytest.raises(kill_switch.KillSwitchTriggeredError):
        kill_switch.require_kill_switch_clear()

    account_readiness = accounts.build_account_readiness({"account_id": "acct", "broker_name": "sandbox"}, credential_policy={"required_credentials": ("api_key",)})
    assert account_readiness.account_creation_allowed is False
    with pytest.raises(accounts.DisabledAccountCreationError):
        accounts.create_account_disabled({"account_id": "acct", "broker_name": "sandbox"})

    credential_readiness_state = credentials.BrokerCredentialDescriptor(broker_name="sandbox", credential_name="api_key")
    with pytest.raises(credentials.DisabledBrokerCredentialError):
        credentials.validate_broker_credentials_disabled(credential_readiness_state)

    ready_approval = approval.ApprovalState(
        approval_id="approval-ready",
        status="approved_local_only",
        approved=True,
        requirements=tuple(
            approval.ApprovalRequirement(
                name=req.name,
                required=req.required,
                satisfied=True,
                description=req.description,
            )
            for req in approval.build_default_approval_requirements()
        ),
    )
    client_status = client_factory.build_disabled_broker_client_status(ready_approval, broker_name="sandbox")
    assert client_status.live_trading_allowed is False
    with pytest.raises(client_factory.DisabledBrokerClientError):
        client_factory.create_broker_client_disabled(ready_approval, broker_name="sandbox")

    assert adapter_readiness.build_broker_adapter_readiness(
        broker_name="sandbox",
        supported_asset_classes=[{"asset_class": "equity", "supported": True}],
        supported_order_types=[{"order_type": "market", "supported": True}],
        account_capabilities=[{"capability_name": "sandbox_account", "supported": True}],
        reconciliation_capabilities=[{"capability_name": "reconciliation", "supported": True}],
    ).live_trading_allowed is False

    credential_meta = credential_readiness.build_disabled_credential_readiness(broker_name="sandbox")
    assert credential_meta.ready is False

    submit_state = submit_readiness.build_disabled_submit_readiness(
        orders.build_order_request({"instrument_id": "ABC", "quantity": 1, "side": "buy"}),
        approval_state=ready_approval,
        broker_client_descriptor=client_factory.BrokerClientDescriptor(broker_name="sandbox", client_name="sandbox", environment="disabled"),
    )
    assert submit_state.submit_path_disabled is True
    with pytest.raises(live_submit.LiveSubmitDisabledError):
        live_submit.submit_live_order_disabled(
            orders.build_order_request({"instrument_id": "ABC", "quantity": 1, "side": "buy"}),
            approval_state=ready_approval,
            broker_client_descriptor=client_factory.BrokerClientDescriptor(broker_name="sandbox", client_name="sandbox", environment="disabled"),
        )

    with pytest.raises(live_reconciliation.LiveReconciliationDisabledError):
        live_reconciliation.reconcile_live_positions_disabled(
            approval_state=ready_approval,
            broker_client_descriptor=client_factory.BrokerClientDescriptor(broker_name="sandbox", client_name="sandbox", environment="disabled"),
        )

    with pytest.raises(live_ledger.LiveLedgerPersistenceDisabledError):
        live_ledger.persist_live_ledger_disabled(
            approval_state=ready_approval,
            broker_client_descriptor=client_factory.BrokerClientDescriptor(broker_name="sandbox", client_name="sandbox", environment="disabled"),
        )

    with pytest.raises(execution.DisabledExecutionError):
        execution.submit_order_disabled()

    with pytest.raises(reconciliation.DisabledBrokerageError):
        reconciliation.reconcile_positions_disabled()

    ledger.clear_ledger_events()
    ledger.record_ledger_event({"event_type": "checkpoint", "subject_id": "sandbox"})
    assert ledger.get_ledger_events()

    monitoring_ready = monitoring.MonitoringReadiness(
        monitoring_id="monitoring-ready",
        requirements=(monitoring.MonitoringRequirement(name="health", required=True, satisfied=True),),
        alerting_requirements=(monitoring.AlertingRequirement(name="alerts", required=True, satisfied=True),),
        health_check_requirements=(monitoring.HealthCheckRequirement(name="health-check", required=True, satisfied=True),),
        ready=True,
        status="ready_local_only",
        live_monitoring_allowed=False,
    )
    assert monitoring.evaluate_monitoring_readiness(monitoring_ready).live_monitoring_allowed is False

    deployment_ready = deployment.DeploymentReadiness(
        deployment_id="deployment-ready",
        monitoring_readiness=monitoring_ready,
        rollback_plan=rollback.RollbackPlan(rollback_id="rollback-ready", reason="local_only", steps=("step-1",), status="metadata_only"),
        kill_switch_state=kill_switch.KillSwitchState(kill_switch_id="kill-clear", clear=True, status="clear", reason="local_only"),
        requirements=(deployment.DeploymentRequirement(name="monitoring_ready", required=True, satisfied=True),),
        ready=True,
        status="ready_local_only",
        live_deployment_allowed=False,
    )
    assert deployment.evaluate_deployment_readiness(deployment_ready).live_deployment_allowed is False
    with pytest.raises(deployment.ProductionDeploymentBlockedError):
        deployment.require_deployment_ready(deployment.build_disabled_deployment_readiness())
