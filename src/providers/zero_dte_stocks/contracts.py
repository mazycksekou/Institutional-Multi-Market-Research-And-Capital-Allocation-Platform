from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from ..contracts import ProviderContract, build_provider_contract
from ..normalization import normalize_provider_payload as _normalize_provider_payload
from ..validation import validate_provider_payload as _validate_provider_payload

ZERO_DTE_STOCK_PROVIDER_TYPE = "stock_price"
ZeroDteStockProviderContract = ProviderContract


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


SAMPLE_DRY_RUN_PAYLOAD = {
    "symbol": "AAPL",
    "price": 190.0,
    "bid": 189.9,
    "ask": 190.1,
    "volume": 100000,
    "timestamp": _utc_now_iso(),
}


def build_zero_dte_stock_provider_contract(
    provider_id: str = "zero_dte_stock_placeholder",
    provider_name: str = "Zero DTE Stock Placeholder",
    **overrides: Any,
) -> ProviderContract:
    payload = build_provider_contract(
        provider_id=provider_id,
        provider_name=provider_name,
        provider_type=ZERO_DTE_STOCK_PROVIDER_TYPE,
        supports_streaming=bool(overrides.pop("supports_streaming", True)),
        supports_polling=bool(overrides.pop("supports_polling", True)),
        min_poll_seconds=int(overrides.pop("min_poll_seconds", 5)),
        rate_limit_note=str(overrides.pop("rate_limit_note", "dry_run_only")),
        required_credentials=list(overrides.pop("required_credentials", []) or []),
        supported_markets=list(overrides.pop("supported_markets", ["equities"]) or ["equities"]),
        enabled=bool(overrides.pop("enabled", False)),
        live_calls_enabled=bool(overrides.pop("live_calls_enabled", False)),
    )
    payload.update(overrides)
    return ProviderContract.from_mapping(payload)


def validate_zero_dte_stock_payload(
    payload: Mapping[str, Any],
    *,
    max_staleness_seconds: int = 3600 * 12,
) -> dict[str, Any]:
    return _validate_provider_payload(
        ZERO_DTE_STOCK_PROVIDER_TYPE,
        dict(payload),
        max_staleness_seconds=max_staleness_seconds,
    )


def normalize_zero_dte_stock_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = _normalize_provider_payload(ZERO_DTE_STOCK_PROVIDER_TYPE, payload)
    return {
        "provider_type": ZERO_DTE_STOCK_PROVIDER_TYPE,
        "symbol": normalized.get("symbol"),
        "price": normalized.get("price"),
        "bid": normalized.get("bid"),
        "ask": normalized.get("ask"),
        "volume": normalized.get("volume"),
        "timestamp": normalized.get("timestamp"),
    }


__all__ = [
    "ZERO_DTE_STOCK_PROVIDER_TYPE",
    "ZeroDteStockProviderContract",
    "SAMPLE_DRY_RUN_PAYLOAD",
    "build_zero_dte_stock_provider_contract",
    "normalize_zero_dte_stock_payload",
    "validate_zero_dte_stock_payload",
]
