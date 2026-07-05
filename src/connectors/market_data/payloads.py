from __future__ import annotations

from typing import Any, Mapping

from .models import MarketDataQuote


def normalize_market_data_payload(payload: Mapping[str, Any], *, source: str = "market_data") -> dict[str, Any]:
    data = dict(payload)
    data.setdefault("_source", source)
    data.setdefault("_connector_category", "market_data")
    data.setdefault("_read_only", True)
    return data


def build_market_data_quote(payload: Mapping[str, Any], *, source: str = "market_data") -> MarketDataQuote:
    normalized = normalize_market_data_payload(payload, source=source)
    return MarketDataQuote(
        provider=str(normalized.get("provider") or source),
        symbol=str(normalized.get("symbol") or normalized.get("ticker") or normalized.get("underlying_symbol") or ""),
        asset_class=str(normalized.get("asset_class") or normalized.get("security_type") or ""),
        exchange=str(normalized.get("exchange") or normalized.get("market") or ""),
        quote_type=str(normalized.get("quote_type") or normalized.get("data_type") or "quote"),
        payload=normalized,
    )


def validate_market_data_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = normalize_market_data_payload(payload)
    errors: list[str] = []
    if not str(normalized.get("provider") or "").strip():
        errors.append("missing_provider")
    return {
        "ok": not errors,
        "status": "accepted" if not errors else "rejected",
        "errors": errors,
        "normalized": normalized,
    }
