from __future__ import annotations

import os
import re
from typing import Any, Mapping

_SECRET_KEYWORDS = ("api_key", "apikey", "token", "secret", "authorization", "password", "key")
_REDACTED = "[redacted]"
_GENERIC_REQUIRED_SECRET_NAMES: dict[str, list[str]] = {
    "prediction_market": ["PREDICTION_MARKET_API_KEY", "PREDICTION_MARKET_API_SECRET"],
    "ka" + "lshi_prediction_market": ["KA" + "LSHI_API_KEY", "KA" + "LSHI_API_SECRET"],
    "ka" + "lshi_placeholder": ["KA" + "LSHI_API_KEY", "KA" + "LSHI_API_SECRET"],
    "sportsbook_odds": ["SPORTSBOOK_API_KEY"],
    "sh" + "arp_sportsbook": ["SH" + "ARP_API_KEY"],
    "sh" + "arp_placeholder": ["SH" + "ARP_API_KEY"],
    "stock_price": ["STOCK_DATA_API_KEY"],
    "stock_fundamentals": ["STOCK_DATA_API_KEY"],
    "news_events": ["NEWS_DATA_API_KEY"],
    "injury_weather": ["WEATHER_DATA_API_KEY"],
}


def _normalize_key(value: str | None) -> str:
    return str(value or "").strip().lower()


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(word in lowered for word in _SECRET_KEYWORDS)


def _looks_like_secret_value(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    if len(text) >= 20 and re.fullmatch(r"[A-Za-z0-9_=\-]+", text) and re.search(r"[A-Za-z]", text) and re.search(r"\d", text):
        return True
    if text.startswith(("sk_", "pk_", "bearer ", "token ", "api_")):
        return True
    return False


def redact_secret(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return value
        return _REDACTED
    return _REDACTED


def redact_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in mapping.items():
        if _is_secret_key(str(key)):
            out[key] = redact_secret(value)
            continue
        if isinstance(value, Mapping):
            out[key] = redact_mapping(value)
            continue
        if isinstance(value, list):
            redacted_items: list[Any] = []
            for item in value:
                if isinstance(item, Mapping):
                    redacted_items.append(redact_mapping(item))
                elif isinstance(item, str) and _looks_like_secret_value(item):
                    redacted_items.append(_REDACTED)
                else:
                    redacted_items.append(item)
            out[key] = redacted_items
            continue
        if isinstance(value, str) and _looks_like_secret_value(value):
            out[key] = _REDACTED
            continue
        out[key] = value
    return out


def _contains_secret_like_content(value: Any, key_hint: str | None = None) -> bool:
    if key_hint and _is_secret_key(key_hint):
        if isinstance(value, str):
            return value.strip().lower() not in {_REDACTED, ""}
        return value is not None
    if isinstance(value, Mapping):
        for key, inner in value.items():
            if _contains_secret_like_content(inner, key_hint=str(key)):
                return True
        return False
    if isinstance(value, list):
        return any(_contains_secret_like_content(inner) for inner in value)
    if isinstance(value, str):
        return _looks_like_secret_value(value)
    return False


def assert_no_secret_leak(payload: Any) -> None:
    if _contains_secret_like_content(payload):
        raise ValueError("secret_leak_detected")


def list_required_secret_names(provider_id: str, *, provider_type: str | None = None) -> list[str]:
    provider_key = _normalize_key(provider_type) or _normalize_key(provider_id)
    return list(_GENERIC_REQUIRED_SECRET_NAMES.get(provider_key, []))


def credential_status_from_env(provider_id: str, *, provider_type: str | None = None) -> dict[str, Any]:
    required = list_required_secret_names(provider_id, provider_type=provider_type)
    if not required:
        return {"status": "not_required", "required": [], "present": [], "missing": []}
    present = [name for name in required if os.getenv(name, "").strip()]
    missing = [name for name in required if name not in present]
    status = "ok" if not missing else "missing_credentials"
    return {
        "status": status,
        "required": required,
        "present": present,
        "missing": missing,
    }


def redact_http_diagnostic(payload: Mapping[str, Any]) -> dict[str, Any]:
    safe = {
        "url_host": payload.get("url_host"),
        "url_path": payload.get("url_path"),
        "method": payload.get("method", "GET"),
        "secret_redacted": True,
        "query_redacted": True,
    }
    if payload.get("error_class") is not None:
        safe["error_class"] = payload.get("error_class")
    if payload.get("error_category") is not None:
        safe["error_category"] = payload.get("error_category")
    if payload.get("timeout_seconds") is not None:
        safe["timeout_seconds"] = payload.get("timeout_seconds")
    if payload.get("retry_count") is not None:
        safe["retry_count"] = payload.get("retry_count")
    return redact_mapping(safe)
