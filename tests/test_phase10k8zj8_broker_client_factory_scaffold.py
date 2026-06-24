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


def test_broker_client_factory_docs_exist_and_describe_disabled_behavior() -> None:
    docs = [
        ROOT / "PHASE10K8ZJ8_BROKER_CLIENT_FACTORY_SCAFFOLD.md",
        ROOT / "BROKER_CLIENT_FACTORY_DISABLED_BEHAVIOR_AFTER_10K8ZJ8.md",
        ROOT / "BROKER_CLIENT_FACTORY_REQUIREMENTS_AFTER_10K8ZJ8.md",
    ]
    for path in docs:
        assert path.is_file(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs).lower()
    for phrase in [
        "approval state is required",
        "create_broker_client_disabled() always raises disabledbrokerclienterror",
        "no broker SDK imports",
        "live trading remains disabled",
    ]:
        assert phrase.lower() in text


def test_broker_client_factory_scaffold_imports_safely_and_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    approval = _fresh_import("src.brokerage.approval")
    factory = _fresh_import("src.brokerage.client_factory")

    assert brokerage.BrokerClientDescriptor.__module__ == "src.brokerage.client_factory"
    assert brokerage.BrokerClientFactoryStatus.__module__ == "src.brokerage.client_factory"

    requirements = tuple(
        approval.ApprovalRequirement(name=item.name, required=item.required, satisfied=True, description=item.description)
        for item in approval.build_default_approval_requirements()
    )
    approval_state = approval.ApprovalState(approval_id="approval-satisfied", status="approved", approved=True, requirements=requirements)
    descriptor = factory.build_broker_client_descriptor(approval_state, broker_name="demo-broker", account_id="acct-1")
    status = factory.build_disabled_broker_client_status(approval_state, broker_name="demo-broker", account_id="acct-1")
    assert descriptor.approval_state_id == "approval-satisfied"
    assert status.ready is True
    assert status.client_creation_allowed is False
    assert status.live_trading_allowed is False
    assert status.approval_gate.ready is True
    with pytest.raises(factory.DisabledBrokerClientError):
        factory.create_broker_client_disabled(approval_state, broker_name="demo-broker", account_id="acct-1")

    source = Path(factory.__file__).read_text(encoding="utf-8").lower()
    for item in FORBIDDEN_IMPORTS:
        assert f"import {item}" not in source
        assert f"from {item}" not in source
