from __future__ import annotations

from typing import Any

from .provider_payload_validator import validate_provider_payload
from .scheduler_config import utc_now_iso

REQUIRED_FIELDS = ["source", "title", "event_type", "affected_entities", "severity_score", "published_at", "timestamp"]
OPTIONAL_FIELDS = []
SAMPLE_DRY_RUN_PAYLOAD = {
    "source": "news_events_placeholder",
    "title": "Demo news event",
    "event_type": "injury_update",
    "affected_entities": ["Team A"],
    "severity_score": 0.4,
    "published_at": "2026-05-28T00:00:00+00:00",
    "timestamp": utc_now_iso(),
}


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_provider_payload("news_events", payload)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": payload.get("source"),
        "title": payload.get("title"),
        "event_type": payload.get("event_type"),
        "affected_entities": payload.get("affected_entities"),
        "severity_score": payload.get("severity_score"),
        "published_at": payload.get("published_at"),
        "timestamp": payload.get("timestamp"),
    }

