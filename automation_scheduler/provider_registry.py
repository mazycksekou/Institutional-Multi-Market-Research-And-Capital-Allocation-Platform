from __future__ import annotations

from typing import Any

from src.providers.registry import (
    ProviderRegistry,
    create_provider_registry,
    get_provider_registry as _get_provider_registry,
)


def get_provider_registry() -> dict[str, dict[str, Any]]:
    return _get_provider_registry(include_legacy_aliases=True)


def provider_min_interval_seconds(provider_name: str, config: dict[str, Any] | None = None) -> int:
    providers = (config or {}).get("providers", get_provider_registry())
    provider = providers.get(provider_name, {})
    min_poll = int(provider.get("min_poll_seconds", 30))
    return max(1, min_poll)


def get_provider(provider_name: str) -> dict[str, Any]:
    return get_provider_registry()[provider_name]


__all__ = [
    "ProviderRegistry",
    "create_provider_registry",
    "get_provider",
    "get_provider_registry",
    "provider_min_interval_seconds",
]
