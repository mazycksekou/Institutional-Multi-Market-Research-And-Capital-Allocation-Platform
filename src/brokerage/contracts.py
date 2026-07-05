"""Production-shaped brokerage contracts.

The brokerage boundary stays disabled in this phase, but the contracts are
live-shaped so future trading can plug in without changing upstream callers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _enum_value(value: Any) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


class DisabledBrokerageError(RuntimeError):
    """Raised when a brokerage action is requested while the boundary is disabled."""


class DisabledExecutionError(DisabledBrokerageError):
    """Raised when order submission is attempted against the disabled boundary."""


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderTimeInForce(str, Enum):
    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


class OrderStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    SUBMITTED = "submitted"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    DISABLED = "disabled"


class ExecutionMode(str, Enum):
    DISABLED = "disabled"
    SIMULATION = "simulation"
    LIVE = "live"


@dataclass(frozen=True)
class OrderRequest:
    order_id: str
    instrument_id: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    time_in_force: OrderTimeInForce = OrderTimeInForce.DAY
    limit_price: float | None = None
    stop_price: float | None = None
    provider: str | None = None
    symbol: str | None = None
    market_type: str | None = None
    decision_id: str | None = None
    strategy_id: str | None = None
    client_order_id: str | None = None
    reference_price: float | None = None
    expected_value: float | None = None
    risk_profile: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)
    status: OrderStatus = OrderStatus.READY

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["side"] = _enum_value(self.side)
        payload["order_type"] = _enum_value(self.order_type)
        payload["time_in_force"] = _enum_value(self.time_in_force)
        payload["status"] = _enum_value(self.status)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True)
class ExecutionRequest:
    execution_id: str
    order_request: OrderRequest
    execution_mode: ExecutionMode = ExecutionMode.DISABLED
    created_at: str = field(default_factory=_utc_now_iso)
    disabled_reason: str | None = None
    broker_name: str | None = None
    account_id: str | None = None
    client_execution_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["execution_mode"] = _enum_value(self.execution_mode)
        payload["order_request"] = self.order_request.as_dict()
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True)
class ExecutionResult:
    execution_id: str
    order_request: OrderRequest
    execution_mode: ExecutionMode = ExecutionMode.DISABLED
    status: OrderStatus = OrderStatus.DISABLED
    blocked: bool = True
    blocked_reasons: tuple[str, ...] = ()
    message: str | None = None
    broker_order_id: str | None = None
    ledger_event: "LedgerEvent | None" = None
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["execution_mode"] = _enum_value(self.execution_mode)
        payload["status"] = _enum_value(self.status)
        payload["order_request"] = self.order_request.as_dict()
        payload["ledger_event"] = self.ledger_event.as_dict() if self.ledger_event is not None else None
        payload["metadata"] = dict(self.metadata)
        payload["blocked_reasons"] = list(self.blocked_reasons)
        return payload


@dataclass(frozen=True)
class PositionSnapshot:
    position_id: str
    instrument_id: str
    side: OrderSide | str | None = None
    quantity: float = 0.0
    average_price: float | None = None
    mark_price: float | None = None
    market_value: float | None = None
    unrealized_pnl: float | None = None
    realized_pnl: float | None = None
    currency: str = "USD"
    account_id: str | None = None
    portfolio_id: str | None = None
    created_at: str = field(default_factory=_utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["side"] = _enum_value(self.side) if self.side is not None else None
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True)
class LedgerEvent:
    event_id: str
    event_type: str
    subject_id: str
    created_at: str = field(default_factory=_utc_now_iso)
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["payload"] = dict(self.payload)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True)
class ExecutionReadiness:
    ready: bool
    status: str
    execution_mode: ExecutionMode = ExecutionMode.DISABLED
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    order_request: OrderRequest | None = None
    execution_request: ExecutionRequest | None = None
    position_snapshot: PositionSnapshot | None = None
    ledger_event: LedgerEvent | None = None
    brokerage_boundary_disabled: bool = True
    live_trading_allowed: bool = False
    account_required: bool = True
    credentials_required: bool = True

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["execution_mode"] = _enum_value(self.execution_mode)
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        payload["order_request"] = self.order_request.as_dict() if self.order_request is not None else None
        payload["execution_request"] = self.execution_request.as_dict() if self.execution_request is not None else None
        payload["position_snapshot"] = self.position_snapshot.as_dict() if self.position_snapshot is not None else None
        payload["ledger_event"] = self.ledger_event.as_dict() if self.ledger_event is not None else None
        return payload
