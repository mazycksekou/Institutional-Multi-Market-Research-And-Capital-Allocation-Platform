"""Dry-run execution proof helpers.

These helpers use the canonical brokerage contracts, stop before the broker
adapter boundary, and only create local ledger events.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .contracts import ExecutionMode, ExecutionRequest, LedgerEvent, OrderRequest
from .ledger import record_ledger_event
from .orders import build_execution_request, build_order_request


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _to_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "as_dict"):
        candidate = value.as_dict()
        if isinstance(candidate, Mapping):
            return dict(candidate)
    payload: dict[str, Any] = {}
    for name in ("dry_run_id", "order_request", "execution_request", "ledger_event", "metadata"):
        if hasattr(value, name):
            payload[name] = getattr(value, name)
    return payload


@dataclass(frozen=True, slots=True)
class DryRunLedgerEvent:
    """Local-only dry-run ledger event."""

    event_id: str
    event_type: str
    subject_id: str
    order_request: OrderRequest
    execution_request: ExecutionRequest
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["order_request"] = self.order_request.as_dict()
        payload["execution_request"] = self.execution_request.as_dict()
        payload["payload"] = dict(self.payload)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class DryRunOrder:
    """Canonical order and execution objects for a dry run."""

    dry_run_id: str
    order_request: OrderRequest
    execution_request: ExecutionRequest
    broker_adapter_reached: bool = False
    live_submit_allowed: bool = False
    status: str = "dry_run_only"
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["order_request"] = self.order_request.as_dict()
        payload["execution_request"] = self.execution_request.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class DryRunExecutionResult:
    """Dry-run execution result that stops before the broker adapter."""

    dry_run_id: str
    order_request: OrderRequest
    execution_request: ExecutionRequest
    ledger_event: DryRunLedgerEvent
    broker_adapter_reached: bool = False
    live_submit_allowed: bool = False
    submitted: bool = False
    status: str = "dry_run_only"
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["order_request"] = self.order_request.as_dict()
        payload["execution_request"] = self.execution_request.as_dict()
        payload["ledger_event"] = self.ledger_event.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


def build_dry_run_order(
    candidate: OrderRequest | Mapping[str, Any] | None = None,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> DryRunOrder:
    order_request = candidate if isinstance(candidate, OrderRequest) else build_order_request(candidate)
    execution_request = build_execution_request(order_request, execution_mode=ExecutionMode.DISABLED, metadata=metadata)
    return DryRunOrder(
        dry_run_id=f"dry_run_{order_request.order_id}",
        order_request=order_request,
        execution_request=execution_request,
        broker_adapter_reached=False,
        live_submit_allowed=False,
        metadata=dict(metadata or {}),
    )


def build_dry_run_ledger_event(
    order_request: OrderRequest | Mapping[str, Any] | None = None,
    *,
    execution_request: ExecutionRequest | Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DryRunLedgerEvent:
    order = order_request if isinstance(order_request, OrderRequest) else build_order_request(order_request)
    execution = execution_request if isinstance(execution_request, ExecutionRequest) else build_execution_request(order, candidate=execution_request if isinstance(execution_request, Mapping) else None)
    ledger_event = record_ledger_event(
        event_type="dry_run_execution",
        subject_id=order.order_id,
        payload={"dry_run_only": True, "broker_adapter_reached": False},
        metadata=dict(metadata or {}),
    )
    event = LedgerEvent(
        event_id=str(ledger_event["event_id"]),
        event_type=str(ledger_event["event_type"]),
        subject_id=str(ledger_event["subject_id"]),
        payload=dict(ledger_event.get("payload") or {}),
        metadata=dict(ledger_event.get("metadata") or {}),
    )
    return DryRunLedgerEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        subject_id=event.subject_id,
        order_request=order,
        execution_request=execution,
        payload=event.payload,
        metadata=event.metadata,
    )


def build_dry_run_execution(
    order_request: OrderRequest | Mapping[str, Any] | None = None,
    *,
    execution_request: ExecutionRequest | Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DryRunExecutionResult:
    dry_run_order = build_dry_run_order(order_request, metadata=metadata)
    execution = execution_request if isinstance(execution_request, ExecutionRequest) else build_execution_request(dry_run_order.order_request, candidate=execution_request if isinstance(execution_request, Mapping) else None, execution_mode=ExecutionMode.DISABLED, metadata=metadata)
    ledger_event = build_dry_run_ledger_event(dry_run_order.order_request, execution_request=execution, metadata=metadata)
    return DryRunExecutionResult(
        dry_run_id=dry_run_order.dry_run_id,
        order_request=dry_run_order.order_request,
        execution_request=execution,
        ledger_event=ledger_event,
        broker_adapter_reached=False,
        live_submit_allowed=False,
        submitted=False,
        status="dry_run_only",
        metadata=dict(metadata or {}),
    )


__all__ = [
    "DryRunExecutionResult",
    "DryRunLedgerEvent",
    "DryRunOrder",
    "build_dry_run_execution",
    "build_dry_run_ledger_event",
    "build_dry_run_order",
]

