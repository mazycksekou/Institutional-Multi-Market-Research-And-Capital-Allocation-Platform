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


def test_approval_audit_layer(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _fresh_import("src.brokerage.approval_audit", monkeypatch)
    _assert_no_forbidden_imports(module)

    record = module.build_approval_audit()
    assert record.status == "disabled"
    assert record.events == ()

    event = module.ApprovalAuditEvent(
        event_id="approval_audit_event",
        event_type="approval_decision",
        approval_id="approval_audit_default",
        operator_id="operator_default",
        status="approved_local_only",
        message="local approval recorded",
    )
    updated = module.append_approval_event(record, event)
    assert len(updated.events) == 1
    assert updated.events[0].status == "approved_local_only"

    summary = module.summarize_approval_history(updated)
    assert summary.total_events == 1
    assert summary.approved_events == 1
    assert summary.blocked_events == 0

    status = module.ApprovalAuditStatus(ready=False, status="disabled", audit_record=updated)
    assert status.live_audit_allowed is False

