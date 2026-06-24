"""Disabled broker client factory scaffold."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .approval import ApprovalGateStatus, ApprovalState, evaluate_approval_gate
from .contracts import DisabledBrokerageError


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class BrokerClientDescriptor:
    """Local metadata describing a future broker client."""

    broker_name: str
    approval_state_id: str | None = None
    client_name: str = "disabled"
    environment: str = "disabled"
    account_id: str | None = None
    approval_required: bool = True
    live_trading_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class BrokerClientFactoryStatus:
    """Disabled broker-client factory status snapshot."""

    ready: bool
    status: str
    approval_state: ApprovalState
    approval_gate: ApprovalGateStatus
    broker_client_descriptor: BrokerClientDescriptor
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    brokerage_boundary_disabled: bool = True
    client_creation_allowed: bool = False
    live_trading_allowed: bool = False
    approval_required: bool = True
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_state"] = self.approval_state.as_dict()
        payload["approval_gate"] = self.approval_gate.as_dict()
        payload["broker_client_descriptor"] = self.broker_client_descriptor.as_dict()
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


class DisabledBrokerClientError(DisabledBrokerageError):
    """Raised when broker-client creation is attempted against the disabled boundary."""


def _coerce_approval_state(state: ApprovalState | Mapping[str, Any]) -> ApprovalState:
    if isinstance(state, ApprovalState):
        return state
    if isinstance(state, Mapping):
        return ApprovalState(
            approval_id=str(state.get("approval_id") or state.get("state_id") or "live_activation_state"),
            status=str(state.get("status") or "disabled"),
            approved=bool(state.get("approved", False)),
            denied=bool(state.get("denied", False)),
            approval_scope=str(state.get("approval_scope") or "live_activation"),
            approval_source=str(state.get("approval_source") or "local"),
            metadata=dict(state.get("metadata") or {k: v for k, v in state.items() if v is not None}),
        )
    raise TypeError("approval_state must be an ApprovalState or mapping")


def build_broker_client_descriptor(
    approval_state: ApprovalState | Mapping[str, Any],
    *,
    broker_name: str,
    account_id: str | None = None,
    client_name: str = "disabled",
    environment: str = "disabled",
    metadata: Mapping[str, Any] | None = None,
) -> BrokerClientDescriptor:
    state = _coerce_approval_state(approval_state)
    return BrokerClientDescriptor(
        broker_name=str(broker_name),
        approval_state_id=state.approval_id,
        client_name=client_name,
        environment=environment,
        account_id=account_id,
        approval_required=True,
        live_trading_allowed=False,
        metadata=dict(metadata or {}),
    )


def build_disabled_broker_client_status(
    approval_state: ApprovalState | Mapping[str, Any],
    *,
    broker_name: str,
    account_id: str | None = None,
    client_name: str = "disabled",
    environment: str = "disabled",
    metadata: Mapping[str, Any] | None = None,
) -> BrokerClientFactoryStatus:
    state = _coerce_approval_state(approval_state)
    approval_gate = evaluate_approval_gate(state)
    descriptor = build_broker_client_descriptor(
        state,
        broker_name=broker_name,
        account_id=account_id,
        client_name=client_name,
        environment=environment,
        metadata=metadata,
    )
    blockers = tuple(
        dict.fromkeys(
            [
                "brokerage_boundary_disabled",
                "client_creation_disabled",
                *approval_gate.blockers,
            ]
        )
    )
    status = "approved_local_only" if approval_gate.ready else approval_gate.status
    return BrokerClientFactoryStatus(
        ready=approval_gate.ready,
        status=status,
        approval_state=state,
        approval_gate=approval_gate,
        broker_client_descriptor=descriptor,
        blockers=blockers,
        warnings=approval_gate.warnings,
        brokerage_boundary_disabled=True,
        client_creation_allowed=False,
        live_trading_allowed=False,
        approval_required=True,
        metadata=dict(metadata or {}),
    )


def create_broker_client_disabled(
    approval_state: ApprovalState | Mapping[str, Any],
    *,
    broker_name: str,
    account_id: str | None = None,
    client_name: str = "disabled",
    environment: str = "disabled",
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    status = build_disabled_broker_client_status(
        approval_state,
        broker_name=broker_name,
        account_id=account_id,
        client_name=client_name,
        environment=environment,
        metadata=metadata,
    )
    raise DisabledBrokerClientError(
        f"broker client creation is disabled in this phase; status={status.status}; broker={broker_name}; account_id={account_id or 'unknown'}"
    )


__all__ = [
    "BrokerClientDescriptor",
    "BrokerClientFactoryStatus",
    "DisabledBrokerClientError",
    "build_broker_client_descriptor",
    "build_disabled_broker_client_status",
    "create_broker_client_disabled",
]
