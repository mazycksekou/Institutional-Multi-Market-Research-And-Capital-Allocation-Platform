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


def test_activation_gate_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _fresh_import("src.brokerage.activation", monkeypatch)
    approval = importlib.import_module("src.brokerage.approval")
    kill_switch = importlib.import_module("src.brokerage.kill_switch")

    _assert_no_forbidden_imports(module)

    default_state = module.build_disabled_activation_state()
    assert default_state.live_activation_allowed is False
    assert default_state.status == "disabled"

    with pytest.raises(module.ActivationBlockedError):
        module.require_activation_ready(default_state)

    ready_approval = approval.ApprovalState(
        approval_id="approval-ready",
        status="approved_local_only",
        approved=True,
        requirements=tuple(
            approval.ApprovalRequirement(
                name=req.name,
                required=req.required,
                satisfied=True,
                description=req.description,
            )
            for req in approval.build_default_approval_requirements()
        ),
    )
    clear_kill = kill_switch.KillSwitchState(
        kill_switch_id="kill-clear",
        clear=True,
        status="clear",
        reason="local_only",
    )
    ready_state = module.build_disabled_activation_state(
        approval_state=ready_approval,
        kill_switch_state=clear_kill,
        credential_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
        broker_client_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
        monitoring_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
        rollback_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
    )
    readiness = module.evaluate_activation_readiness(ready_state)
    assert readiness.ready is True
    assert readiness.live_activation_allowed is False
    assert readiness.approval_required is True
    assert readiness.kill_switch_required is True
    assert readiness.credentials_required is True
    assert readiness.broker_required is True
    assert readiness.monitoring_required is True
    assert readiness.rollback_required is True
    gate_result = module.require_activation_ready(ready_state)
    assert gate_result.approved is True

    blocked_cases = [
        (
            "approval",
            module.build_disabled_activation_state(
                kill_switch_state=clear_kill,
                credential_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                broker_client_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                monitoring_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                rollback_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
            ),
            "approval_state_ready",
        ),
        (
            "kill_switch",
            module.build_disabled_activation_state(
                approval_state=ready_approval,
                credential_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                broker_client_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                monitoring_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                rollback_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
            ),
            "kill_switch_clear",
        ),
        (
            "credential",
            module.build_disabled_activation_state(
                approval_state=ready_approval,
                kill_switch_state=clear_kill,
                credential_readiness={"ready": False, "status": "disabled", "blockers": (), "warnings": ()},
                broker_client_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                monitoring_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                rollback_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
            ),
            "credential_readiness_ready",
        ),
        (
            "broker",
            module.build_disabled_activation_state(
                approval_state=ready_approval,
                kill_switch_state=clear_kill,
                credential_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                broker_client_readiness={"ready": False, "status": "disabled", "blockers": (), "warnings": ()},
                monitoring_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                rollback_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
            ),
            "broker_client_readiness_ready",
        ),
        (
            "monitoring",
            module.build_disabled_activation_state(
                approval_state=ready_approval,
                kill_switch_state=clear_kill,
                credential_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                broker_client_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                monitoring_readiness={"ready": False, "status": "disabled", "blockers": (), "warnings": ()},
                rollback_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
            ),
            "monitoring_readiness_ready",
        ),
        (
            "rollback",
            module.build_disabled_activation_state(
                approval_state=ready_approval,
                kill_switch_state=clear_kill,
                credential_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                broker_client_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                monitoring_readiness={"ready": True, "status": "ready_local_only", "blockers": (), "warnings": ()},
                rollback_readiness={"ready": False, "status": "disabled", "blockers": (), "warnings": ()},
            ),
            "rollback_readiness_ready",
        ),
    ]
    for label, state, blocker_name in blocked_cases:
        result = module.evaluate_activation_readiness(state)
        assert result.ready is False, label
        assert result.live_activation_allowed is False
        assert blocker_name in result.gate_result.missing_requirements, label
        with pytest.raises(module.ActivationBlockedError):
            module.require_activation_ready(state)
