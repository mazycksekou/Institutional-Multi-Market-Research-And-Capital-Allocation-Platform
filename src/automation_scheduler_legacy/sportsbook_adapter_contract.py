from __future__ import annotations

from typing import Any

from src.providers.sportsbooks import (
    SAMPLE_DRY_RUN_PAYLOAD as _CANONICAL_SAMPLE_DRY_RUN_PAYLOAD,
    SPORTSBOOK_PROVIDER_TYPE,
    build_sportsbook_provider_contract,
    normalize_sportsbook_payload as _normalize_sportsbook_payload,
    validate_sportsbook_payload as _validate_sportsbook_payload,
)

REQUIRED_FIELDS = ["event_id", "sport", "league", "event_name", "book", "market", "selection", "odds", "timestamp"]
OPTIONAL_FIELDS = ["start_time", "line"]
SAMPLE_DRY_RUN_PAYLOAD = {
    **_CANONICAL_SAMPLE_DRY_RUN_PAYLOAD,
}


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return _validate_sportsbook_payload(payload)


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return _normalize_sportsbook_payload(payload)


__all__ = [
    "REQUIRED_FIELDS",
    "OPTIONAL_FIELDS",
    "SAMPLE_DRY_RUN_PAYLOAD",
    "SPORTSBOOK_PROVIDER_TYPE",
    "build_sportsbook_provider_contract",
    "normalize_payload",
    "validate_payload",
]
