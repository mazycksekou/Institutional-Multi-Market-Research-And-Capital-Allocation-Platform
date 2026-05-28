from __future__ import annotations

from math import ceil
from typing import Any


def get_provider_registry() -> dict[str, dict[str, Any]]:
    return {
        "sportsbooks": {
            "provider_type": "sportsbook_aggregate",
            "streaming_supported": False,
            "placeholder_only": True,
            "rate_limit_per_minute": 30,
            "credential_env_vars": [],
        },
        "odds_api": {
            "provider_type": "odds_feed",
            "streaming_supported": False,
            "placeholder_only": True,
            "rate_limit_per_minute": 20,
            "credential_env_vars": ["ODDS_API_KEY"],
        },
        "opticodds": {
            "provider_type": "odds_feed",
            "streaming_supported": False,
            "placeholder_only": True,
            "rate_limit_per_minute": 60,
            "credential_env_vars": ["OPTICODDS_API_KEY"],
        },
        "sportradar": {
            "provider_type": "sports_data",
            "streaming_supported": True,
            "placeholder_only": True,
            "rate_limit_per_minute": 120,
            "credential_env_vars": ["SPORTRADAR_API_KEY"],
        },
        "sportsgameodds": {
            "provider_type": "sports_data",
            "streaming_supported": False,
            "placeholder_only": True,
            "rate_limit_per_minute": 30,
            "credential_env_vars": ["SPORTSGAMEODDS_API_KEY"],
        },
        "kalshi": {
            "provider_type": "prediction_market",
            "streaming_supported": True,
            "placeholder_only": True,
            "rate_limit_per_minute": 120,
            "credential_env_vars": ["KALSHI_API_KEY"],
        },
        "alpaca": {
            "provider_type": "brokerage",
            "streaming_supported": True,
            "placeholder_only": True,
            "rate_limit_per_minute": 200,
            "credential_env_vars": ["ALPACA_API_KEY", "ALPACA_SECRET_KEY"],
        },
        "polygon_or_massive": {
            "provider_type": "market_data",
            "streaming_supported": True,
            "placeholder_only": True,
            "rate_limit_per_minute": 300,
            "credential_env_vars": ["POLYGON_API_KEY"],
        },
        "news_provider": {
            "provider_type": "news_feed",
            "streaming_supported": False,
            "placeholder_only": True,
            "rate_limit_per_minute": 30,
            "credential_env_vars": ["NEWS_PROVIDER_API_KEY"],
        },
    }


def get_provider(provider_name: str) -> dict[str, Any]:
    registry = get_provider_registry()
    if provider_name not in registry:
        raise KeyError(f"unknown provider: {provider_name}")
    return registry[provider_name]


def provider_min_interval_seconds(provider_name: str, config: dict[str, Any] | None = None) -> int:
    providers = (config or {}).get("providers") if isinstance(config, dict) else None
    provider = (providers or get_provider_registry()).get(provider_name, {})
    rate_limit_per_minute = max(1, int(provider.get("rate_limit_per_minute", 1)))
    return max(1, ceil(60 / rate_limit_per_minute))
