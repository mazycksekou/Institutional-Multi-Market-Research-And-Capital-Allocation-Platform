"""Disabled execution helpers that keep the broker boundary production-shaped."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import DisabledBrokerageError, DisabledExecutionError, ExecutionMode, ExecutionResult, OrderRequest, OrderStatus
from .ledger import record_ledger_event
from .orders import build_execution_request, build_order_request
from .readiness import get_execution_readiness


def build_disabled_execution_result(
    order_request: OrderRequest | Mapping[str, Any] | None = None,
    *,
    execution_request: Mapping[str, Any] | None = None,
    reason: str = "brokerage_boundary_disabled",
    blocked_reasons: list[str] | tuple[str, ...] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ExecutionResult:
    order = build_order_request(order_request) if not isinstance(order_request, OrderRequest) else order_request
    execution = build_execution_request(order, candidate=execution_request, execution_mode=ExecutionMode.DISABLED)
    readiness = get_execution_readiness(order, execution_request=execution)
    reasons = tuple(dict.fromkeys([reason, *(blocked_reasons or []), *readiness.blockers]))
    ledger_event = record_ledger_event(
        event_type="brokerage_execution_blocked",
        subject_id=order.order_id,
        payload={
            "order_request": order.as_dict(),
            "execution_request": execution.as_dict(),
            "reason": reason,
            "blocked_reasons": list(reasons),
        },
        metadata=dict(metadata or {}),
    )
    return ExecutionResult(
        execution_id=execution.execution_id,
        order_request=order,
        execution_mode=ExecutionMode.DISABLED,
        status=OrderStatus.DISABLED,
        blocked=True,
        blocked_reasons=reasons,
        message="brokerage boundary is disabled",
        broker_order_id=None,
        ledger_event=None,
        metadata={
            "readiness": readiness.as_dict(),
            "ledger_event": ledger_event,
            **dict(metadata or {}),
        },
    )


def submit_order_disabled(
    order_request: OrderRequest | Mapping[str, Any] | None = None,
    *,
    execution_request: Mapping[str, Any] | None = None,
    reason: str = "brokerage_boundary_disabled",
    blocked_reasons: list[str] | tuple[str, ...] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ExecutionResult:
    result = build_disabled_execution_result(
        order_request,
        execution_request=execution_request,
        reason=reason,
        blocked_reasons=blocked_reasons,
        metadata=metadata,
    )
    raise DisabledExecutionError(f"{result.message}: {', '.join(result.blocked_reasons)}")


__all__ = [
    "DisabledBrokerageError",
    "DisabledExecutionError",
    "build_disabled_execution_result",
    "submit_order_disabled",
]
