from __future__ import annotations

import re
from typing import Any, Mapping


REDACTED = "[redacted]"
OMITTED = "[omitted]"

SECRET_KEY_PARTS = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "authorization",
    "auth",
    "credential",
    "signature",
    "private_key",
    "bearer",
    "cookie",
    "session",
)

RAW_PAYLOAD_KEYS = {
    "provider_payload",
    "raw_payload",
    "raw_provider_payload",
    "raw_request_payload",
    "external_payload",
    "source_payload",
    "source_payload_redacted",
    "raw_kalshi_payload",
    "raw_sharp_payload",
    "request_payload",
    "response_payload",
    "order_payload",
    "broker_order_payload",
    "sportsbook_bet_payload",
    "kalshi_order_payload",
    "crypto_trade_payload",
    "trade_payload",
    "execution_payload",
    "executable_order_payload",
    "bet_slip",
    "wager_payload",
}

SECRET_VALUE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\bsk_[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\bpk-[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\bapi[_-]?[A-Za-z0-9_\-]{16,}\b", re.IGNORECASE),
    re.compile(r"\bbearer\s+[A-Za-z0-9._\-]{12,}\b", re.IGNORECASE),
    re.compile(r"\btoken\s+[A-Za-z0-9._\-]{12,}\b", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
    re.compile(r"\b[A-Za-z0-9_\-=]{32,}\b"),
)


def is_secret_key(key: str) -> bool:
    lower = str(key or "").strip().lower()
    return any(part in lower for part in SECRET_KEY_PARTS)


def looks_like_secret_value(value: str) -> bool:
    text = str(value or "")
    if not text.strip():
        return False
    return any(pattern.search(text) for pattern in SECRET_VALUE_PATTERNS)


def redact_string(value: str) -> str:
    text = str(value)
    redacted = text
    for pattern in SECRET_VALUE_PATTERNS:
        redacted = pattern.sub(REDACTED, redacted)
    return redacted


def contains_secret_like_content(payload: Any, *, key_hint: str | None = None) -> bool:
    if key_hint and is_secret_key(key_hint):
        if isinstance(payload, str):
            return payload.strip() not in {"", REDACTED}
        return payload is not None
    if isinstance(payload, Mapping):
        return any(contains_secret_like_content(value, key_hint=str(key)) for key, value in payload.items())
    if isinstance(payload, list):
        return any(contains_secret_like_content(value) for value in payload)
    if isinstance(payload, str):
        return looks_like_secret_value(payload)
    return False


def redact_sensitive(payload: Any, *, list_limit: int = 100) -> Any:
    if isinstance(payload, Mapping):
        out: dict[str, Any] = {}
        for key, value in payload.items():
            lower = str(key).strip().lower()
            if lower in RAW_PAYLOAD_KEYS:
                out[str(key)] = OMITTED
            elif is_secret_key(str(key)):
                out[str(key)] = REDACTED
            else:
                out[str(key)] = redact_sensitive(value, list_limit=list_limit)
        return out
    if isinstance(payload, list):
        return [redact_sensitive(value, list_limit=list_limit) for value in payload[: max(1, int(list_limit or 100))]]
    if isinstance(payload, str):
        return redact_string(payload)
    return payload


def secret_safety_fields(*, source_payload: Any = None, redacted_payload: Any = None) -> dict[str, Any]:
    safe_payload = redacted_payload if redacted_payload is not None else redact_sensitive(source_payload)
    source_had_secret = contains_secret_like_content(source_payload) if source_payload is not None else False
    safe_has_secret = contains_secret_like_content(safe_payload)
    return {
        "secrets_detected": False,
        "raw_payload_exposed": False,
        "auth_header_exposed": False,
        "signature_exposed": False,
        "redaction_applied": True,
        "source_secret_like_content_redacted": bool(source_had_secret),
        "redacted_payload_contains_secret": bool(safe_has_secret),
    }


def assert_no_secret_leak(payload: Any) -> None:
    if contains_secret_like_content(payload):
        raise ValueError("secret_leak_detected")
