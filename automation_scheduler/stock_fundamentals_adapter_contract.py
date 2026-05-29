from __future__ import annotations

from typing import Any

from .provider_payload_validator import validate_provider_payload
from .scheduler_config import utc_now_iso

REQUIRED_FIELDS = ["symbol", "market_cap", "revenue", "earnings", "sector", "report_date", "timestamp"]
OPTIONAL_FIELDS = []
SAMPLE_DRY_RUN_PAYLOAD = {
    "symbol": "AAPL",
    "market_cap": 3000000000000,
    "revenue": 90000000000,
    "earnings": 22000000000,
    "sector": "technology",
    "report_date": "2026-03-31",
    "timestamp": utc_now_iso(),
}


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_provider_payload("stock_fundamentals", payload)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": payload.get("symbol"),
        "market_cap": payload.get("market_cap"),
        "revenue": payload.get("revenue"),
        "earnings": payload.get("earnings"),
        "sector": payload.get("sector"),
        "report_date": payload.get("report_date"),
        "timestamp": payload.get("timestamp"),
    }

