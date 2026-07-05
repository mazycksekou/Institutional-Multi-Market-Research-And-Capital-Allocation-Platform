"""Broker adapter protocol scaffold.

This module defines the live-shaped adapter contract without activating any
broker SDKs, network calls, or credential reads.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _coerce_text_tuple(values: Sequence[Any] | None) -> tuple[str, ...]:
    return tuple(str(value) for value in values or () if value not in (None, ""))


@dataclass(frozen=True, slots=True)
class BrokerAdapterDescriptor:
    """Local metadata describing a future broker adapter."""

    broker_name: str
    adapter_name: str = "disabled"
    provider_name: str | None = None
    adapter_type: str = "sandbox"
    environment: str = "disabled"
    approval_required: bool = True
    credentials_required: bool = True
    live_trading_allowed: bool = False
    sandbox_allowed: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class BrokerAdapterCapabilities:
    """Disabled capability matrix for future broker integrations."""

    supports_accounts: bool = False
    supports_positions: bool = False
    supports_orders: bool = False
    supports_submit: bool = False
    supports_reconciliation: bool = False
    supports_ledger_persistence: bool = False
    supports_sandbox: bool = True
    requires_approval: bool = True
    requires_credentials: bool = True
    live_trading_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class BrokerAdapterStatus:
    """Disabled broker-adapter readiness snapshot."""

    ready: bool
    status: str
    broker_adapter_descriptor: BrokerAdapterDescriptor
    capabilities: BrokerAdapterCapabilities
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    approval_required: bool = True
    credentials_required: bool = True
    live_trading_allowed: bool = False
    brokerage_boundary_disabled: bool = True
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["broker_adapter_descriptor"] = self.broker_adapter_descriptor.as_dict()
        payload["capabilities"] = self.capabilities.as_dict()
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class BrokerAccountInfo:
    """Local metadata for a future broker account."""

    account_id: str
    broker_name: str
    account_status: str = "disabled"
    cash_balance_hint: float | None = None
    buying_power_hint: float | None = None
    live_trading_enabled: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class BrokerPositionInfo:
    """Local metadata for a future broker position."""

    position_id: str
    account_id: str
    instrument_id: str
    quantity: float = 0.0
    average_price: float | None = None
    mark_price: float | None = None
    market_value: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True, slots=True)
class BrokerOrderInfo:
    """Local metadata for a future broker order."""

    order_id: str
    account_id: str
    instrument_id: str
    side: str
    quantity: float = 0.0
    order_status: str = "disabled"
    order_type: str = "market"
    limit_price: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


class DisabledBrokerAdapterError(RuntimeError):
    """Raised when broker-adapter behavior is requested while disabled."""


class BrokerAdapter(Protocol):
    """Live-shaped protocol for future broker adapters."""

    def describe(self) -> BrokerAdapterDescriptor: ...

    def get_capabilities(self) -> BrokerAdapterCapabilities: ...

    def get_status(self) -> BrokerAdapterStatus: ...

    def get_account_info(self) -> BrokerAccountInfo | None: ...

    def get_positions(self) -> tuple[BrokerPositionInfo, ...]: ...

    def get_orders(self) -> tuple[BrokerOrderInfo, ...]: ...

    def submit_order(self, order_request: Mapping[str, Any]) -> BrokerOrderInfo: ...


def build_adapter_descriptor(
    *,
    broker_name: str,
    adapter_name: str = "disabled",
    provider_name: str | None = None,
    adapter_type: str = "sandbox",
    environment: str = "disabled",
    approval_required: bool = True,
    credentials_required: bool = True,
    live_trading_allowed: bool = False,
    sandbox_allowed: bool = True,
    metadata: Mapping[str, Any] | None = None,
) -> BrokerAdapterDescriptor:
    return BrokerAdapterDescriptor(
        broker_name=str(broker_name),
        adapter_name=str(adapter_name),
        provider_name=str(provider_name) if provider_name is not None else None,
        adapter_type=str(adapter_type),
        environment=str(environment),
        approval_required=bool(approval_required),
        credentials_required=bool(credentials_required),
        live_trading_allowed=bool(live_trading_allowed),
        sandbox_allowed=bool(sandbox_allowed),
        metadata=dict(metadata or {}),
    )


def build_adapter_capabilities(
    *,
    supports_accounts: bool = False,
    supports_positions: bool = False,
    supports_orders: bool = False,
    supports_submit: bool = False,
    supports_reconciliation: bool = False,
    supports_ledger_persistence: bool = False,
    supports_sandbox: bool = True,
    requires_approval: bool = True,
    requires_credentials: bool = True,
    live_trading_allowed: bool = False,
    metadata: Mapping[str, Any] | None = None,
) -> BrokerAdapterCapabilities:
    return BrokerAdapterCapabilities(
        supports_accounts=bool(supports_accounts),
        supports_positions=bool(supports_positions),
        supports_orders=bool(supports_orders),
        supports_submit=bool(supports_submit),
        supports_reconciliation=bool(supports_reconciliation),
        supports_ledger_persistence=bool(supports_ledger_persistence),
        supports_sandbox=bool(supports_sandbox),
        requires_approval=bool(requires_approval),
        requires_credentials=bool(requires_credentials),
        live_trading_allowed=bool(live_trading_allowed),
        metadata=dict(metadata or {}),
    )


def build_disabled_adapter_status(
    *,
    broker_name: str,
    adapter_name: str = "disabled",
    provider_name: str | None = None,
    adapter_type: str = "sandbox",
    environment: str = "disabled",
    blockers: Sequence[str] | None = None,
    warnings: Sequence[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> BrokerAdapterStatus:
    descriptor = build_adapter_descriptor(
        broker_name=broker_name,
        adapter_name=adapter_name,
        provider_name=provider_name,
        adapter_type=adapter_type,
        environment=environment,
        metadata=metadata,
    )
    capabilities = build_adapter_capabilities(metadata=metadata)
    blocker_items = (
        "broker_adapter_boundary_disabled",
        "approval_required",
        "credentials_required",
        "live_trading_disabled",
        *tuple(str(item) for item in blockers or () if item),
    )
    warning_items = _coerce_text_tuple(warnings)
    return BrokerAdapterStatus(
        ready=False,
        status="disabled",
        broker_adapter_descriptor=descriptor,
        capabilities=capabilities,
        blockers=tuple(dict.fromkeys(blocker_items)),
        warnings=warning_items,
        approval_required=True,
        credentials_required=True,
        live_trading_allowed=False,
        brokerage_boundary_disabled=True,
        metadata=dict(metadata or {}),
    )


__all__ = [
    "BrokerAdapter",
    "BrokerAdapterCapabilities",
    "BrokerAdapterDescriptor",
    "BrokerAdapterStatus",
    "BrokerAccountInfo",
    "BrokerOrderInfo",
    "BrokerPositionInfo",
    "DisabledBrokerAdapterError",
    "build_adapter_capabilities",
    "build_adapter_descriptor",
    "build_disabled_adapter_status",
]
