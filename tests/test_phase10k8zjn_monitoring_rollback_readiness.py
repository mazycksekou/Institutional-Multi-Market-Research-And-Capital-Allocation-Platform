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


def test_monitoring_and_deployment_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    monitoring = _fresh_import("src.brokerage.monitoring", monkeypatch)
    deployment = _fresh_import("src.brokerage.deployment_readiness", monkeypatch)
    kill_switch = importlib.import_module("src.brokerage.kill_switch")
    rollback = importlib.import_module("src.brokerage.rollback")

    _assert_no_forbidden_imports(monitoring)
    _assert_no_forbidden_imports(deployment)

    monitoring_readiness = monitoring.build_monitoring_readiness()
    assert monitoring_readiness.ready is False
    assert monitoring_readiness.live_monitoring_allowed is False

    ready_monitoring = monitoring.MonitoringReadiness(
        monitoring_id="monitoring-ready",
        requirements=(monitoring.MonitoringRequirement(name="health", required=True, satisfied=True),),
        alerting_requirements=(monitoring.AlertingRequirement(name="alerts", required=True, satisfied=True),),
        health_check_requirements=(monitoring.HealthCheckRequirement(name="health-check", required=True, satisfied=True),),
        ready=True,
        status="ready_local_only",
        live_monitoring_allowed=False,
    )
    evaluated_monitoring = monitoring.evaluate_monitoring_readiness(ready_monitoring)
    assert evaluated_monitoring.ready is True
    assert evaluated_monitoring.live_monitoring_allowed is False

    disabled_deployment = deployment.build_disabled_deployment_readiness(
        monitoring_readiness=ready_monitoring,
        rollback_plan=rollback.build_rollback_plan(),
        kill_switch_state=kill_switch.build_default_kill_switch_state(),
    )
    assert disabled_deployment.ready is False
    assert disabled_deployment.live_deployment_allowed is False

    ready_deployment = deployment.DeploymentReadiness(
        deployment_id="deployment-ready",
        monitoring_readiness=ready_monitoring,
        rollback_plan=rollback.RollbackPlan(
            rollback_id="rollback-ready",
            reason="local_only",
            steps=("step-1",),
            status="metadata_only",
        ),
        kill_switch_state=kill_switch.KillSwitchState(
            kill_switch_id="kill-clear",
            clear=True,
            status="clear",
            reason="local_only",
        ),
        requirements=(deployment.DeploymentRequirement(name="monitoring_ready", required=True, satisfied=True),),
        ready=True,
        status="ready_local_only",
        live_deployment_allowed=False,
    )
    evaluated_deployment = deployment.evaluate_deployment_readiness(ready_deployment)
    assert evaluated_deployment.ready is True
    assert evaluated_deployment.live_deployment_allowed is False

    with pytest.raises(deployment.ProductionDeploymentBlockedError):
        deployment.require_deployment_ready(disabled_deployment)

