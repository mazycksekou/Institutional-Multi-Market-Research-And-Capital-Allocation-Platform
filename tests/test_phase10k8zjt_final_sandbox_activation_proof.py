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


def test_final_sandbox_activation_proof(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _fresh_import("src.brokerage.sandbox_proof", monkeypatch)
    _assert_no_forbidden_imports(module)

    result = module.run_sandbox_proof()
    assert result.proof_passed is True
    assert result.live_trading_allowed is False
    assert result.sandbox_activation.live_activation_allowed is False
    assert result.sandbox_activation.state.approval_validation.valid is True
    assert result.sandbox_activation.state.deployment_ready is False
    assert result.dry_run_execution.live_submit_allowed is False
    assert result.dry_run_ledger.live_persistence_allowed is False
    assert any(step.name == "broker_sdk_absent" and step.passed for step in result.steps)

