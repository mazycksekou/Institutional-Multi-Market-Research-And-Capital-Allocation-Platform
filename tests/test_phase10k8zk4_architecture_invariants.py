from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DELETED_WRAPPERS = (
    "sharp_client.py",
    "providers/sharp_provider.py",
    "betting_providers/sharp_api.py",
    "betting_providers/the_odds_api.py",
    "betting_providers/sportsgameodds.py",
    "automation_scheduler/sharp_sportsbook_adapter.py",
    "automation_scheduler/sportsbook_odds_provider.py",
    "kalshi_client.py",
    "providers/kalshi_provider.py",
    "betting_providers/kalshi_api.py",
    "automation_scheduler/kalshi_readonly_adapter.py",
    "automation_scheduler/kalshi_market_provider.py",
    "automation_scheduler/settlement_rule_checker.py",
    "automation_scheduler/settlement_discovery.py",
    "automation_scheduler/audit_ledger.py",
    "automation_scheduler/institutional_audit_ledger.py",
    "automation_scheduler/strategy_performance_ledger.py",
    "automation_scheduler/broker_quality_scoring.py",
    "automation_scheduler/small_account_strategy.py",
    "automation_scheduler/manifold_no_bet_detector.py",
    "automation_scheduler/institutional_execution_desk.py",
    "automation_scheduler/execution_gatekeeper.py",
    "automation_scheduler/execution_authorization.py",
)


def _clear_brokerage_modules() -> None:
    for name in list(sys.modules):
        if name == "src.brokerage" or name.startswith("src.brokerage."):
            sys.modules.pop(name, None)


def _fresh_import(name: str, monkeypatch: pytest.MonkeyPatch):
    _clear_brokerage_modules()
    monkeypatch.setattr(os, "getenv", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("os.getenv must not be called at import time")))
    return importlib.import_module(name)


def test_architecture_invariants(monkeypatch: pytest.MonkeyPatch) -> None:
    brokerage = _fresh_import("src.brokerage", monkeypatch)
    docs = (
        "FINAL_ARCHITECTURE_INVARIANTS_AFTER_10K8ZK4.md",
        "CANONICAL_MODULE_OWNERSHIP_AFTER_10K8ZK4.md",
        "DISABLED_BOUNDARY_INVARIANTS_AFTER_10K8ZK4.md",
    )
    for name in docs:
        assert (ROOT / name).exists(), name

    invariants_text = (ROOT / "FINAL_ARCHITECTURE_INVARIANTS_AFTER_10K8ZK4.md").read_text(encoding="utf-8")
    assert "Canonical ownership is unchanged." in invariants_text
    assert "No alternate execution path is canonical." in invariants_text
    assert "No legacy wrappers are reintroduced." in invariants_text

    disabled_text = (ROOT / "DISABLED_BOUNDARY_INVARIANTS_AFTER_10K8ZK4.md").read_text(encoding="utf-8")
    assert "No alternate paper-only runtime path." in disabled_text

    assert brokerage.build_default_kill_switch_state().clear is False
    assert brokerage.build_disabled_enablement().live_enablement_allowed is False
    assert brokerage.build_disabled_deployment_readiness().ready is False

    live_submit = importlib.import_module("src.brokerage.live_submit")
    approval = importlib.import_module("src.brokerage.approval")
    client_factory = importlib.import_module("src.brokerage.client_factory")
    order = brokerage.build_order_request({"instrument_id": "ABC", "quantity": 1, "side": "buy"})
    with pytest.raises(live_submit.LiveSubmitDisabledError):
        live_submit.submit_live_order_disabled(
            order,
            approval_state=approval.ApprovalState(approval_id="approval_blocked", approved=False),
            broker_client_descriptor=client_factory.BrokerClientDescriptor(
                broker_name="sandbox-broker",
                client_name="disabled",
                environment="disabled",
            ),
        )

    for rel_path in DELETED_WRAPPERS:
        assert not (ROOT / rel_path).exists(), rel_path
