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


def test_sandbox_broker_docs_exist_and_describe_disabled_boundary() -> None:
    docs = [
        ROOT / "PHASE10K8ZJE_SANDBOX_BROKER_BOUNDARY.md",
        ROOT / "SANDBOX_BROKER_REQUIREMENTS_AFTER_10K8ZJE.md",
        ROOT / "SANDBOX_BROKER_DISABLED_BEHAVIOR_AFTER_10K8ZJE.md",
    ]
    for path in docs:
        assert path.is_file(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs).lower()
    for phrase in [
        "sandbox descriptors and status snapshots are local descriptors",
        "approval remains required",
        "account creation remains disallowed",
        "no sdk, network, or broker behavior is activated",
    ]:
        assert phrase in text


def test_sandbox_broker_boundary_builds_metadata_and_stays_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    sandbox = _fresh_import("src.brokerage.sandbox")

    assert brokerage.SandboxBrokerDescriptor.__module__ == "src.brokerage.sandbox"
    descriptor = sandbox.build_sandbox_descriptor(sandbox_id="sandbox-1", broker_name="demo-broker")
    capabilities = sandbox.build_sandbox_capabilities()
    status = sandbox.build_sandbox_status(sandbox_id="sandbox-1", broker_name="demo-broker")

    assert descriptor.sandbox_id == "sandbox-1"
    assert descriptor.account_creation_allowed is False
    assert descriptor.live_trading_allowed is False
    assert capabilities.supports_submit is False
    assert capabilities.credentials_required is False
    assert status.ready is False
    assert status.sandbox_boundary_disabled is True
    assert status.live_trading_allowed is False
    assert status.blockers

    source = Path(sandbox.__file__).read_text(encoding="utf-8").lower()
    for item in FORBIDDEN_IMPORTS:
        assert f"import {item}" not in source
        assert f"from {item}" not in source
