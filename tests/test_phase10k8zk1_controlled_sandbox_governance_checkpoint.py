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


def test_controlled_sandbox_governance_checkpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    brokerage = _fresh_import("src.brokerage", monkeypatch)
    module_operator = importlib.import_module("src.brokerage.operator")
    module_audit = importlib.import_module("src.brokerage.approval_audit")
    module_enablement = importlib.import_module("src.brokerage.sandbox_enablement")
    module_adapter = importlib.import_module("src.brokerage.sandbox_adapter")
    module_kill = importlib.import_module("src.brokerage.kill_switch_policy")
    module_deployment = importlib.import_module("src.brokerage.deployment_policy")
    live_submit = importlib.import_module("src.brokerage.live_submit")
    execution = importlib.import_module("src.brokerage.execution")
    orders = importlib.import_module("src.brokerage.orders")
    readiness = importlib.import_module("src.brokerage.readiness")

    for module in (brokerage, module_operator, module_audit, module_enablement, module_adapter, module_kill, module_deployment):
        _assert_no_forbidden_imports(module)

    assert hasattr(brokerage, "build_operator_request")
    assert hasattr(brokerage, "build_approval_audit")
    assert hasattr(brokerage, "build_disabled_enablement")
    assert hasattr(brokerage, "build_sandbox_adapter")
    assert hasattr(brokerage, "build_default_kill_switch_policy")
    assert hasattr(brokerage, "build_default_deployment_policy")

    assert hasattr(module_operator, "build_default_operator")
    assert module_operator.build_operator_request().approval_allowed is False

    assert module_audit.build_approval_audit().status == "disabled"
    assert module_enablement.build_disabled_enablement().live_enablement_allowed is False
    assert module_adapter.build_sandbox_adapter(broker_name="sandbox").live_trading_allowed is False
    assert module_kill.evaluate_policy(module_kill.build_default_policy()).live_trading_allowed is False
    assert module_deployment.evaluate_deployment_policy(module_deployment.build_default_policy()).live_deployment_allowed is False

    assert live_submit.build_live_submit_request(
        orders.build_order_request({"instrument_id": "ABC", "quantity": 1, "side": "buy"}),
        approval_state=importlib.import_module("src.brokerage.approval").ApprovalState(approval_id="approval", approved=False),
        broker_client_descriptor=importlib.import_module("src.brokerage.client_factory").BrokerClientDescriptor(broker_name="sandbox", client_name="sandbox", environment="disabled"),
    ).live_submit_allowed is False
    assert execution.submit_order_disabled.__name__ == "submit_order_disabled"
    assert readiness.get_execution_readiness({"instrument_id": "ABC", "quantity": 1, "side": "buy"}).live_trading_allowed is False

    checkpoint_path = Path("PHASE10K8ZK1_CONTROLLED_SANDBOX_GOVERNANCE_CHECKPOINT.md")
    assert checkpoint_path.exists()

