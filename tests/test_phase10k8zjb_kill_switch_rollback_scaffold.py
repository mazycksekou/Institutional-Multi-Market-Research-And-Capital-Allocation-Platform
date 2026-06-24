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


def test_kill_switch_and_rollback_docs_exist_and_describe_disabled_behavior() -> None:
    docs = [
        ROOT / "PHASE10K8ZJB_KILL_SWITCH_ROLLBACK_SCAFFOLD.md",
        ROOT / "KILL_SWITCH_DISABLED_BEHAVIOR_AFTER_10K8ZJB.md",
        ROOT / "ROLLBACK_PLAN_AFTER_10K8ZJB.md",
    ]
    for path in docs:
        assert path.is_file(), path
    text = "\n".join(path.read_text(encoding="utf-8") for path in docs).lower()
    for phrase in [
        "default kill switch blocks live activation",
        "Rollback plan is metadata only",
        "live trading remains disabled",
    ]:
        assert phrase.lower() in text


def test_kill_switch_scaffold_blocks_by_default_and_builds_metadata_only_rollback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = _fresh_import("src.brokerage")
    kill_switch = _fresh_import("src.brokerage.kill_switch")
    rollback = _fresh_import("src.brokerage.rollback")

    default_state = kill_switch.build_default_kill_switch_state()
    assert default_state.clear is False
    with pytest.raises(kill_switch.KillSwitchTriggeredError):
        kill_switch.require_kill_switch_clear(default_state)

    clear_state = kill_switch.KillSwitchState(kill_switch_id="kill-switch-clear", clear=True, status="clear", reason="approval-granted")
    assert kill_switch.require_kill_switch_clear(clear_state) == clear_state

    rollback_plan = rollback.build_rollback_plan(
        rollback_id="rollback-1",
        reason="future_live_activation",
        steps=("disable orders", "notify owners"),
    )
    assert rollback_plan.status == "metadata_only"
    assert rollback_plan.reason == "future_live_activation"
    assert rollback_plan.steps == ("disable orders", "notify owners")
    assert brokerage.KillSwitchState.__module__ == "src.brokerage.kill_switch"
