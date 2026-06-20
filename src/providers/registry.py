from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Mapping

from .contracts import ProviderContract, get_default_provider_contracts
from .errors import ProviderConfigurationError
from .policy.secret_policy import credential_status_from_env


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class ProviderRegistry:
    _contracts: dict[str, ProviderContract] = field(default_factory=dict)

    def register(self, contract: ProviderContract | Mapping[str, Any]) -> ProviderContract:
        normalized = contract if isinstance(contract, ProviderContract) else ProviderContract.from_mapping(contract)
        if not normalized.provider_id:
            raise ProviderConfigurationError("provider_id is required")
        self._contracts[normalized.provider_id] = normalized
        return normalized

    def get(self, provider_id: str) -> ProviderContract | None:
        return self._contracts.get(str(provider_id))

    def list(self) -> list[ProviderContract]:
        return list(self._contracts.values())

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {provider_id: contract.as_dict() for provider_id, contract in self._contracts.items()}

    def clear(self) -> None:
        self._contracts.clear()

    def is_empty(self) -> bool:
        return not self._contracts

    def __len__(self) -> int:
        return len(self._contracts)

    def __contains__(self, provider_id: object) -> bool:
        return str(provider_id) in self._contracts


def create_provider_registry() -> ProviderRegistry:
    return ProviderRegistry()


def get_provider_registry() -> dict[str, dict[str, Any]]:
    registry = get_default_provider_contracts()
    sportsbook_provider_enabled = _env_bool("SPORTSBOOK_PROVIDER_ENABLED", default=False)
    sportsbook_live_reads_enabled = _env_bool("SPORTSBOOK_LIVE_READS_ENABLED", default=False)
    sportsbook_live_calls_enabled = bool(sportsbook_provider_enabled and sportsbook_live_reads_enabled)
    prediction_market_provider_enabled = _env_bool("PREDICTION_MARKET_PROVIDER_ENABLED", default=False)
    prediction_market_live_reads_enabled = _env_bool("PREDICTION_MARKET_LIVE_READS_ENABLED", default=False)
    prediction_market_live_calls_enabled = bool(prediction_market_provider_enabled and prediction_market_live_reads_enabled)

    registry["sportsbook_placeholder"] = {
        **registry["sportsbook_placeholder"],
        "enabled": sportsbook_provider_enabled,
        "live_calls_enabled": sportsbook_live_calls_enabled,
        "provider_live_calls_enabled": sportsbook_live_calls_enabled,
        "provider_credentials_required": True,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "read_only_mode": True,
        "credential_status": "missing_credentials" if sportsbook_provider_enabled else "not_required",
        "name": "Sportsbook Placeholder",
        "market_type": "sportsbook_odds",
        "capabilities": {
            "supports_streaming": False,
            "supports_polling": True,
            "min_poll_seconds": int(registry["sportsbook_placeholder"].get("min_poll_seconds", 60)),
            "live_calls_enabled": sportsbook_live_calls_enabled,
            "dry_run": True,
        },
    }
    registry["prediction_market_placeholder"] = {
        **registry["prediction_market_placeholder"],
        "enabled": prediction_market_provider_enabled,
        "live_calls_enabled": prediction_market_live_calls_enabled,
        "provider_live_calls_enabled": prediction_market_live_calls_enabled,
        "provider_credentials_required": True,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "prediction_market_order_execution_enabled": False,
        "read_only_mode": True,
        "credential_status": "missing_credentials" if prediction_market_provider_enabled else "not_required",
        "name": "Prediction Market Placeholder",
        "market_type": "prediction_market",
        "capabilities": {
            "supports_streaming": False,
            "supports_polling": True,
            "min_poll_seconds": int(registry["prediction_market_placeholder"].get("min_poll_seconds", 60)),
            "live_calls_enabled": prediction_market_live_calls_enabled,
            "dry_run": True,
        },
    }
    registry["stock_placeholder"] = dict(registry["stock_price_placeholder"])
    registry["news_placeholder"] = dict(registry["news_events_placeholder"])
    registry["sportsbooks"] = dict(registry["sportsbook_placeholder"])
    registry["prediction_markets"] = dict(registry["prediction_market_placeholder"])
    registry["zero_dte_stocks"] = dict(registry["stock_placeholder"])
    registry["news_events"] = dict(registry["news_placeholder"])
    registry["injury_weather"] = dict(registry["injury_weather_placeholder"])
    return registry


def provider_min_interval_seconds(provider_name: str, config: dict[str, Any] | None = None) -> int:
    providers = (config or {}).get("providers", get_provider_registry())
    provider = providers.get(provider_name, {})
    min_poll = int(provider.get("min_poll_seconds", 30))
    return max(1, min_poll)


def get_provider(provider_name: str) -> dict[str, Any]:
    return get_provider_registry()[provider_name]
