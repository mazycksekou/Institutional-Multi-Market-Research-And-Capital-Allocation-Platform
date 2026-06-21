from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from src.connectors.market_data.models import MarketDataQuote, MarketDataSnapshot

from .models import ZeroDteStockQuote, ZeroDteStockSnapshot

ZERO_DTE_STOCK_PROVIDER_TYPE = "stock_price"


def _payload_to_mapping(payload: Any) -> dict[str, Any]:
    if isinstance(payload, ZeroDteStockQuote):
        return payload.as_dict()
    if isinstance(payload, ZeroDteStockSnapshot):
        if payload.quotes:
            return payload.quotes[0].as_dict()
        return {
            "provider": payload.provider,
            "provider_type": payload.provider_type,
            "timestamp": None,
        }
    if isinstance(payload, MarketDataQuote):
        data = dict(payload.payload or {})
        data.setdefault("provider", payload.provider)
        data.setdefault("symbol", payload.symbol)
        data.setdefault("asset_class", payload.asset_class)
        data.setdefault("exchange", payload.exchange)
        data.setdefault("quote_type", payload.quote_type)
        return data
    if isinstance(payload, MarketDataSnapshot):
        if payload.records:
            return _payload_to_mapping(payload.records[0])
        return {"provider": payload.provider, "provider_type": ZERO_DTE_STOCK_PROVIDER_TYPE}
    if isinstance(payload, Mapping):
        return dict(payload)
    if hasattr(payload, "as_dict") and callable(getattr(payload, "as_dict")):
        candidate = payload.as_dict()
        if isinstance(candidate, Mapping):
            return dict(candidate)
    raise TypeError("zero_dte_stocks provider requires a mapping or market-data payload")


def normalize_zero_dte_stock_payload(payload: Any, *, provider: str = "zero_dte_stocks") -> dict[str, Any]:
    data = _payload_to_mapping(payload)
    normalized = dict(data)
    normalized.setdefault("provider", provider)
    normalized.setdefault("provider_type", ZERO_DTE_STOCK_PROVIDER_TYPE)
    normalized.setdefault("raw", dict(data))
    return {
        "provider": str(normalized.get("provider") or provider),
        "provider_type": ZERO_DTE_STOCK_PROVIDER_TYPE,
        "symbol": normalized.get("symbol"),
        "price": normalized.get("price"),
        "bid": normalized.get("bid"),
        "ask": normalized.get("ask"),
        "volume": normalized.get("volume"),
        "timestamp": normalized.get("timestamp"),
        "raw": dict(normalized),
    }


def build_zero_dte_stock_quote(payload: Any, *, provider: str = "zero_dte_stocks") -> ZeroDteStockQuote:
    normalized = normalize_zero_dte_stock_payload(payload, provider=provider)
    return ZeroDteStockQuote(
        provider=str(normalized.get("provider") or provider),
        provider_type=ZERO_DTE_STOCK_PROVIDER_TYPE,
        symbol=normalized.get("symbol"),
        price=normalized.get("price"),
        bid=normalized.get("bid"),
        ask=normalized.get("ask"),
        volume=normalized.get("volume"),
        timestamp=normalized.get("timestamp"),
        raw=dict(normalized.get("raw") or {}),
    )


def build_zero_dte_stock_snapshot(
    payloads: Any,
    *,
    provider: str = "zero_dte_stocks",
) -> ZeroDteStockSnapshot:
    if isinstance(payloads, ZeroDteStockSnapshot):
        return payloads
    if isinstance(payloads, MarketDataSnapshot):
        payload_iterable: Iterable[Any] = payloads.records
    elif isinstance(payloads, (ZeroDteStockQuote, MarketDataQuote, Mapping)) or hasattr(payloads, "as_dict"):
        payload_iterable = (payloads,)
    else:
        payload_iterable = payloads
    quotes = tuple(build_zero_dte_stock_quote(payload, provider=provider) for payload in payload_iterable)
    return ZeroDteStockSnapshot(provider=provider, provider_type=ZERO_DTE_STOCK_PROVIDER_TYPE, quotes=quotes)


def normalize_zero_dte_stock_quote(payload: Any, *, provider: str = "zero_dte_stocks") -> dict[str, Any]:
    return build_zero_dte_stock_quote(payload, provider=provider).as_dict()


def normalize_zero_dte_stock_snapshot(payload: Any, *, provider: str = "zero_dte_stocks") -> dict[str, Any]:
    snapshot = build_zero_dte_stock_snapshot(payload, provider=provider)
    return snapshot.as_dict()


def validate_zero_dte_stock_payload(
    payload: Any,
    *,
    max_staleness_seconds: int = 3600 * 12,
) -> dict[str, Any]:
    normalized = normalize_zero_dte_stock_payload(payload)
    errors: list[str] = []
    if not str(normalized.get("provider") or "").strip():
        errors.append("missing_provider")
    if not str(normalized.get("symbol") or "").strip():
        errors.append("missing_symbol")
    if normalized.get("timestamp") in (None, ""):
        errors.append("missing_timestamp")
    return {
        "ok": not errors,
        "status": "accepted" if not errors else "rejected",
        "errors": errors,
        "max_staleness_seconds": int(max_staleness_seconds),
        "normalized": normalized,
    }
