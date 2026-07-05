"""Disabled live-ledger persistence scaffold."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .approval import ApprovalState, evaluate_approval_gate
from .client_factory import BrokerClientDescriptor


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_approval_state(approval_state: ApprovalState | Mapping[str, Any]) -> ApprovalState:
    if isinstance(approval_state, ApprovalState):
        return approval_state
    if isinstance(approval_state, Mapping):
        return ApprovalState(
            approval_id=str(approval_state.get("approval_id") or approval_state.get("state_id") or "live_activation_state"),
            status=str(approval_state.get("status") or "disabled"),
            approved=bool(approval_state.get("approved", False)),
            denied=bool(approval_state.get("denied", False)),
            approval_scope=str(approval_state.get("approval_scope") or "live_activation"),
            approval_source=str(approval_state.get("approval_source") or "local"),
            metadata=dict(approval_state.get("metadata") or {k: v for k, v in approval_state.items() if v is not None}),
        )
    raise TypeError("approval_state must be an ApprovalState or mapping")


def _coerce_descriptor(descriptor: BrokerClientDescriptor | Mapping[str, Any]) -> BrokerClientDescriptor:
    from .client_factory import BrokerClientDescriptor as _BrokerClientDescriptor

    if isinstance(descriptor, _BrokerClientDescriptor):
        return descriptor
    if isinstance(descriptor, Mapping):
        return _BrokerClientDescriptor(
            broker_name=str(descriptor.get("broker_name") or descriptor.get("broker") or "unknown"),
            approval_state_id=descriptor.get("approval_state_id"),
            client_name=str(descriptor.get("client_name") or "disabled"),
            environment=str(descriptor.get("environment") or "disabled"),
            account_id=descriptor.get("account_id"),
            approval_required=bool(descriptor.get("approval_required", True)),
            live_trading_allowed=bool(descriptor.get("live_trading_allowed", False)),
            metadata=dict(descriptor.get("metadata") or {k: v for k, v in descriptor.items() if v is not None}),
        )
    raise TypeError("broker_client_descriptor must be a BrokerClientDescriptor or mapping")


@dataclass(frozen=True, slots=True)
class LiveLedgerPersistencePlan:
    """Local-only live ledger persistence metadata."""

    persistence_id: str
    approval_state: ApprovalState
    broker_client_descriptor: BrokerClientDescriptor
    ledger_namespace: str = "live_execution"
    ledger_event: dict[str, Any] | None = None
    approval_gate_status: str = "disabled"
    live_persistence_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_state"] = self.approval_state.as_dict()
        payload["broker_client_descriptor"] = self.broker_client_descriptor.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


class LiveLedgerPersistenceDisabledError(RuntimeError):
    """Raised when live ledger persistence is requested while disabled."""


def build_live_ledger_persistence_plan(
    *,
    approval_state: ApprovalState | Mapping[str, Any],
    broker_client_descriptor: BrokerClientDescriptor | Mapping[str, Any],
    ledger_namespace: str = "live_execution",
    ledger_event: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> LiveLedgerPersistencePlan:
    approval = _coerce_approval_state(approval_state)
    descriptor = _coerce_descriptor(broker_client_descriptor)
    gate = evaluate_approval_gate(approval)
    return LiveLedgerPersistencePlan(
        persistence_id=f"live_ledger_{descriptor.broker_name}",
        approval_state=approval,
        broker_client_descriptor=descriptor,
        ledger_namespace=str(ledger_namespace),
        ledger_event=dict(ledger_event or {}) if ledger_event is not None else None,
        approval_gate_status=gate.status,
        live_persistence_allowed=False,
        metadata=dict(metadata or {}),
    )


def persist_live_ledger_disabled(
    *,
    approval_state: ApprovalState | Mapping[str, Any],
    broker_client_descriptor: BrokerClientDescriptor | Mapping[str, Any],
    ledger_namespace: str = "live_execution",
    ledger_event: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    plan = build_live_ledger_persistence_plan(
        approval_state=approval_state,
        broker_client_descriptor=broker_client_descriptor,
        ledger_namespace=ledger_namespace,
        ledger_event=ledger_event,
        metadata=metadata,
    )
    raise LiveLedgerPersistenceDisabledError(
        f"live ledger persistence is disabled in this phase; persistence_id={plan.persistence_id}; approval_gate_status={plan.approval_gate_status}"
    )


__all__ = [
    "LiveLedgerPersistenceDisabledError",
    "LiveLedgerPersistencePlan",
    "build_live_ledger_persistence_plan",
    "persist_live_ledger_disabled",
]
