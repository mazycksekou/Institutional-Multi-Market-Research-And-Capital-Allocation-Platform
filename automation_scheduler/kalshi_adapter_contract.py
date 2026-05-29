from __future__ import annotations

from typing import Any

from .provider_payload_validator import validate_provider_payload
from .scheduler_config import utc_now_iso

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
OPTIONAL_FIELDS = []
SAMPLE_DRY_RUN_PAYLOAD = {
    "market_id": "kalshi_demo_1",
    "event_id": "kalshi_event_demo_1",
    "event_title": "Demo Event",
    "contract_id": "kalshi_contract_demo_1",
    "contract_title": "Yes",
    "yes_price": 0.56,
    "no_price": 0.44,
    "implied_probability": 0.56,
    "volume": 1000,
    "open_interest": 450,
    "close_time": "2026-05-30T00:00:00+00:00",
    "timestamp": utc_now_iso(),
}


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_provider_payload("prediction_market", payload)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "market_id": payload.get("market_id"),
        "event_id": payload.get("event_id"),
        "event_title": payload.get("event_title"),
        "contract_id": payload.get("contract_id"),
        "contract_title": payload.get("contract_title"),
        "yes_price": payload.get("yes_price"),
        "no_price": payload.get("no_price"),
        "implied_probability": payload.get("implied_probability"),
        "volume": payload.get("volume"),
        "open_interest": payload.get("open_interest"),
        "close_time": payload.get("close_time"),
        "timestamp": payload.get("timestamp"),
    }
