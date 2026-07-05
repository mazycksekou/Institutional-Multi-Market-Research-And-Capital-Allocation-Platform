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


def test_deployment_governance(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _fresh_import("src.brokerage.deployment_policy", monkeypatch)
    _assert_no_forbidden_imports(module)

    policy = module.build_default_policy()
    default = module.evaluate_deployment_policy(policy)
    assert default.live_deployment_allowed is False
    assert default.approved is False

    approval = importlib.import_module("src.brokerage.approval")
    approval_evidence = importlib.import_module("src.brokerage.approval_evidence")
    monitoring = importlib.import_module("src.brokerage.monitoring")
    rollback = importlib.import_module("src.brokerage.rollback")
    kill_switch = importlib.import_module("src.brokerage.kill_switch")
    credentials = importlib.import_module("src.brokerage.credential_readiness")
    client_factory = importlib.import_module("src.brokerage.client_factory")
    adapter_readiness = importlib.import_module("src.brokerage.adapter_readiness")

    approved_evidence = approval_evidence.ApprovalEvidence(
        evidence_id="approval_evidence_explicit",
        source=approval_evidence.ApprovalSource.OWNER,
        requirements=tuple(
            approval_evidence.ApprovalRequirement(name=req.name, required=req.required, satisfied=True, description=req.description)
            for req in approval.build_default_approval_requirements()
        ),
        approved=True,
        status="approved_local_only",
        approval_scope="deployment",
    )
    approval_state = approval.ApprovalState(
        approval_id="approval_state_ready",
        status="approved_local_only",
        approved=True,
        requirements=tuple(
            approval.ApprovalRequirement(name=req.name, required=req.required, satisfied=True, description=req.description)
            for req in approval.build_default_approval_requirements()
        ),
    )
    kill_switch_state = kill_switch.KillSwitchState(kill_switch_id="sandbox_kill_switch", clear=True, status="clear", reason="local_only")
    credential_state = credentials.CredentialReadinessState(
        broker_name="sandbox-broker",
        requirements=(credentials.CredentialRequirement(name="api_key", required=True, satisfied=True),),
        status="ready_local_only",
        ready=True,
        credentials_required=True,
        live_trading_allowed=False,
    )
    broker_state = adapter_readiness.build_broker_adapter_readiness(
        broker_name="sandbox-broker",
        supported_asset_classes=["equity"],
        supported_order_types=["market"],
        account_capabilities=["sandbox_account"],
        reconciliation_capabilities=["position_reconciliation"],
    )
    broker_ready = adapter_readiness.validate_broker_adapter_readiness(broker_state)
    monitoring_ready = monitoring.MonitoringReadiness(
        monitoring_id="monitoring-ready",
        requirements=(monitoring.MonitoringRequirement(name="health", required=True, satisfied=True),),
        alerting_requirements=(monitoring.AlertingRequirement(name="alerts", required=True, satisfied=True),),
        health_check_requirements=(monitoring.HealthCheckRequirement(name="health-check", required=True, satisfied=True),),
        ready=True,
        status="ready_local_only",
        live_monitoring_allowed=False,
    )
    rollback_plan = rollback.RollbackPlan(rollback_id="rollback-ready", status="metadata_only", steps=("rollback-local-only",))
    result = module.evaluate_deployment_policy(
        policy,
        approval_evidence=approved_evidence,
        monitoring_readiness=monitoring_ready,
        rollback_plan=rollback_plan,
        broker_readiness=broker_ready,
        credential_readiness=credential_state,
        kill_switch_state=kill_switch_state,
    )
    assert result.live_deployment_allowed is False
    assert result.approved is True
    assert result.ready is True
    assert result.status == "ready_local_only"

