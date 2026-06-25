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


def test_operator_approval_interface(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _fresh_import("src.brokerage.operator", monkeypatch)
    _assert_no_forbidden_imports(module)

    default_operator = module.build_default_operator()
    assert default_operator.operator_id == "operator_default"
    assert default_operator.display_name == "default_operator"

    default_request = module.build_operator_request()
    assert default_request.approval_allowed is False
    assert default_request.status == "denied"

    default_decision = module.evaluate_operator_approval(default_request)
    assert default_decision.approved is False
    assert default_decision.status == "denied"
    assert default_decision.approval_allowed is False

    approved_request = module.build_operator_request(
        default_operator,
        requirements=tuple(
            module.ApprovalRequirement(
                name=req.name,
                required=req.required,
                satisfied=True,
                description=req.description,
            )
            for req in importlib.import_module("src.brokerage.approval").build_default_approval_requirements()
        ),
        approval_metadata={
            "approved": True,
            "approval_reference": "manual_review",
            "approval_reason": "local_only_sandbox",
            "satisfied_requirements": [req.name for req in importlib.import_module("src.brokerage.approval").build_default_approval_requirements()],
        },
    )
    approved_decision = module.evaluate_operator_approval(
        approved_request,
        approval_metadata={
            "approved": True,
            "approval_reference": "manual_review",
            "approval_reason": "local_only_sandbox",
            "satisfied_requirements": [item.name for item in approved_request.requirements],
        },
    )
    assert approved_decision.approved is True
    assert approved_decision.status == "approved_local_only"
    assert approved_decision.approval_allowed is True

    record = module.record_operator_decision(approved_request, operator_decision=approved_decision)
    assert record.decision.approved is True
    assert record.audit_trail.entries
    assert record.audit_trail.entries[0].operator_id == "operator_default"

