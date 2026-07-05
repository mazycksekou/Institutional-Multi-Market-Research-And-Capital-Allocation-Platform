from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_IMPORTS = ["requests", "httpx", "websocket", "openai", "anthropic", "alpaca", "robinhood", "ib_insync", "ccxt"]


def _fresh_import(name: str):
    for key in list(sys.modules):
        if key == name or key.startswith(f"{name}."):
            sys.modules.pop(key, None)
    return importlib.import_module(name)


def test_credential_activation_docs_exist_and_describe_disabled_boundary() -> None:
    docs = [
        ROOT / "PHASE10K8ZJF_CREDENTIAL_ACTIVATION_BOUNDARY.md",
        ROOT / "CREDENTIAL_LOADING_REQUIREMENTS_AFTER_10K8ZJF.md",
        ROOT / "CREDENTIAL_LOADING_DISABLED_BEHAVIOR_AFTER_10K8ZJF.md",
    ]
    for path in docs:
        assert path.is_file(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs).lower()
    for phrase in [
        "must require approvalstate",
        "must require a clear kill switch",
        "always raises disabledcredentialloaderror",
        "no environment variables are read at import time",
    ]:
        assert phrase in text


def test_credential_activation_boundary_builds_requests_and_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    approval = _fresh_import("src.brokerage.approval")
    kill_switch = _fresh_import("src.brokerage.kill_switch")
    credential_loader = _fresh_import("src.brokerage.credential_loader")

    requirements = tuple(
        approval.ApprovalRequirement(name=item.name, required=item.required, satisfied=True, description=item.description)
        for item in approval.build_default_approval_requirements()
    )
    approval_state = approval.ApprovalState(approval_id="approval-satisfied", status="approved", approved=True, requirements=requirements)
    clear_kill_switch = kill_switch.KillSwitchState(kill_switch_id="kill-switch-clear", clear=True, status="clear", reason="approval-granted")

    requirements_model = credential_loader.build_credential_activation_requirements(
        approval_state,
        clear_kill_switch,
        broker_name="demo-broker",
        required_credentials=("api_key", "api_secret"),
        credential_sources=("env", "vault"),
    )
    request = credential_loader.build_credential_load_request(
        approval_state,
        clear_kill_switch,
        broker_name="demo-broker",
        required_credentials=("api_key", "api_secret"),
        credential_sources=("env", "vault"),
    )
    assert requirements_model.approval_state.approval_id == "approval-satisfied"
    assert requirements_model.kill_switch_state.clear is True
    assert "credential_loading_disabled_in_this_phase" in requirements_model.warnings
    assert request.requirements.approval_gate_status == "approved_local_only"
    assert request.requirements.kill_switch_status == "clear"
    assert request.credential_names == ("api_key", "api_secret")

    with pytest.raises(credential_loader.DisabledCredentialLoadError):
        credential_loader.load_credentials_disabled(
            approval_state,
            clear_kill_switch,
            broker_name="demo-broker",
            required_credentials=("api_key",),
        )

    source = Path(credential_loader.__file__).read_text(encoding="utf-8").lower()
    for item in FORBIDDEN_IMPORTS:
        assert f"import {item}" not in source
        assert f"from {item}" not in source
