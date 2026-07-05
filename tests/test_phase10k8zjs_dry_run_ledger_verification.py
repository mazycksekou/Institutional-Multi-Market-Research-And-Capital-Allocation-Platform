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


def test_dry_run_ledger_verification(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _fresh_import("src.brokerage.dry_run_ledger", monkeypatch)
    _assert_no_forbidden_imports(module)

    ledger = module.build_dry_run_ledger(ledger_path=tmp_path / "dry_run_ledger.jsonl")
    assert ledger.live_persistence_allowed is False
    updated = module.append_dry_run_event(ledger, order_request={"instrument_id": "ABC", "quantity": 1, "side": "buy"})
    assert len(updated.entries) == 1
    result = module.verify_dry_run_consistency(updated)
    assert result["consistent"] is True
    assert result["live_persistence_allowed"] is False
    assert Path(updated.ledger_path).exists()

