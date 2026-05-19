from __future__ import annotations

from typing import Any


def unavailable(provider: str, reason: str = "missing_environment") -> dict[str, Any]:
    return {
        "provider": provider,
        "provider_status": "unavailable",
        "reason": reason,
        "data": [],
    }


def provider_error(provider: str, message: str, provider_notes: list[str] | None = None) -> dict[str, Any]:
    return {
        "provider": provider,
        "provider_status": "error",
        "message": message,
        "provider_notes": provider_notes or [],
        "data": [],
    }


def available(provider: str, data: Any, **extra: Any) -> dict[str, Any]:
    return {
        "provider": provider,
        "provider_status": "available",
        "data": data,
        **extra,
    }
