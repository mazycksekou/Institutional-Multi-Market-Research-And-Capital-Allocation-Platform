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


def test_sandbox_enablement_layer(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _fresh_import("src.brokerage.sandbox_enablement", monkeypatch)
    _assert_no_forbidden_imports(module)

    default_enablement = module.build_disabled_enablement()
    assert default_enablement.live_enablement_allowed is False
    assert default_enablement.approval_evidence.approved is False

    approval = importlib.import_module("src.brokerage.approval")
    approval_evidence = importlib.import_module("src.brokerage.approval_evidence")
    activation = importlib.import_module("src.brokerage.activation")
    credentials = importlib.import_module("src.brokerage.credential_readiness")
    client_factory = importlib.import_module("src.brokerage.client_factory")
    monitoring = importlib.import_module("src.brokerage.monitoring")
    rollback = importlib.import_module("src.brokerage.rollback")
    kill_switch = importlib.import_module("src.brokerage.kill_switch")
    deployment = importlib.import_module("src.brokerage.deployment_readiness")

    approved_evidence = approval_evidence.ApprovalEvidence(
        evidence_id="approval_evidence_explicit",
        source=approval_evidence.ApprovalSource.OWNER,
        requirements=tuple(
            approval_evidence.ApprovalRequirement(name=req.name, required=req.required, satisfied=True, description=req.description)
            for req in approval.build_default_approval_requirements()
        ),
        approved=True,
        status="approved_local_only",
        approval_scope="sandbox_activation",
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
        requirements=(
            credentials.CredentialRequirement(name="api_key", required=True, satisfied=True, description="ready"),
            credentials.CredentialRequirement(name="api_secret", required=True, satisfied=True, description="ready"),
        ),
        status="ready_local_only",
        ready=True,
        credentials_required=True,
        live_trading_allowed=False,
        blockers=(),
        warnings=(),
    )
    broker_ready_meta = {
        "ready": True,
        "status": "ready_local_only",
        "supported_asset_classes": ({"asset_class": "equity", "supported": True},),
        "supported_order_types": ({"order_type": "market", "supported": True},),
        "account_capabilities": ({"capability_name": "sandbox_account", "supported": True},),
        "reconciliation_capabilities": ({"capability_name": "position_reconciliation", "supported": True},),
        "blockers": (),
        "warnings": (),
    }
    monitoring_ready = monitoring.MonitoringReadiness(
        monitoring_id="sandbox_monitoring",
        requirements=(monitoring.MonitoringRequirement(name="health", required=True, satisfied=True),),
        alerting_requirements=(monitoring.AlertingRequirement(name="alerts", required=True, satisfied=True),),
        health_check_requirements=(monitoring.HealthCheckRequirement(name="health-check", required=True, satisfied=True),),
        ready=True,
        status="ready_local_only",
        live_monitoring_allowed=False,
        blockers=(),
        warnings=(),
    )
    rollback_plan = rollback.RollbackPlan(rollback_id="rollback-ready", status="metadata_only", steps=("rollback-local-only",))
    rollback_ready_meta = {
        "ready": True,
        "status": "ready_local_only",
        "steps": ("rollback-local-only",),
        "blockers": (),
        "warnings": (),
    }
    deployment_ready = deployment.DeploymentReadiness(
        deployment_id="deployment-ready",
        monitoring_readiness=monitoring_ready,
        rollback_plan=rollback_plan,
        kill_switch_state=kill_switch_state,
        requirements=(deployment.DeploymentRequirement(name="approval_required", required=True, satisfied=True),),
        ready=True,
        status="ready_local_only",
        live_deployment_allowed=False,
        blockers=(),
        warnings=(),
    )
    activation_ready = activation.evaluate_activation_readiness(
        activation.ActivationState(
            activation_id="activation-ready",
            approval_state=approval_state,
            kill_switch_state=kill_switch_state,
            credential_readiness=credential_state,
            broker_client_readiness=broker_ready_meta,
            monitoring_readiness=monitoring_ready,
            rollback_readiness=rollback_ready_meta,
            activation_scope="sandbox_activation",
            status="ready_local_only",
            live_activation_allowed=False,
            metadata={"sandbox_mode": "ready_local_only"},
        )
    )

    request = module.build_disabled_enablement(
        approval_evidence=approved_evidence,
        activation_readiness=activation_ready,
        credential_readiness=credential_state,
        broker_readiness=broker_ready_meta,
        kill_switch_state=kill_switch_state,
        monitoring_readiness=monitoring_ready,
        rollback_readiness=rollback_ready_meta,
        deployment_readiness=deployment_ready,
    )
    result = module.evaluate_enablement(request)
    assert result.live_enablement_allowed is False
    assert result.ready is True
    assert result.state.approval_validation.valid is True
    assert result.state.activation_ready is True
    assert result.state.credential_ready is True
    assert result.state.broker_ready is True
    assert result.state.kill_switch_ready is True
    assert result.state.monitoring_ready is True
    assert result.state.rollback_ready is True
    assert result.state.deployment_ready is True
