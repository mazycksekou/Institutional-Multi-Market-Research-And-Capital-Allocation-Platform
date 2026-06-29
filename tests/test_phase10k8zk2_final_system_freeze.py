from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DELETED_PATHS = (
    "sharp_client.py",
    "providers/sharp_provider.py",
    "betting_providers/sharp_api.py",
    "betting_providers/the_odds_api.py",
    "betting_providers/sportsgameodds.py",
    'src/automation_scheduler_legacy/sharp_sportsbook_adapter.py',
    'src/automation_scheduler_legacy/sportsbook_odds_provider.py',
    "kalshi_client.py",
    "providers/kalshi_provider.py",
    "betting_providers/kalshi_api.py",
    'src/automation_scheduler_legacy/kalshi_readonly_adapter.py',
    'src/automation_scheduler_legacy/kalshi_market_provider.py',
    'src/automation_scheduler_legacy/settlement_rule_checker.py',
    'src/automation_scheduler_legacy/settlement_discovery.py',
    'src/automation_scheduler_legacy/audit_ledger.py',
    'src/automation_scheduler_legacy/institutional_audit_ledger.py',
    'src/automation_scheduler_legacy/strategy_performance_ledger.py',
    'src/automation_scheduler_legacy/broker_quality_scoring.py',
    'src/automation_scheduler_legacy/small_account_strategy.py',
    'src/automation_scheduler_legacy/manifold_no_bet_detector.py',
    'src/automation_scheduler_legacy/institutional_execution_desk.py',
    'src/automation_scheduler_legacy/execution_gatekeeper.py',
    'src/automation_scheduler_legacy/execution_authorization.py',
)


def _clear_brokerage_modules() -> None:
    for name in list(sys.modules):
        if name == "src.brokerage" or name.startswith("src.brokerage."):
            sys.modules.pop(name, None)


def _fresh_import(name: str, monkeypatch: pytest.MonkeyPatch):
    _clear_brokerage_modules()
    monkeypatch.setattr(os, "getenv", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("os.getenv must not be called at import time")))
    return importlib.import_module(name)


def test_final_system_freeze(monkeypatch: pytest.MonkeyPatch) -> None:
    brokerage = _fresh_import("src.brokerage", monkeypatch)

    freeze_docs = (
        "PHASE10K8ZK2_FINAL_SYSTEM_FREEZE.md",
        "FINAL_CANONICAL_ARCHITECTURE_MAP_AFTER_10K8ZK2.md",
        "FINAL_DISABLED_BOUNDARY_MAP_AFTER_10K8ZK2.md",
        "FINAL_PRODUCTION_SHAPED_EXECUTION_PATH_AFTER_10K8ZK2.md",
    )
    for name in freeze_docs:
        assert (ROOT / name).exists(), name

    freeze_text = (ROOT / "PHASE10K8ZK2_FINAL_SYSTEM_FREEZE.md").read_text(encoding="utf-8")
    canonical_path = "src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.live_submit -> broker adapter boundary"
    assert canonical_path in freeze_text
    assert "No alternate paper-only execution path exists." in freeze_text
    assert "src.ai" in freeze_text
    assert "src.brokerage" in freeze_text

    assert hasattr(brokerage, "get_execution_readiness")
    assert hasattr(brokerage, "build_disabled_enablement")
    assert hasattr(brokerage, "build_sandbox_adapter")
    assert hasattr(brokerage, "build_default_kill_switch_policy")
    assert hasattr(brokerage, "build_default_deployment_policy")

    readiness = brokerage.get_execution_readiness({"instrument_id": "ABC", "quantity": 1, "side": "buy"})
    assert readiness.live_trading_allowed is False

    for rel_path in FORBIDDEN_DELETED_PATHS:
        assert not (ROOT / rel_path).exists(), rel_path
