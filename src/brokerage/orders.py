"""Production-shaped order request builders for the disabled brokerage boundary."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import ExecutionMode, ExecutionRequest, OrderRequest, OrderSide, OrderStatus, OrderTimeInForce, OrderType


def _first_text(payload: Mapping[str, Any], keys: tuple[str, ...], default: str = "unknown") -> str:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def _first_float(payload: Mapping[str, Any], keys: tuple[str, ...], default: float | None = None) -> float | None:
    for key in keys:
        value = payload.get(key)
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return default


def _normalize_side(value: Any) -> OrderSide:
    text = str(value or "").strip().lower()
    if text in {"sell", "short", "no"}:
        return OrderSide.SELL
    return OrderSide.BUY


def _normalize_order_type(value: Any, limit_price: float | None = None, stop_price: float | None = None) -> OrderType:
    text = str(value or "").strip().lower()
    if text in {"limit", "lmt"}:
        return OrderType.LIMIT
    if text in {"stop", "stp"}:
        return OrderType.STOP
    if text in {"stop_limit", "stop-limit", "stoplimit"}:
        return OrderType.STOP_LIMIT
    if limit_price is not None and stop_price is not None:
        return OrderType.STOP_LIMIT
    if limit_price is not None:
        return OrderType.LIMIT
    if stop_price is not None:
        return OrderType.STOP
    return OrderType.MARKET


def _normalize_tif(value: Any) -> OrderTimeInForce:
    text = str(value or "").strip().lower()
    if text in {"gtc", "good_till_cancelled", "good-til-cancelled"}:
        return OrderTimeInForce.GTC
    if text in {"ioc", "immediate_or_cancel"}:
        return OrderTimeInForce.IOC
    if text in {"fok", "fill_or_kill"}:
        return OrderTimeInForce.FOK
    return OrderTimeInForce.DAY


def build_order_request(
    candidate: Mapping[str, Any] | None = None,
    *,
    instrument_id: str | None = None,
    side: Any | None = None,
    quantity: Any | None = None,
    order_type: Any | None = None,
    time_in_force: Any | None = None,
    limit_price: Any | None = None,
    stop_price: Any | None = None,
    provider: str | None = None,
    symbol: str | None = None,
    market_type: str | None = None,
    decision_id: str | None = None,
    strategy_id: str | None = None,
    client_order_id: str | None = None,
    reference_price: Any | None = None,
    expected_value: Any | None = None,
    risk_profile: str | None = None,
    notes: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> OrderRequest:
    payload = dict(candidate or {})
    for key, value in {
        "instrument_id": instrument_id,
        "side": side,
        "quantity": quantity,
        "order_type": order_type,
        "time_in_force": time_in_force,
        "limit_price": limit_price,
        "stop_price": stop_price,
        "provider": provider,
        "symbol": symbol,
        "market_type": market_type,
        "decision_id": decision_id,
        "strategy_id": strategy_id,
        "client_order_id": client_order_id,
        "reference_price": reference_price,
        "expected_value": expected_value,
        "risk_profile": risk_profile,
        "notes": notes,
    }.items():
        if value is not None:
            payload[key] = value
    instrument = _first_text(payload, ("instrument_id", "contract_id", "ticker", "symbol", "event_id", "market_id"))
    limit = _first_float(payload, ("limit_price", "limit", "price_limit", "order_limit_price"))
    stop = _first_float(payload, ("stop_price", "stop", "price_stop"))
    side_value = _normalize_side(payload.get("side") or payload.get("action") or payload.get("order_action") or payload.get("direction"))
    qty = _first_float(payload, ("quantity", "size", "stake", "notional", "order_size"), default=0.0) or 0.0
    if qty < 0:
        qty = abs(qty)
    order_kind = _normalize_order_type(payload.get("order_type") or payload.get("execution_type"), limit_price=limit, stop_price=stop)
    tif = _normalize_tif(payload.get("time_in_force") or payload.get("tif"))
    client_id = str(payload.get("client_order_id") or payload.get("order_id") or payload.get("decision_id") or instrument)
    metadata_payload = dict(metadata or {})
    for key, value in payload.items():
        if key in {"candidate", "metadata"} or value is None:
            continue
        metadata_payload.setdefault(str(key), value)
    return OrderRequest(
        order_id=client_id,
        instrument_id=instrument,
        side=side_value,
        quantity=float(qty),
        order_type=order_kind,
        time_in_force=tif,
        limit_price=limit,
        stop_price=stop,
        provider=str(payload.get("provider") or "unknown"),
        symbol=str(payload.get("symbol") or payload.get("ticker") or instrument),
        market_type=str(payload.get("market_type") or payload.get("market") or "unknown"),
        decision_id=str(payload.get("decision_id") or "") or None,
        strategy_id=str(payload.get("strategy_id") or "") or None,
        client_order_id=client_id,
        reference_price=_first_float(payload, ("reference_price", "fair_price", "expected_price")),
        expected_value=_first_float(payload, ("expected_value", "ev", "expected_ev")),
        risk_profile=str(payload.get("risk_profile") or "standard"),
        notes=str(payload.get("notes") or ""),
        metadata=metadata_payload,
        status=OrderStatus.READY,
    )


def build_execution_request(
    order_request: OrderRequest | Mapping[str, Any] | None = None,
    *,
    candidate: Mapping[str, Any] | None = None,
    execution_mode: ExecutionMode | str = ExecutionMode.DISABLED,
    broker_name: str | None = None,
    account_id: str | None = None,
    client_execution_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ExecutionRequest:
    if not isinstance(order_request, OrderRequest):
        order_request = build_order_request(order_request if isinstance(order_request, Mapping) else candidate)
    if isinstance(execution_mode, ExecutionMode):
        mode = execution_mode
    else:
        mode_text = str(execution_mode or "").strip().lower()
        mode = ExecutionMode(mode_text) if mode_text in ExecutionMode._value2member_map_ else ExecutionMode.DISABLED
    execution_id = client_execution_id or str(
        (candidate or {}).get("execution_id")
        or (candidate or {}).get("request_id")
        or order_request.client_order_id
        or f"exec_{order_request.order_id}"
    )
    metadata_payload = dict(metadata or {})
    if candidate:
        metadata_payload.setdefault("candidate", dict(candidate))
    return ExecutionRequest(
        execution_id=execution_id,
        order_request=order_request,
        execution_mode=mode,
        created_at=(candidate or {}).get("created_at") or order_request.created_at,
        disabled_reason=str((candidate or {}).get("disabled_reason") or "brokerage_boundary_disabled"),
        broker_name=broker_name or str((candidate or {}).get("broker_name") or ""),
        account_id=account_id or str((candidate or {}).get("account_id") or ""),
        client_execution_id=client_execution_id or execution_id,
        metadata=metadata_payload,
    )
