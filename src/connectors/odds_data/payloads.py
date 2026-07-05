from __future__ import annotations

from typing import Any, Mapping

from .models import OddsDataRecord


def normalize_odds_payload(payload: Mapping[str, Any], *, source: str = "odds_data") -> dict[str, Any]:
    data = dict(payload)
    data.setdefault("_source", source)
    data.setdefault("_connector_category", "odds_data")
    data.setdefault("_read_only", True)
    return data


def build_odds_record(payload: Mapping[str, Any], *, source: str = "odds_data") -> OddsDataRecord:
    normalized = normalize_odds_payload(payload, source=source)
    return OddsDataRecord(
        provider=str(normalized.get("provider") or source),
        sport=str(normalized.get("sport") or ""),
        league=str(normalized.get("league") or ""),
        event_id=str(normalized.get("event_id") or normalized.get("id") or ""),
        market=str(normalized.get("market") or ""),
        selection=str(normalized.get("selection") or ""),
        payload=normalized,
    )


def validate_odds_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = normalize_odds_payload(payload)
    errors: list[str] = []
    if not str(normalized.get("provider") or "").strip():
        errors.append("missing_provider")
    return {
        "ok": not errors,
        "status": "accepted" if not errors else "rejected",
        "errors": errors,
        "normalized": normalized,
    }
