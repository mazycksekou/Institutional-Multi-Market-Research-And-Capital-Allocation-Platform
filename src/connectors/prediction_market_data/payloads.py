from __future__ import annotations

from typing import Any, Mapping

from .models import PredictionMarketRecord


def normalize_prediction_market_payload(payload: Mapping[str, Any], *, source: str = "prediction_market_data") -> dict[str, Any]:
    data = dict(payload)
    data.setdefault("_source", source)
    data.setdefault("_connector_category", "prediction_market_data")
    data.setdefault("_read_only", True)
    return data


def build_prediction_market_record(payload: Mapping[str, Any], *, source: str = "prediction_market_data") -> PredictionMarketRecord:
    normalized = normalize_prediction_market_payload(payload, source=source)
    return PredictionMarketRecord(
        provider=str(normalized.get("provider") or source),
        market_id=str(normalized.get("market_id") or normalized.get("ticker") or ""),
        event_id=str(normalized.get("event_id") or normalized.get("event_ticker") or ""),
        title=str(normalized.get("title") or normalized.get("name") or ""),
        payload=normalized,
    )


def validate_prediction_market_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = normalize_prediction_market_payload(payload)
    errors: list[str] = []
    if not str(normalized.get("provider") or "").strip():
        errors.append("missing_provider")
    return {
        "ok": not errors,
        "status": "accepted" if not errors else "rejected",
        "errors": errors,
        "normalized": normalized,
    }
