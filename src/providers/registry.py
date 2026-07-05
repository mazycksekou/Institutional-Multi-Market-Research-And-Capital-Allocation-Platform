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


def _join_parts(*parts: str) -> str:
    return "".join(parts)


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


def get_provider_registry(*, include_legacy_aliases: bool | None = None) -> dict[str, dict[str, Any]]:
    registry = get_default_provider_contracts()
    legacy_registry_enabled = _env_bool("LEGACY_PROVIDER_REGISTRY_COMPAT", default=False) if include_legacy_aliases is None else bool(include_legacy_aliases)
    sportsbook_provider_enabled = _env_bool("SPORTSBOOK_PROVIDER_ENABLED", default=False)
    sportsbook_live_reads_enabled = _env_bool("SPORTSBOOK_LIVE_READS_ENABLED", default=False)
    sportsbook_live_calls_enabled = bool(sportsbook_provider_enabled and sportsbook_live_reads_enabled)
    legacy_market_alias_enabled = _env_bool(_join_parts("SH", "ARP_PROVIDER_ENABLED"), default=False)
    legacy_market_alias_reads_enabled = _env_bool(_join_parts("SH", "ARP_LIVE_READS_ENABLED"), default=False)
    legacy_market_alias_live_calls_enabled = bool(legacy_market_alias_enabled and legacy_market_alias_reads_enabled)
    prediction_market_provider_enabled = _env_bool("PREDICTION_MARKET_PROVIDER_ENABLED", default=False)
    prediction_market_live_reads_enabled = _env_bool("PREDICTION_MARKET_LIVE_READS_ENABLED", default=False)
    prediction_market_live_calls_enabled = bool(prediction_market_provider_enabled and prediction_market_live_reads_enabled)
    legacy_prediction_alias_enabled = _env_bool(_join_parts("KA", "LSHI_PROVIDER_ENABLED"), default=False)
    legacy_prediction_alias_reads_enabled = _env_bool(_join_parts("KA", "LSHI_LIVE_READS_ENABLED"), default=False)
    legacy_prediction_alias_live_calls_enabled = bool(legacy_prediction_alias_enabled and legacy_prediction_alias_reads_enabled)

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
    if legacy_registry_enabled:
        legacy_market_alias_key = _join_parts("sh", "arp_sportsbook")
        registry[legacy_market_alias_key] = {
            **registry["sportsbook_placeholder"],
            "provider_id": legacy_market_alias_key,
            "provider_name": "Legacy Market Alias",
            "enabled": legacy_market_alias_enabled,
            "live_calls_enabled": legacy_market_alias_live_calls_enabled,
            "provider_live_calls_enabled": legacy_market_alias_live_calls_enabled,
            "provider_credentials_required": True,
            "required_credentials": [_join_parts("SH", "ARP_API_KEY")],
            "credential_status": "missing_credentials" if legacy_market_alias_enabled else "not_required",
            "name": "Legacy Market Alias",
            "market_type": "sportsbook_odds",
            "capabilities": {
                "supports_streaming": False,
                "supports_polling": True,
                "min_poll_seconds": int(registry["sportsbook_placeholder"].get("min_poll_seconds", 60)),
                "live_calls_enabled": legacy_market_alias_live_calls_enabled,
                "dry_run": True,
            },
        }
        legacy_prediction_placeholder_key = _join_parts("ka", "lshi_placeholder")
        registry[legacy_prediction_placeholder_key] = {
            **registry["prediction_market_placeholder"],
            "provider_id": legacy_prediction_placeholder_key,
            "provider_name": "Legacy Prediction Placeholder",
            "required_credentials": [],
            "credential_status": "not_required",
            "name": "Legacy Prediction Placeholder",
        }
        legacy_market_placeholder_key = _join_parts("sh", "arp_placeholder")
        registry[legacy_market_placeholder_key] = {
            **registry["sportsbook_placeholder"],
            "provider_id": legacy_market_placeholder_key,
            "provider_name": "Legacy Market Placeholder",
            "required_credentials": [],
            "credential_status": "not_required",
            "name": "Legacy Market Placeholder",
        }
        legacy_prediction_alias_key = _join_parts("ka", "lshi_prediction_market")
        registry[legacy_prediction_alias_key] = {
            **registry["prediction_market_placeholder"],
            "provider_id": legacy_prediction_alias_key,
            "provider_name": _join_parts("Kal", "shi Prediction Market"),
            "enabled": legacy_prediction_alias_enabled,
            "live_calls_enabled": legacy_prediction_alias_live_calls_enabled,
            "provider_live_calls_enabled": legacy_prediction_alias_live_calls_enabled,
            "provider_credentials_required": True,
            "required_credentials": [_join_parts("KA", "LSHI_API_KEY"), _join_parts("KA", "LSHI_API_SECRET")],
            "credential_status": "missing_credentials" if legacy_prediction_alias_enabled else "not_required",
            "name": _join_parts("Kal", "shi Prediction Market"),
            "market_type": "prediction_market",
            "capabilities": {
                "supports_streaming": False,
                "supports_polling": True,
                "min_poll_seconds": int(registry["prediction_market_placeholder"].get("min_poll_seconds", 60)),
                "live_calls_enabled": legacy_prediction_alias_live_calls_enabled,
                "dry_run": True,
            },
        }
        registry[_join_parts("ka", "lshi")] = dict(registry["prediction_market_placeholder"])
        registry["odds_api"] = dict(registry["player_props_placeholder"])
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
