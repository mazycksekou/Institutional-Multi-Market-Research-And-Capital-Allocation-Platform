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


def test_broker_adapter_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _fresh_import("src.brokerage.adapter_readiness", monkeypatch)
    _assert_no_forbidden_imports(module)

    readiness = module.build_broker_adapter_readiness(
        broker_name="sandbox-broker",
        supported_asset_classes=[
            {"asset_class": "equity", "supported": True, "notes": "local metadata only"},
        ],
        supported_order_types=[
            {"order_type": "market", "supported": True, "notes": "local metadata only"},
        ],
        account_capabilities=[
            {"capability_name": "sandbox_account", "supported": True, "notes": "local metadata only"},
        ],
        reconciliation_capabilities=[
            {"capability_name": "position_reconciliation", "supported": True, "notes": "local metadata only"},
        ],
    )
    assert readiness.broker_name == "sandbox-broker"
    assert readiness.status in {"ready_local_only", "disabled"}
    assert readiness.live_trading_allowed is False
    assert readiness.sandbox_allowed is True
    assert readiness.supported_asset_classes[0].asset_class == "equity"
    assert readiness.supported_order_types[0].order_type == "market"
    assert readiness.account_capabilities[0].capability_name == "sandbox_account"
    assert readiness.reconciliation_capabilities[0].capability_name == "position_reconciliation"
    evaluated = module.validate_broker_adapter_readiness(readiness)
    assert evaluated.broker_name == readiness.broker_name
    assert evaluated.live_trading_allowed is False

