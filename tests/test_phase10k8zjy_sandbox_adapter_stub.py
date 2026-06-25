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


def test_sandbox_adapter_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _fresh_import("src.brokerage.sandbox_adapter", monkeypatch)
    _assert_no_forbidden_imports(module)

    adapter = module.build_sandbox_adapter(
        broker_name="sandbox-broker",
        supported_asset_classes=["equity"],
        supported_order_types=["market"],
        account_capabilities=["sandbox_account"],
        reconciliation_capabilities=["position_reconciliation"],
    )
    assert adapter.live_trading_allowed is False
    assert adapter.broker_connection_allowed is False
    assert adapter.account_creation_allowed is False
    assert adapter.order_submission_allowed is False

    response = module.evaluate_sandbox_adapter(adapter)
    assert response.live_trading_allowed is False
    assert response.status in {"ready_local_only", "sandbox_adapter_blocked"}
    assert response.broker_connection_allowed is False

