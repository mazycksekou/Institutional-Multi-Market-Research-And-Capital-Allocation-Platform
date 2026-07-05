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


def test_broker_adapter_docs_exist_and_describe_disabled_boundary() -> None:
    docs = [
        ROOT / "PHASE10K8ZJD_BROKER_ADAPTER_PROTOCOL.md",
        ROOT / "BROKER_ADAPTER_CAPABILITIES_AFTER_10K8ZJD.md",
        ROOT / "BROKER_ADAPTER_BOUNDARY_AFTER_10K8ZJD.md",
    ]
    for path in docs:
        assert path.is_file(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs).lower()
    for phrase in [
        "canonical execution path remains",
        "broker adapter boundary",
        "no sdk imports",
        "live trading remains impossible",
    ]:
        assert phrase in text


def test_broker_adapter_protocol_builds_metadata_and_stays_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    adapter = _fresh_import("src.brokerage.adapter")

    assert brokerage.BrokerAdapter.__module__ == "src.brokerage.adapter"
    assert brokerage.BrokerAdapterDescriptor.__module__ == "src.brokerage.adapter"
    descriptor = adapter.build_adapter_descriptor(broker_name="demo-broker", provider_name="demo-provider")
    capabilities = adapter.build_adapter_capabilities()
    status = adapter.build_disabled_adapter_status(broker_name="demo-broker", provider_name="demo-provider")

    assert descriptor.broker_name == "demo-broker"
    assert descriptor.live_trading_allowed is False
    assert capabilities.supports_submit is False
    assert capabilities.live_trading_allowed is False
    assert status.ready is False
    assert status.brokerage_boundary_disabled is True
    assert status.live_trading_allowed is False
    assert status.blockers
    assert "broker_adapter_boundary_disabled" in status.blockers

    source = Path(adapter.__file__).read_text(encoding="utf-8").lower()
    for item in FORBIDDEN_IMPORTS:
        assert f"import {item}" not in source
        assert f"from {item}" not in source
