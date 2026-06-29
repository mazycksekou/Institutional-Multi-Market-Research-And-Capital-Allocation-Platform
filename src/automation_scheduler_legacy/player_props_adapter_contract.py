from __future__ import annotations

from typing import Any

from src.providers.validation import validate_provider_payload
from .scheduler_config import utc_now_iso

REQUIRED_FIELDS = ["event_id", "player_name", "team", "market", "selection", "line", "odds", "timestamp"]
OPTIONAL_FIELDS = ["book"]
SAMPLE_DRY_RUN_PAYLOAD = {
    "event_id": "evt_prop_1",
    "player_name": "Player A",
    "team": "TEAM",
    "book": "player_props_placeholder",
    "market": "points",
    "selection": "over",
    "line": 24.5,
    "odds": -115,
    "timestamp": utc_now_iso(),
}


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_provider_payload("player_props", payload)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": payload.get("event_id"),
        "player_name": payload.get("player_name"),
        "team": payload.get("team"),
        "market": payload.get("market"),
        "selection": payload.get("selection"),
        "line": payload.get("line"),
        "odds": payload.get("odds"),
        "timestamp": payload.get("timestamp"),
    }
