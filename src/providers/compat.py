from __future__ import annotations

import os
from typing import Any

SPORTSBOOK_ODDS = "sportsbook_odds"
PREDICTION_MARKET = "prediction_market"


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def clean_error(error_type: str, message: str, **extra: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "error_type": error_type,
        "message": message,
        **extra,
    }


def unknown_provider(available_providers: list[str]) -> dict[str, Any]:
    return clean_error(
        "UNKNOWN_PROVIDER",
        "Unknown provider",
        available_providers=available_providers,
    )


def provider_disabled(provider_id: str) -> dict[str, Any]:
    return clean_error(
        "PROVIDER_DISABLED",
        "Provider is disabled",
        provider=provider_id,
    )


def provider_not_configured(provider_id: str) -> dict[str, Any]:
    return clean_error(
        "PROVIDER_NOT_CONFIGURED",
        "Provider credentials or base URL are missing",
        provider=provider_id,
    )


def method_not_implemented(provider_id: str, message: str) -> dict[str, Any]:
    return clean_error(
        "PROVIDER_METHOD_NOT_IMPLEMENTED",
        message,
        provider=provider_id,
    )


def available(provider: str, data: Any, **extra: Any) -> dict[str, Any]:
    return {
        "provider": provider,
        "provider_status": "available",
        "data": data,
        **extra,
    }


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


class ProviderAdapter:
    id = ""
    name = ""
    provider_type = ""

    @property
    def enabled(self) -> bool:
        return False

    @property
    def configured(self) -> bool:
        return False

    def capability(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type,
            "enabled": self.enabled,
            "configured": self.configured,
            "supports_sports_list": False,
            "supports_events": False,
            "supports_odds": False,
            "supports_props": False,
            "supports_prediction_markets": False,
        }


__all__ = [
    "PREDICTION_MARKET",
    "SPORTSBOOK_ODDS",
    "ProviderAdapter",
    "available",
    "clean_error",
    "env_bool",
    "method_not_implemented",
    "provider_disabled",
    "provider_error",
    "provider_not_configured",
    "unknown_provider",
    "unavailable",
]
