"""Production-shaped position snapshots for the disabled brokerage boundary."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import OrderSide, PositionSnapshot


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_position_snapshot(position: Mapping[str, Any] | None = None, *, metadata: Mapping[str, Any] | None = None) -> PositionSnapshot:
    payload = dict(position or {})
    instrument_id = str(
        payload.get("instrument_id")
        or payload.get("contract_id")
        or payload.get("ticker")
        or payload.get("symbol")
        or "unknown"
    )
    side_value = payload.get("side") or payload.get("position_side") or payload.get("direction")
    if isinstance(side_value, OrderSide):
        side = side_value
    else:
        text = str(side_value or "").strip().lower()
        side = OrderSide.SELL if text in {"sell", "short"} else OrderSide.BUY if text in {"buy", "long"} else text or None
    return PositionSnapshot(
        position_id=str(payload.get("position_id") or payload.get("account_position_id") or instrument_id),
        instrument_id=instrument_id,
        side=side,
        quantity=float(_to_float(payload.get("quantity"), 0.0) or 0.0),
        average_price=_to_float(payload.get("average_price") or payload.get("avg_price")),
        mark_price=_to_float(payload.get("mark_price") or payload.get("last_price")),
        market_value=_to_float(payload.get("market_value")),
        unrealized_pnl=_to_float(payload.get("unrealized_pnl")),
        realized_pnl=_to_float(payload.get("realized_pnl")),
        currency=str(payload.get("currency") or "USD"),
        account_id=str(payload.get("account_id") or payload.get("portfolio_id") or ""),
        portfolio_id=str(payload.get("portfolio_id") or payload.get("account_id") or ""),
        metadata=dict(metadata or {k: v for k, v in payload.items() if v is not None}),
    )
