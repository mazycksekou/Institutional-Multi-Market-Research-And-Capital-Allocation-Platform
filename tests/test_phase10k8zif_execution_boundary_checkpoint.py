from __future__ import annotations

import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_execution_boundary_checkpoint_docs_state_disabled_brokerage() -> None:
    text = (ROOT / "PHASE10K8ZIF_EXECUTION_BOUNDARY_CHECKPOINT.md").read_text(encoding="utf-8")
    for phrase in [
        "src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary",
        "Broker submit is disabled.",
        "Live trading remains impossible.",
        "No separate paper-only canonical path exists.",
    ]:
        assert phrase in text


def test_execution_boundary_imports_remain_disabled() -> None:
    brokerage = importlib.import_module("src.brokerage")
    execution = importlib.import_module("src.brokerage.execution")
    readiness = importlib.import_module("src.brokerage.readiness")
    plan = importlib.import_module("src.services.decision_engine").build_brokerage_execution_plan(
        {"ticker": "XYZ", "stake": 5, "american_odds": -110, "decision_id": "d2", "provider": "demo"}
    )
    with pytest.raises(Exception):
        brokerage.submit_order_disabled(plan["execution_request"])
    with pytest.raises(Exception):
        execution.submit_order_disabled(plan["execution_request"])
    assert readiness.get_execution_readiness(plan["order_request"]).ready is False

