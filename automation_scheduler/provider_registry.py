from __future__ import annotations

from math import ceil
from typing import Any

from .provider_contracts import get_default_provider_contracts


def get_provider_registry() -> dict[str, dict[str, Any]]:
    registry = get_default_provider_contracts()
    registry["stock_placeholder"] = dict(registry["stock_price_placeholder"])
    registry["news_placeholder"] = dict(registry["news_events_placeholder"])
    # compatibility aliases
    registry["sportsbooks"] = dict(registry["sportsbook_placeholder"])
    registry["odds_api"] = dict(registry["player_props_placeholder"])
    registry["kalshi"] = dict(registry["kalshi_placeholder"])
    registry["alpaca"] = dict(registry["stock_placeholder"])
    registry["news_provider"] = dict(registry["news_placeholder"])
    for key, value in registry.items():
        value["name"] = value.get("provider_name", key)
        value["market_type"] = value.get("provider_type", "unknown")
        value["contract_status"] = value.get("contract_status", "defined")
        value["capabilities"] = {
            "supports_streaming": bool(value.get("supports_streaming", False)),
            "supports_polling": bool(value.get("supports_polling", True)),
            "min_poll_seconds": int(value.get("min_poll_seconds", 60)),
            "live_calls_enabled": bool(value.get("live_calls_enabled", False)),
            "dry_run": bool(value.get("dry_run", True)),
        }
    return registry


def provider_min_interval_seconds(provider_name: str, config: dict[str, Any] | None = None) -> int:
    providers = (config or {}).get("providers", get_provider_registry())
    provider = providers.get(provider_name, {})
    min_poll = int(provider.get("min_poll_seconds", 30))
    return max(1, min_poll)


def get_provider(provider_name: str) -> dict[str, Any]:
    return get_provider_registry()[provider_name]
