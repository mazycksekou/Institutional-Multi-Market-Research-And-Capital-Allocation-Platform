from __future__ import annotations

from math import ceil
from typing import Any

from .provider_contracts import get_default_provider_contracts
from .provider_secret_policy import credential_status_from_env


def get_provider_registry() -> dict[str, dict[str, Any]]:
    registry = get_default_provider_contracts()
    sharp_credential_status = credential_status_from_env("sharp_sportsbook")
    registry["sharp_sportsbook"] = {
        "provider_id": "sharp_sportsbook",
        "provider_name": "Sharp Sportsbook",
        "provider_type": "sportsbook_odds",
        "enabled": False,
        "dry_run": True,
        "supports_streaming": False,
        "supports_polling": True,
        "min_poll_seconds": 60,
        "rate_limit_note": "read_only_get_only",
        "credential_status": sharp_credential_status["status"],
        "required_credentials": ["SHARP_API_KEY"],
        "supported_markets": ["moneyline", "spread", "total", "player_props"],
        "output_schema_version": "automation_scheduler.v1.sharp_sportsbook.v1",
        "last_health_status": "not_checked",
        "live_calls_enabled": False,
        "provider_live_calls_enabled": False,
        "provider_credentials_required": True,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "contract_status": "defined",
        "read_only_mode": True,
    }
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
