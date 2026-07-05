"""Disabled live-reconciliation interface scaffold."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .approval import ApprovalState, evaluate_approval_gate
from .client_factory import BrokerClientDescriptor
from .contracts import PositionSnapshot
from .reconciliation import PositionReconciliationRequest, build_reconciliation_request


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
    if isinstance(descriptor, BrokerClientDescriptor):
        return descriptor
    if isinstance(descriptor, Mapping):
        return BrokerClientDescriptor(
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
class LiveReconciliationPlan:
    """Production-shaped live-reconciliation plan metadata."""

    reconciliation_id: str
    approval_state: ApprovalState
    broker_client_descriptor: BrokerClientDescriptor
    reconciliation_request: PositionReconciliationRequest
    approval_gate_status: str = "disabled"
    live_reconciliation_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_state"] = self.approval_state.as_dict()
        payload["broker_client_descriptor"] = self.broker_client_descriptor.as_dict()
        payload["reconciliation_request"] = self.reconciliation_request.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


class LiveReconciliationDisabledError(RuntimeError):
    """Raised when live position reconciliation is requested while disabled."""


def build_live_reconciliation_plan(
    current_positions: Sequence[PositionSnapshot | Mapping[str, Any]] | None = None,
    target_positions: Sequence[PositionSnapshot | Mapping[str, Any]] | None = None,
    *,
    approval_state: ApprovalState | Mapping[str, Any],
    broker_client_descriptor: BrokerClientDescriptor | Mapping[str, Any],
    account_id: str | None = None,
    broker_name: str | None = None,
    portfolio_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> LiveReconciliationPlan:
    approval = _coerce_approval_state(approval_state)
    descriptor = _coerce_descriptor(broker_client_descriptor)
    gate = evaluate_approval_gate(approval)
    request = build_reconciliation_request(
        current_positions,
        target_positions,
        account_id=account_id,
        broker_name=broker_name or descriptor.broker_name,
        portfolio_id=portfolio_id,
        metadata=dict(metadata or {}),
    )
    return LiveReconciliationPlan(
        reconciliation_id=f"live_recon_{request.reconciliation_id}",
        approval_state=approval,
        broker_client_descriptor=descriptor,
        reconciliation_request=request,
        approval_gate_status=gate.status,
        live_reconciliation_allowed=False,
        metadata=dict(metadata or {}),
    )


def reconcile_live_positions_disabled(
    current_positions: Sequence[PositionSnapshot | Mapping[str, Any]] | None = None,
    target_positions: Sequence[PositionSnapshot | Mapping[str, Any]] | None = None,
    *,
    approval_state: ApprovalState | Mapping[str, Any],
    broker_client_descriptor: BrokerClientDescriptor | Mapping[str, Any],
    account_id: str | None = None,
    broker_name: str | None = None,
    portfolio_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    plan = build_live_reconciliation_plan(
        current_positions,
        target_positions,
        approval_state=approval_state,
        broker_client_descriptor=broker_client_descriptor,
        account_id=account_id,
        broker_name=broker_name,
        portfolio_id=portfolio_id,
        metadata=metadata,
    )
    raise LiveReconciliationDisabledError(
        f"live reconciliation is disabled in this phase; reconciliation_id={plan.reconciliation_id}; approval_gate_status={plan.approval_gate_status}"
    )


__all__ = [
    "LiveReconciliationDisabledError",
    "LiveReconciliationPlan",
    "build_live_reconciliation_plan",
    "reconcile_live_positions_disabled",
]
