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


def test_live_submit_docs_exist_and_describe_disabled_behavior() -> None:
    docs = [
        ROOT / "PHASE10K8ZJ9_LIVE_SUBMIT_INTERFACE_SCAFFOLD.md",
        ROOT / "LIVE_SUBMIT_DISABLED_BEHAVIOR_AFTER_10K8ZJ9.md",
        ROOT / "LIVE_SUBMIT_REQUIREMENTS_AFTER_10K8ZJ9.md",
    ]
    for path in docs:
        assert path.is_file(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs).lower()
    for phrase in [
        "approval state and broker client descriptor are required",
        "submit_live_order_disabled() always raises livesubmitdisablederror",
        "live submit remains disabled",
        "no order submission occurs.",
    ]:
        assert phrase.lower() in text


def test_live_submit_scaffold_builds_request_and_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    approval = _fresh_import("src.brokerage.approval")
    factory = _fresh_import("src.brokerage.client_factory")
    live_submit = _fresh_import("src.brokerage.live_submit")

    requirements = tuple(
        approval.ApprovalRequirement(name=item.name, required=item.required, satisfied=True, description=item.description)
        for item in approval.build_default_approval_requirements()
    )
    approval_state = approval.ApprovalState(approval_id="approval-satisfied", status="approved", approved=True, requirements=requirements)
    descriptor = factory.build_broker_client_descriptor(approval_state, broker_name="demo-broker", account_id="acct-1")
    order_request = brokerage.build_order_request({"ticker": "TEST", "stake": 10, "provider": "demo"})
    execution_request = brokerage.build_execution_request(order_request)
    request = live_submit.build_live_submit_request(
        order_request,
        execution_request=execution_request,
        approval_state=approval_state,
        broker_client_descriptor=descriptor,
    )
    assert request.live_submit_allowed is False
    assert request.approval_gate_status == "approved_local_only"
    assert request.order_request.order_id == order_request.order_id
    assert request.execution_request.execution_id == execution_request.execution_id
    with pytest.raises(live_submit.LiveSubmitDisabledError):
        live_submit.submit_live_order_disabled(
            order_request,
            execution_request=execution_request,
            approval_state=approval_state,
            broker_client_descriptor=descriptor,
        )

    source = Path(live_submit.__file__).read_text(encoding="utf-8").lower()
    for item in FORBIDDEN_IMPORTS:
        assert f"import {item}" not in source
        assert f"from {item}" not in source
