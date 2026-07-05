from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _clear_brokerage_modules() -> None:
    for name in list(sys.modules):
        if name == "src.brokerage" or name.startswith("src.brokerage."):
            sys.modules.pop(name, None)


def _fresh_import(name: str, monkeypatch: pytest.MonkeyPatch):
    _clear_brokerage_modules()
    monkeypatch.setattr(os, "getenv", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("os.getenv must not be called at import time")))
    return importlib.import_module(name)


def test_operator_implementation_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    brokerage = _fresh_import("src.brokerage", monkeypatch)
    docs = (
        "PHASE10K8ZK4_OPERATOR_IMPLEMENTATION_PLAN.md",
        "LIVE_IMPLEMENTATION_WORK_BREAKDOWN_AFTER_10K8ZK4.md",
        "BROKER_INTEGRATION_TASK_GRAPH_AFTER_10K8ZK4.md",
        "IMPLEMENTATION_DEPENDENCY_GRAPH_AFTER_10K8ZK4.md",
    )
    for name in docs:
        assert (ROOT / name).exists(), name

    text = (ROOT / "PHASE10K8ZK4_OPERATOR_IMPLEMENTATION_PLAN.md").read_text(encoding="utf-8")
    text_lower = text.lower()
    for phrase in (
        "canonical path to preserve",
        "src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.live_submit -> broker adapter boundary",
        "broker adapter implementation sequence",
        "credential implementation sequence",
        "account implementation sequence",
        "order submission implementation sequence",
        "reconciliation implementation sequence",
        "monitoring implementation sequence",
        "rollback implementation sequence",
        "deployment implementation sequence",
        "no broker sdks.",
        "no credential loading.",
        "no network calls.",
    ):
        assert phrase in text_lower

    assert brokerage.build_default_kill_switch_state().clear is False
    assert brokerage.build_disabled_deployment_readiness().ready is False
    assert brokerage.build_disabled_enablement().live_enablement_allowed is False
    assert brokerage.get_execution_readiness({"instrument_id": "ABC", "quantity": 1, "side": "buy"}).live_trading_allowed is False
