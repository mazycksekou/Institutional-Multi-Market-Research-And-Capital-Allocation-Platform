from __future__ import annotations

from typing import Any

from .provider_payload_validator import validate_provider_payload
from .scheduler_config import utc_now_iso

REQUIRED_FIELDS = ["event_id", "sport", "league", "event_name", "book", "market", "selection", "odds", "timestamp"]
OPTIONAL_FIELDS = ["start_time", "line"]
SAMPLE_DRY_RUN_PAYLOAD = {
    "event_id": "evt_demo_1",
    "sport": "basketball",
    "league": "NBA",
    "event_name": "A vs B",
    "start_time": "2026-05-28T00:00:00+00:00",
    "book": "sportsbook_placeholder",
    "market": "h2h",
    "selection": "A",
    "line": None,
    "odds": -110,
    "timestamp": utc_now_iso(),
}


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_provider_payload("sportsbook_odds", payload)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": payload.get("event_id"),
        "sport": payload.get("sport"),
        "league": payload.get("league"),
        "event_name": payload.get("event_name"),
        "start_time": payload.get("start_time"),
        "book": payload.get("book"),
        "market": payload.get("market"),
        "selection": payload.get("selection"),
        "line": payload.get("line"),
        "odds": payload.get("odds"),
        "timestamp": payload.get("timestamp"),
    }

