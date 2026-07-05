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


def test_sandbox_submit_docs_exist_and_describe_disabled_flow() -> None:
    docs = [
        ROOT / "PHASE10K8ZJG_SANDBOX_SUBMIT_FLOW.md",
        ROOT / "SANDBOX_SUBMIT_DISABLED_BEHAVIOR_AFTER_10K8ZJG.md",
        ROOT / "SANDBOX_SUBMIT_REQUIREMENTS_AFTER_10K8ZJG.md",
    ]
    for path in docs:
        assert path.is_file(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs).lower()
    for phrase in [
        "uses the canonical order and execution contracts",
        "approval state is required",
        "a sandbox broker descriptor is required",
        "always raises disabledsandboxsubmiterror",
    ]:
        assert phrase in text


def test_sandbox_submit_flow_builds_live_shaped_request_and_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    approval = _fresh_import("src.brokerage.approval")
    sandbox = _fresh_import("src.brokerage.sandbox")
    sandbox_submit = _fresh_import("src.brokerage.sandbox_submit")

    requirements = tuple(
        approval.ApprovalRequirement(name=item.name, required=item.required, satisfied=True, description=item.description)
        for item in approval.build_default_approval_requirements()
    )
    approval_state = approval.ApprovalState(approval_id="approval-satisfied", status="approved", approved=True, requirements=requirements)
    descriptor = sandbox.build_sandbox_descriptor(sandbox_id="sandbox-1", broker_name="demo-broker")
    order_request = brokerage.build_order_request({"ticker": "TEST", "stake": 10, "provider": "demo"})
    execution_request = brokerage.build_execution_request(order_request)
    request = sandbox_submit.build_sandbox_submit_request(
        order_request,
        execution_request=execution_request,
        approval_state=approval_state,
        sandbox_descriptor=descriptor,
    )

    assert request.sandbox_submit_allowed is False
    assert request.live_trading_allowed is False
    assert request.approval_gate_status == "approved_local_only"
    assert request.order_request.order_id == order_request.order_id
    assert request.execution_request.execution_id == execution_request.execution_id
    with pytest.raises(sandbox_submit.DisabledSandboxSubmitError):
        sandbox_submit.submit_sandbox_order_disabled(
            order_request,
            execution_request=execution_request,
            approval_state=approval_state,
            sandbox_descriptor=descriptor,
        )

    source = Path(sandbox_submit.__file__).read_text(encoding="utf-8").lower()
    for item in FORBIDDEN_IMPORTS:
        assert f"import {item}" not in source
        assert f"from {item}" not in source
