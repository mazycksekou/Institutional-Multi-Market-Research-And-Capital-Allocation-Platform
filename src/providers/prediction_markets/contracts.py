from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from ..contracts import ProviderContract, build_provider_contract
from ..normalization import normalize_provider_payload as _normalize_provider_payload
from ..validation import validate_provider_payload as _validate_provider_payload

PREDICTION_MARKET_PROVIDER_TYPE = "prediction_market"
PredictionMarketProviderContract = ProviderContract


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


SAMPLE_DRY_RUN_PAYLOAD = {
    "market_id": "prediction_market_demo_1",
    "event_id": "prediction_market_event_demo_1",
    "event_title": "Demo Event",
    "contract_id": "prediction_market_contract_demo_1",
    "contract_title": "Yes",
    "yes_price": 0.56,
    "no_price": 0.44,
    "implied_probability": 0.56,
    "volume": 1000,
    "open_interest": 450,
    "close_time": "2026-05-30T00:00:00+00:00",
    "timestamp": _utc_now_iso(),
}


def build_prediction_market_provider_contract(
    provider_id: str = "prediction_market_placeholder",
    provider_name: str = "Prediction Market Placeholder",
    **overrides: Any,
) -> ProviderContract:
    payload = build_provider_contract(
        provider_id=provider_id,
        provider_name=provider_name,
        provider_type=PREDICTION_MARKET_PROVIDER_TYPE,
        supports_streaming=bool(overrides.pop("supports_streaming", False)),
        supports_polling=bool(overrides.pop("supports_polling", True)),
        min_poll_seconds=int(overrides.pop("min_poll_seconds", 30)),
        rate_limit_note=str(overrides.pop("rate_limit_note", "dry_run_only")),
        required_credentials=list(overrides.pop("required_credentials", []) or []),
        supported_markets=list(overrides.pop("supported_markets", ["yes_no_contracts"]) or ["yes_no_contracts"]),
        enabled=bool(overrides.pop("enabled", False)),
        live_calls_enabled=bool(overrides.pop("live_calls_enabled", False)),
    )
    payload.update(overrides)
    return ProviderContract.from_mapping(payload)


def validate_prediction_market_payload(
    payload: Mapping[str, Any],
    *,
    max_staleness_seconds: int = 3600 * 12,
) -> dict[str, Any]:
    return _validate_provider_payload(
        PREDICTION_MARKET_PROVIDER_TYPE,
        dict(payload),
        max_staleness_seconds=max_staleness_seconds,
    )


def normalize_prediction_market_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = _normalize_provider_payload(PREDICTION_MARKET_PROVIDER_TYPE, payload)
    return {
        "provider_type": PREDICTION_MARKET_PROVIDER_TYPE,
        "market_id": normalized.get("market_id"),
        "event_id": normalized.get("event_id"),
        "event_title": normalized.get("event_title"),
        "contract_id": normalized.get("contract_id"),
        "contract_title": normalized.get("contract_title"),
        "yes_price": normalized.get("yes_price"),
        "no_price": normalized.get("no_price"),
        "implied_probability": normalized.get("implied_probability"),
        "volume": normalized.get("volume"),
        "open_interest": normalized.get("open_interest"),
        "close_time": normalized.get("close_time"),
        "timestamp": normalized.get("timestamp"),
    }


__all__ = [
    "PREDICTION_MARKET_PROVIDER_TYPE",
    "PredictionMarketProviderContract",
    "SAMPLE_DRY_RUN_PAYLOAD",
    "build_prediction_market_provider_contract",
    "normalize_prediction_market_payload",
    "validate_prediction_market_payload",
]
