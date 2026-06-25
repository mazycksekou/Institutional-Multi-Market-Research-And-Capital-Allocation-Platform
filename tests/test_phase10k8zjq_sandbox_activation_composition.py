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


def test_sandbox_activation_composition(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _fresh_import("src.brokerage.sandbox_activation", monkeypatch)
    proof_module = importlib.import_module("src.brokerage.approval_evidence")
    _assert_no_forbidden_imports(module)

    default_request = module.build_disabled_sandbox_activation()
    assert default_request.live_activation_allowed is False
    assert default_request.approval_evidence.approved is False

    approved_evidence = proof_module.ApprovalEvidence(
        evidence_id="approval_evidence_explicit",
        source=proof_module.ApprovalSource.OWNER,
        requirements=tuple(
            proof_module.ApprovalRequirement(name=req.name, required=req.required, satisfied=True, description=req.description)
            for req in proof_module.build_default_approval_evidence().requirements
        ),
        approved=True,
        status="approved_local_only",
        approval_scope="sandbox_activation",
    )
    activation_request = module.build_disabled_sandbox_activation(
        approval_evidence=approved_evidence,
        activation_metadata={"sandbox_mode": "explicit"},
        broker_readiness={
            "ready": True,
            "status": "ready_local_only",
            "blockers": (),
            "warnings": (),
        },
        credential_readiness={
            "ready": True,
            "status": "ready_local_only",
            "blockers": (),
            "warnings": (),
        },
        kill_switch_state={"clear": True, "status": "clear", "reason": "local_only"},
        rollback_metadata={"status": "metadata_only", "steps": ("rollback",)},
        monitoring_readiness={
            "ready": True,
            "status": "ready_local_only",
            "blockers": (),
            "warnings": (),
        },
        deployment_readiness={
            "ready": False,
            "status": "disabled",
            "blockers": ("deployment_disabled",),
            "warnings": (),
        },
    )
    result = module.evaluate_sandbox_activation(activation_request)
    assert result.live_activation_allowed is False
    assert result.state.approval_validation.valid is True
    assert result.state.broker_readiness_ready is True
    assert result.state.credential_readiness_ready is True
    assert result.state.kill_switch_ready is True
    assert result.state.rollback_ready is True
    assert result.state.monitoring_ready is True
    assert result.state.deployment_ready is False

