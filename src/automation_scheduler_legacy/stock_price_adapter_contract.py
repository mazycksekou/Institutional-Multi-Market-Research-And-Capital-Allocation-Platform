from __future__ import annotations

from typing import Any

from src.providers.validation import validate_provider_payload
from src.services.scheduler_config import utc_now_iso

REQUIRED_FIELDS = ["symbol", "price", "bid", "ask", "volume", "timestamp"]
OPTIONAL_FIELDS = []
SAMPLE_DRY_RUN_PAYLOAD = {
    "symbol": "AAPL",
    "price": 205.1,
    "bid": 205.0,
    "ask": 205.2,
    "volume": 1200000,
    "timestamp": utc_now_iso(),
}


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_provider_payload("stock_price", payload)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": payload.get("symbol"),
        "price": payload.get("price"),
        "bid": payload.get("bid"),
        "ask": payload.get("ask"),
        "volume": payload.get("volume"),
        "timestamp": payload.get("timestamp"),
    }
