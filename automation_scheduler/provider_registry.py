from __future__ import annotations

from math import ceil
from typing import Any


def get_provider_registry() -> dict[str, dict[str, Any]]:
    registry = {
        "sportsbook_placeholder": {"name": "sportsbook_placeholder", "market_type": "sports", "supports_streaming": False, "min_poll_seconds": 15, "rate_limit_note": "placeholder", "enabled": False},
        "player_props_placeholder": {"name": "player_props_placeholder", "market_type": "player_props", "supports_streaming": False, "min_poll_seconds": 30, "rate_limit_note": "placeholder", "enabled": False},
        "kalshi_placeholder": {"name": "kalshi_placeholder", "market_type": "prediction_market", "supports_streaming": True, "min_poll_seconds": 15, "rate_limit_note": "placeholder", "enabled": False},
        "stock_placeholder": {"name": "stock_placeholder", "market_type": "stock", "supports_streaming": True, "min_poll_seconds": 5, "rate_limit_note": "placeholder", "enabled": False},
        "news_placeholder": {"name": "news_placeholder", "market_type": "news", "supports_streaming": False, "min_poll_seconds": 60, "rate_limit_note": "placeholder", "enabled": False},
    }
    # compatibility aliases
    registry["sportsbooks"] = dict(registry["sportsbook_placeholder"])
    registry["odds_api"] = dict(registry["player_props_placeholder"])
    registry["kalshi"] = dict(registry["kalshi_placeholder"])
    registry["alpaca"] = dict(registry["stock_placeholder"])
    registry["news_provider"] = dict(registry["news_placeholder"])
    return registry


def provider_min_interval_seconds(provider_name: str, config: dict[str, Any] | None = None) -> int:
    providers = (config or {}).get("providers", get_provider_registry())
    provider = providers.get(provider_name, {})
    min_poll = int(provider.get("min_poll_seconds", 30))
    return max(1, min_poll)


def get_provider(provider_name: str) -> dict[str, Any]:
    return get_provider_registry()[provider_name]
