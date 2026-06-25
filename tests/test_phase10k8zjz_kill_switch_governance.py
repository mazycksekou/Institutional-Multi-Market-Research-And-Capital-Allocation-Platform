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


def test_kill_switch_governance(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _fresh_import("src.brokerage.kill_switch_policy", monkeypatch)
    _assert_no_forbidden_imports(module)

    policy = module.build_default_policy()
    decision = module.evaluate_policy(policy)
    assert decision.approved is False
    assert decision.live_trading_allowed is False
    assert "kill_switch_authoritative" in decision.blocked_reasons

    override = module.KillSwitchOverride(override_id="override-1", requested_clear=True, approved=True, reason="local-only")
    overridden = module.evaluate_policy(policy, override=override)
    assert overridden.approved is False
    assert overridden.live_trading_allowed is False
    assert "override_cannot_enable_trading" in overridden.blocked_reasons

