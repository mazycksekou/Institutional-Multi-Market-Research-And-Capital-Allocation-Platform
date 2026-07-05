"""Disabled broker position reconciliation descriptors and helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .contracts import DisabledBrokerageError, PositionSnapshot
from .positions import build_position_snapshot


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_positions(values: Sequence[PositionSnapshot | Mapping[str, Any]] | None) -> tuple[PositionSnapshot, ...]:
    items: list[PositionSnapshot] = []
    for value in values or ():
        if isinstance(value, PositionSnapshot):
            items.append(value)
        elif isinstance(value, Mapping):
            items.append(build_position_snapshot(value))
    return tuple(items)


@dataclass(frozen=True, slots=True)
class PositionReconciliationRequest:
    """Local reconciliation request descriptor."""

    reconciliation_id: str
    account_id: str | None = None
    broker_name: str | None = None
    portfolio_id: str | None = None
    current_positions: tuple[PositionSnapshot, ...] = ()
    target_positions: tuple[PositionSnapshot, ...] = ()
    cash_balance_hint: float | None = None
    buying_power_hint: float | None = None
    margin_enabled: bool | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["current_positions"] = [item.as_dict() for item in self.current_positions]
        payload["target_positions"] = [item.as_dict() for item in self.target_positions]
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class PositionReconciliationResult:
    """Disabled reconciliation result snapshot."""

    ready: bool
    status: str
    request: PositionReconciliationRequest | None = None
    position_deltas: tuple[dict[str, Any], ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    brokerage_boundary_disabled: bool = True
    live_reconciliation_allowed: bool = False
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict() if self.request is not None else None
        payload["position_deltas"] = [dict(item) for item in self.position_deltas]
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


def build_reconciliation_request(
    current_positions: Sequence[PositionSnapshot | Mapping[str, Any]] | None = None,
    target_positions: Sequence[PositionSnapshot | Mapping[str, Any]] | None = None,
    *,
    account_id: str | None = None,
    broker_name: str | None = None,
    portfolio_id: str | None = None,
    cash_balance_hint: float | None = None,
    buying_power_hint: float | None = None,
    margin_enabled: bool | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> PositionReconciliationRequest:
    return PositionReconciliationRequest(
        reconciliation_id=f"recon_{uuid4().hex[:16]}",
        account_id=account_id,
        broker_name=broker_name,
        portfolio_id=portfolio_id,
        current_positions=_coerce_positions(current_positions),
        target_positions=_coerce_positions(target_positions),
        cash_balance_hint=cash_balance_hint,
        buying_power_hint=buying_power_hint,
        margin_enabled=margin_enabled,
        metadata=dict(metadata or {}),
    )


def _coerce_request(request: PositionReconciliationRequest | Mapping[str, Any] | None) -> PositionReconciliationRequest | None:
    if request is None:
        return None
    if isinstance(request, PositionReconciliationRequest):
        return request
    if not isinstance(request, Mapping):
        return None
    current_positions = request.get("current_positions")
    target_positions = request.get("target_positions")
    return build_reconciliation_request(
        current_positions if isinstance(current_positions, Sequence) and not isinstance(current_positions, (str, bytes)) else None,
        target_positions if isinstance(target_positions, Sequence) and not isinstance(target_positions, (str, bytes)) else None,
        account_id=request.get("account_id"),
        broker_name=request.get("broker_name"),
        portfolio_id=request.get("portfolio_id"),
        cash_balance_hint=request.get("cash_balance_hint"),
        buying_power_hint=request.get("buying_power_hint"),
        margin_enabled=request.get("margin_enabled"),
        metadata=request.get("metadata") if isinstance(request.get("metadata"), Mapping) else None,
    )


def reconcile_positions_disabled(
    request: PositionReconciliationRequest | Mapping[str, Any] | None = None,
    *,
    reason: str | None = None,
) -> dict[str, Any]:
    message = reason or "position reconciliation is disabled until live trading approval is explicitly granted"
    request = _coerce_request(request)
    raise DisabledBrokerageError(
        f"{message}; request_present={bool(request is not None)}"
    )


__all__ = [
    "PositionReconciliationRequest",
    "PositionReconciliationResult",
    "build_reconciliation_request",
    "reconcile_positions_disabled",
]
