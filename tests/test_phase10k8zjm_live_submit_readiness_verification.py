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


def test_live_submit_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _fresh_import("src.brokerage.submit_readiness", monkeypatch)
    orders = importlib.import_module("src.brokerage.orders")
    live_submit = importlib.import_module("src.brokerage.live_submit")
    ledger = importlib.import_module("src.brokerage.ledger")
    approval = importlib.import_module("src.brokerage.approval")

    _assert_no_forbidden_imports(module)

    order_request = orders.build_order_request({"instrument_id": "ABC", "side": "buy", "quantity": 1, "provider": "sandbox"})
    execution_request = orders.build_execution_request(order_request)
    approval_state = approval.ApprovalState(
        approval_id="submit-ready",
        status="approved_local_only",
        approved=True,
        requirements=tuple(
            approval.ApprovalRequirement(name=req.name, required=req.required, satisfied=True, description=req.description)
            for req in approval.build_default_approval_requirements()
        ),
    )
    broker_descriptor = importlib.import_module("src.brokerage.client_factory").BrokerClientDescriptor(
        broker_name="sandbox-broker",
        client_name="sandbox-client",
        environment="disabled",
        live_trading_allowed=False,
    )

    state = module.build_disabled_submit_readiness(
        order_request,
        execution_request=execution_request,
        approval_state=approval_state,
        broker_client_descriptor=broker_descriptor,
    )
    assert state.submit_path_disabled is True
    assert state.live_submit_allowed is False
    assert state.ledger_event is not None
    evaluated = module.evaluate_submit_readiness(
        order_request,
        execution_request=execution_request,
        approval_state=approval_state,
        broker_client_descriptor=broker_descriptor,
    )
    assert evaluated.ready is False
    assert evaluated.live_submit_allowed is False
    ledger.clear_ledger_events()
    ledger.record_ledger_event(state.ledger_event)
    assert ledger.get_ledger_events()

    result = module.verify_submit_path_disabled(
        order_request,
        execution_request=execution_request,
        approval_state=approval_state,
        broker_client_descriptor=broker_descriptor,
    )
    assert result.submit_path_disabled is True
    assert result.live_submit_allowed is False

    with pytest.raises(live_submit.LiveSubmitDisabledError):
        live_submit.submit_live_order_disabled(
            order_request,
            execution_request=execution_request,
            approval_state=approval_state,
            broker_client_descriptor=broker_descriptor,
        )
