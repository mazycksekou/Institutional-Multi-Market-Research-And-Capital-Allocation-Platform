from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "PHASE10K8ZIB_UNIFIED_BROKERAGE_BOUNDARY.md",
    ROOT / "UNIFIED_EXECUTION_ARCHITECTURE_AFTER_10K8ZIB.md",
    ROOT / "BROKERAGE_CONTRACTS_AFTER_10K8ZIB.md",
    ROOT / "BROKERAGE_DISABLED_BEHAVIOR_AFTER_10K8ZIB.md",
]


def test_brokerage_docs_state_the_disabled_boundary() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    for phrase in [
        "DisabledBrokerageError",
        "DisabledExecutionError",
        "OrderSide",
        "OrderType",
        "OrderTimeInForce",
        "OrderStatus",
        "ExecutionMode",
        "OrderRequest",
        "ExecutionRequest",
        "ExecutionResult",
        "PositionSnapshot",
        "LedgerEvent",
        "ExecutionReadiness",
        "submit_order_disabled() always raises",
        "disabled broker boundary",
        "No paper-only canonical path exists",
    ]:
        assert phrase in text


def test_brokerage_boundary_imports_and_builders_are_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no env reads")))
    brokerage = importlib.import_module("src.brokerage")
    contracts = importlib.import_module("src.brokerage.contracts")
    orders = importlib.import_module("src.brokerage.orders")
    execution = importlib.import_module("src.brokerage.execution")
    positions = importlib.import_module("src.brokerage.positions")
    ledger = importlib.import_module("src.brokerage.ledger")
    readiness = importlib.import_module("src.brokerage.readiness")

    assert brokerage.DisabledBrokerageError is contracts.DisabledBrokerageError
    assert brokerage.OrderRequest is contracts.OrderRequest
    assert brokerage.ExecutionRequest is contracts.ExecutionRequest
    assert brokerage.LedgerEvent is contracts.LedgerEvent

    order_request = orders.build_order_request(
        {
            "ticker": "TEST",
            "stake": 25,
            "american_odds": -110,
            "decision_id": "decision-1",
            "provider": "demo",
        }
    )
    execution_request = orders.build_execution_request(order_request)
    position_snapshot = positions.build_position_snapshot({"ticker": "TEST", "quantity": 3, "average_price": 1.25})
    event_payload = ledger.record_ledger_event(
        event_type="unit_test_event",
        subject_id="test-1",
        payload={"order_request": order_request.as_dict()},
    )
    readiness_result = readiness.get_execution_readiness(order_request, execution_request=execution_request, position_snapshot=position_snapshot)

    assert order_request.instrument_id == "TEST"
    assert order_request.order_type.value in {"market", "limit", "stop", "stop_limit"}
    assert execution_request.execution_mode.value == "disabled"
    assert position_snapshot.instrument_id == "TEST"
    assert event_payload["event_type"] == "unit_test_event"
    assert readiness_result.ready is False
    assert "broker_boundary_disabled" in readiness_result.blockers


def test_submit_order_disabled_always_raises() -> None:
    execution = importlib.import_module("src.brokerage.execution")
    order_request = importlib.import_module("src.brokerage.orders").build_order_request({"ticker": "TEST", "stake": 25})
    with pytest.raises(execution.DisabledExecutionError):
        execution.submit_order_disabled(order_request)
