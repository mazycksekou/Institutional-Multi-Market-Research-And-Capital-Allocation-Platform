from __future__ import annotations

from typing import Any

from src.providers.validation import validate_provider_payload
from src.services.scheduler_config import utc_now_iso

REQUIRED_FIELDS = ["event_id", "entity", "status", "severity_score", "source", "timestamp"]
OPTIONAL_FIELDS = []
SAMPLE_DRY_RUN_PAYLOAD = {
    "event_id": "evt_weather_1",
    "entity": "Player A",
    "status": "questionable",
    "severity_score": 0.5,
    "source": "injury_weather_placeholder",
    "timestamp": utc_now_iso(),
}


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_provider_payload("injury_weather", payload)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": payload.get("event_id"),
        "entity": payload.get("entity"),
        "status": payload.get("status"),
        "severity_score": payload.get("severity_score"),
        "source": payload.get("source"),
        "timestamp": payload.get("timestamp"),
    }
