from __future__ import annotations

from typing import Any

from src.providers.prediction_markets import (
    PREDICTION_MARKET_PROVIDER_TYPE,
    SAMPLE_DRY_RUN_PAYLOAD as _CANONICAL_SAMPLE_DRY_RUN_PAYLOAD,
    build_prediction_market_provider_contract,
    normalize_prediction_market_payload as _normalize_prediction_market_payload,
    validate_prediction_market_payload as _validate_prediction_market_payload,
)

REQUIRED_FIELDS = [
    "market_id",
    "event_id",
    "event_title",
    "contract_id",
    "contract_title",
    "yes_price",
    "no_price",
    "implied_probability",
    "volume",
    "open_interest",
    "close_time",
    "timestamp",
]
OPTIONAL_FIELDS: list[str] = []
SAMPLE_DRY_RUN_PAYLOAD = {
    **_CANONICAL_SAMPLE_DRY_RUN_PAYLOAD,
}


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return _validate_prediction_market_payload(payload)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return _normalize_prediction_market_payload(payload)


__all__ = [
    "PREDICTION_MARKET_PROVIDER_TYPE",
    "REQUIRED_FIELDS",
    "OPTIONAL_FIELDS",
    "SAMPLE_DRY_RUN_PAYLOAD",
    "build_prediction_market_provider_contract",
    "normalize_payload",
    "validate_payload",
]
