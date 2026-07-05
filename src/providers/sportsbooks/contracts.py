from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from ..contracts import ProviderContract, build_provider_contract
from ..normalization import normalize_provider_payload as _normalize_provider_payload
from ..validation import validate_provider_payload as _validate_provider_payload

SPORTSBOOK_PROVIDER_TYPE = "sportsbook_odds"
SportsbookProviderContract = ProviderContract


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


SAMPLE_DRY_RUN_PAYLOAD = {
    "event_id": "sportsbook_demo_1",
    "sport": "basketball",
    "league": "NBA",
    "event_name": "A vs B",
    "start_time": "2026-05-28T00:00:00+00:00",
    "book": "sportsbook_placeholder",
    "market": "h2h",
    "selection": "A",
    "line": None,
    "odds": -110,
    "timestamp": _utc_now_iso(),
}


def build_sportsbook_provider_contract(
    provider_id: str = "sportsbook_placeholder",
    provider_name: str = "Sportsbook Placeholder",
    **overrides: Any,
) -> ProviderContract:
    payload = build_provider_contract(
        provider_id=provider_id,
        provider_name=provider_name,
        provider_type=SPORTSBOOK_PROVIDER_TYPE,
        supports_streaming=bool(overrides.pop("supports_streaming", False)),
        supports_polling=bool(overrides.pop("supports_polling", True)),
        min_poll_seconds=int(overrides.pop("min_poll_seconds", 15)),
        rate_limit_note=str(overrides.pop("rate_limit_note", "dry_run_only")),
        required_credentials=list(overrides.pop("required_credentials", []) or []),
        supported_markets=list(overrides.pop("supported_markets", ["h2h", "spreads", "totals"]) or ["h2h", "spreads", "totals"]),
        enabled=bool(overrides.pop("enabled", False)),
        live_calls_enabled=bool(overrides.pop("live_calls_enabled", False)),
    )
    payload.update(overrides)
    return ProviderContract.from_mapping(payload)


def validate_sportsbook_payload(
    payload: Mapping[str, Any],
    *,
    max_staleness_seconds: int = 3600 * 12,
) -> dict[str, Any]:
    return _validate_provider_payload(
        SPORTSBOOK_PROVIDER_TYPE,
        dict(payload),
        max_staleness_seconds=max_staleness_seconds,
    )


def normalize_sportsbook_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = _normalize_provider_payload(SPORTSBOOK_PROVIDER_TYPE, payload)
    return {
        "provider_type": SPORTSBOOK_PROVIDER_TYPE,
        "event_id": normalized.get("event_id"),
        "sport": normalized.get("sport"),
        "league": normalized.get("league"),
        "event_name": normalized.get("event_name"),
        "start_time": normalized.get("start_time"),
        "book": normalized.get("book"),
        "market": normalized.get("market"),
        "selection": normalized.get("selection"),
        "line": normalized.get("line"),
        "odds": normalized.get("odds"),
        "timestamp": normalized.get("timestamp"),
    }


__all__ = [
    "SPORTSBOOK_PROVIDER_TYPE",
    "SportsbookProviderContract",
    "SAMPLE_DRY_RUN_PAYLOAD",
    "build_sportsbook_provider_contract",
    "normalize_sportsbook_payload",
    "validate_sportsbook_payload",
]
