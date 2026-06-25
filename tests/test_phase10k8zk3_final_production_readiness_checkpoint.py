from __future__ import annotations

import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_final_production_readiness_checkpoint() -> None:
    docs = (
        "PHASE10K8ZK3_FINAL_PRODUCTION_READINESS_CHECKPOINT.md",
        "POST_FINAL_SYSTEM_FREEZE_ARCHITECTURE_MAP_AFTER_10K8ZK3.md",
        "FINAL_REMAINING_ACTIVATION_QUEUE_AFTER_10K8ZK3.md",
        "NEXT_OPERATOR_APPROVED_LIVE_IMPLEMENTATION_PLAN_AFTER_10K8ZK3.md",
    )
    for name in docs:
        assert (ROOT / name).exists(), name

    checkpoint_text = (ROOT / "PHASE10K8ZK3_FINAL_PRODUCTION_READINESS_CHECKPOINT.md").read_text(encoding="utf-8")
    assert "final system freeze: complete" in checkpoint_text.lower()
    assert "production deployment: blocked" in checkpoint_text.lower()
    assert "live trading remains impossible in this phase." in checkpoint_text.lower()

    queue_text = (ROOT / "FINAL_REMAINING_ACTIVATION_QUEUE_AFTER_10K8ZK3.md").read_text(encoding="utf-8")
    for phrase in (
        "manual approval",
        "kill-switch clearance",
        "credential loading",
        "broker client creation",
        "broker account creation",
        "live order submission",
        "live position reconciliation",
        "live ledger persistence",
        "monitoring",
        "alerting",
        "rollback readiness",
        "production deployment approval",
    ):
        assert phrase in queue_text, phrase

    brokerage = importlib.import_module("src.brokerage")
    assert brokerage.get_execution_readiness({"instrument_id": "ABC", "quantity": 1, "side": "buy"}).live_trading_allowed is False
    assert brokerage.build_disabled_credential_readiness(broker_name="sandbox-broker").ready is False
    assert brokerage.build_disabled_deployment_readiness().ready is False
    assert brokerage.build_default_kill_switch_state().clear is False
