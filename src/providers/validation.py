from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .contracts import PROVIDER_TYPES


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _is_number(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def validate_provider_payload(
    provider_type: str,
    payload: dict[str, Any],
    *,
    max_staleness_seconds: int = 3600 * 12,
) -> dict[str, Any]:
    if provider_type not in PROVIDER_TYPES:
        return {"ok": False, "errors": ["unknown_provider_type"], "validation_status": "rejected"}

    errors: list[str] = []

    timestamp = _parse_timestamp(payload.get("timestamp"))
    if timestamp is None:
        errors.append("missing_timestamp")
    else:
        age_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
        if age_seconds > max_staleness_seconds:
            errors.append("stale_timestamp")

    if provider_type in {"sportsbook_odds", "player_props", "injury_weather"}:
        if not payload.get("event_id"):
            errors.append("missing_event_id")

    if provider_type == "prediction_market":
        if not payload.get("market_id"):
            errors.append("missing_market_id")
        if not payload.get("event_id"):
            errors.append("missing_event_id")
        if not payload.get("contract_id"):
            errors.append("missing_contract_id")

        for price_field in ("yes_price", "no_price", "yes_bid", "yes_ask", "no_bid", "no_ask"):
            if price_field in payload and payload.get(price_field) is not None:
                if not _is_number(payload.get(price_field)):
                    errors.append("malformed_price")
                    continue
                price_value = float(payload.get(price_field))
                if price_value < 0 or price_value > 1:
                    errors.append("malformed_price")

        for numeric_field, malformed_code in (("volume", "malformed_volume"), ("open_interest", "malformed_open_interest")):
            if numeric_field in payload and payload.get(numeric_field) is not None and not _is_number(payload.get(numeric_field)):
                errors.append(malformed_code)

    if provider_type in {"sportsbook_odds", "player_props"}:
        if not payload.get("market"):
            errors.append("missing_market_name")
        if not payload.get("selection"):
            errors.append("missing_selection")
        if not _is_number(payload.get("odds")):
            errors.append("malformed_odds")

    for prob_field in ("implied_probability", "model_probability", "no_vig_probability"):
        if prob_field in payload and payload.get(prob_field) is not None:
            if not _is_number(payload.get(prob_field)):
                errors.append("malformed_probability")
                continue
            p = float(payload.get(prob_field))
            if p < 0 or p > 1:
                errors.append("malformed_probability")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "validation_status": "accepted" if len(errors) == 0 else "rejected",
    }


class ProviderPayloadValidator:
    """Import-safe facade for validating provider payloads."""

    @staticmethod
    def validate(
        provider_type: str,
        payload: dict[str, Any],
        *,
        max_staleness_seconds: int = 3600 * 12,
    ) -> dict[str, Any]:
        return validate_provider_payload(
            provider_type,
            payload,
            max_staleness_seconds=max_staleness_seconds,
        )
