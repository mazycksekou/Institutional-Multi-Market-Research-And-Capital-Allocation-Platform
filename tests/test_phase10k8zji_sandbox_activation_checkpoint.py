from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _fresh_import(name: str):
    for key in list(sys.modules):
        if key == name or key.startswith(f"{name}."):
            sys.modules.pop(key, None)
    return importlib.import_module(name)


def test_sandbox_activation_checkpoint_docs_exist_and_describe_status() -> None:
    docs = [
        ROOT / "PHASE10K8ZJI_SANDBOX_ACTIVATION_CHECKPOINT.md",
        ROOT / "POST_SANDBOX_BOUNDARY_ARCHITECTURE_MAP_AFTER_10K8ZJI.md",
        ROOT / "REMAINING_PRODUCTION_BLOCKERS_AFTER_10K8ZJI.md",
        ROOT / "NEXT_CONTROLLED_ACTIVATION_PHASE_AFTER_10K8ZJI.md",
    ]
    for path in docs:
        assert path.is_file(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs).lower()
    for phrase in [
        "broker adapter boundary exists as metadata only",
        "sandbox broker boundary exists as metadata only",
        "credential activation boundary exists but remains disabled",
        "sandbox submit remains disabled",
        "live trading remains disabled",
    ]:
        assert phrase in text


def test_sandbox_activation_checkpoint_imports_safely_and_keeps_live_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    approval = _fresh_import("src.brokerage.approval")
    adapter = _fresh_import("src.brokerage.adapter")
    sandbox = _fresh_import("src.brokerage.sandbox")
    credential_loader = _fresh_import("src.brokerage.credential_loader")
    sandbox_submit = _fresh_import("src.brokerage.sandbox_submit")
    kill_switch = _fresh_import("src.brokerage.kill_switch")

    assert brokerage.BrokerAdapterDescriptor.__module__ == "src.brokerage.adapter"
    assert brokerage.SandboxBrokerDescriptor.__module__ == "src.brokerage.sandbox"
    assert brokerage.CredentialActivationState.__module__ == "src.brokerage.credential_loader"
    assert brokerage.SandboxSubmitRequest.__module__ == "src.brokerage.sandbox_submit"

    requirements = tuple(
        approval.ApprovalRequirement(name=item.name, required=item.required, satisfied=True, description=item.description)
        for item in approval.build_default_approval_requirements()
    )
    approval_state = approval.ApprovalState(approval_id="approval-satisfied", status="approved", approved=True, requirements=requirements)
    adapter_descriptor = adapter.build_adapter_descriptor(broker_name="demo-broker", provider_name="demo-provider")
    sandbox_descriptor = sandbox.build_sandbox_descriptor(sandbox_id="sandbox-1", broker_name="demo-broker")
    credential_state = credential_loader.build_credential_activation_requirements(
        approval_state,
        kill_switch.build_default_kill_switch_state(),
        broker_name="demo-broker",
        required_credentials=("api_key",),
    )
    order_request = brokerage.build_order_request({"ticker": "TEST", "stake": 10, "provider": "demo"})
    execution_request = brokerage.build_execution_request(order_request)
    sandbox_submit_request = sandbox_submit.build_sandbox_submit_request(
        order_request,
        execution_request=execution_request,
        approval_state=approval_state,
        sandbox_descriptor=sandbox_descriptor,
    )

    assert adapter_descriptor.live_trading_allowed is False
    assert sandbox_descriptor.live_trading_allowed is False
    assert credential_state.live_trading_allowed is False
    assert sandbox_submit_request.live_trading_allowed is False
    assert sandbox_submit_request.sandbox_submit_allowed is False
    assert kill_switch.build_default_kill_switch_state().clear is False
