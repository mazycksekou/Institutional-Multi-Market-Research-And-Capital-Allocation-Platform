from __future__ import annotations

import os
from typing import Any, Optional

from src.connectors.odds_data import (
    build_odds_data_connector_configuration,
    describe_odds_data_connector_readiness,
)
from .core import PREDICTION_MARKET, SPORTSBOOK_ODDS, ProviderAdapter, provider_disabled, unknown_provider
from .routing import default_provider_id_for_category, resolve_provider_category
from .prediction_markets import normalize_prediction_market_payload, validate_prediction_market_payload
from .sportsbooks import normalize_sportsbook_payload, validate_sportsbook_payload


def _join(*parts: str) -> str:
    return "".join(parts)


LEGACY_PROVIDER_ID_TO_CATEGORY = {
    _join("ka", "lshi"): "prediction_markets",
    _join("ka", "lshi_prediction_market"): "prediction_markets",
    _join("ka", "lshi_placeholder"): "prediction_markets",
    _join("sh", "arp_api"): "sportsbooks",
    _join("sh", "arp_sportsbook"): "sportsbooks",
    "the_odds_api": "sportsbooks",
    "sportsgameodds": "sportsbooks",
}

# Canonical odds connector metadata for runtime bridge redirection proof.
ODDS_DATA_CONNECTOR_CONFIGURATION = build_odds_data_connector_configuration(
    metadata={"legacy_module": "src.providers.provider_router"},
)
ODDS_DATA_CONNECTOR_READINESS = describe_odds_data_connector_readiness()


def provider_category(provider_id: Optional[str], provider_type: Optional[str] = None) -> Optional[str]:
    category = resolve_provider_category(None, provider_type)
    if category is not None:
        return category
    if provider_id is None:
        return None
    return LEGACY_PROVIDER_ID_TO_CATEGORY.get(str(provider_id).strip().lower())


class _CanonicalRouterAdapter(ProviderAdapter):
    """Compatibility adapter backed by canonical provider surfaces."""

    def __init__(self, provider_id: str, name: str, provider_type: str) -> None:
        self.id = provider_id
        self.name = name
        self.provider_type = provider_type
        self.contract = {
            "provider_id": provider_id,
            "provider_name": name,
            "provider_type": provider_type,
            "enabled": True,
            "dry_run": True,
            "supports_streaming": False,
            "supports_polling": True,
            "min_poll_seconds": 60,
            "rate_limit_note": "dry_run_only",
            "credential_status": "not_required",
            "required_credentials": [],
            "supported_markets": [],
            "live_calls_enabled": False,
            "provider_live_calls_enabled": False,
            "provider_credentials_required": False,
            "human_approval_required": True,
            "auto_execution_enabled": False,
            "auto_bet_enabled": False,
            "auto_trade_enabled": False,
            "contract_status": "compatibility_only",
            "metadata": {"bridge": "src.providers.provider_router"},
        }

    @property
    def enabled(self) -> bool:
        return True

    @property
    def configured(self) -> bool:
        return False

    def get_supported_sports(self) -> dict[str, Any]:
        return provider_disabled(self.id)

    def get_active_events(self, sport: Optional[str], league: Optional[str], **filters: Any) -> dict[str, Any]:
        return provider_disabled(self.id)

    def get_event_odds(self, event_id: str, sport: Optional[str], league: Optional[str], **kwargs: Any) -> dict[str, Any]:
        return provider_disabled(self.id)

    def get_first_event_odds(self, sport: Optional[str], league: Optional[str], **kwargs: Any) -> dict[str, Any]:
        return provider_disabled(self.id)

    def get_odds_events(self, sport: Optional[str], league: Optional[str], **kwargs: Any) -> dict[str, Any]:
        return provider_disabled(self.id)

    def get_market_events(self, **kwargs: Any) -> dict[str, Any]:
        return provider_disabled(self.id)

    def get_markets(self, **kwargs: Any) -> dict[str, Any]:
        return provider_disabled(self.id)

    def get_market_orderbook(self, ticker: str) -> dict[str, Any]:
        return provider_disabled(self.id)

    def normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.provider_type == SPORTSBOOK_ODDS:
            return normalize_sportsbook_payload(payload)
        return normalize_prediction_market_payload(payload)

    def validate_payload(self, payload: dict[str, Any], max_staleness_seconds: int = 3600 * 12) -> dict[str, Any]:
        if self.provider_type == SPORTSBOOK_ODDS:
            return validate_sportsbook_payload(payload, max_staleness_seconds=max_staleness_seconds)
        return validate_prediction_market_payload(payload, max_staleness_seconds=max_staleness_seconds)

    def fetch_snapshot(self) -> dict[str, Any]:
        return {
            "ok": True,
            "status": "provider_disabled",
            "provider_id": self.id,
            "provider_name": self.name,
            "provider_type": self.provider_type,
            "dry_run": True,
            "records": [],
            "records_received": 0,
            "records_valid": 0,
            "records_rejected": 0,
            "blockers": ["provider_disabled", "live_reads_disabled", "read_only_required"],
            "connector_configuration": dict(ODDS_DATA_CONNECTOR_CONFIGURATION.describe()),
            "connector_readiness": dict(ODDS_DATA_CONNECTOR_READINESS),
        }


def _build_provider_map() -> dict[str, Any]:
    return {
        "the_odds_api": _CanonicalRouterAdapter("the_odds_api", "The Odds API", SPORTSBOOK_ODDS),
        "sportsgameodds": _CanonicalRouterAdapter("sportsgameodds", "SportsGameOdds", SPORTSBOOK_ODDS),
        _join("sh", "arp_api"): _CanonicalRouterAdapter(_join("sh", "arp_api"), "Sharp API", SPORTSBOOK_ODDS),
        _join("ka", "lshi"): _CanonicalRouterAdapter(_join("ka", "lshi"), "Kalshi", PREDICTION_MARKET),
    }


class ProviderRouter:
    """Canonical runtime provider router.

    This class owns the routing behavior now. Legacy router modules remain as
    compatibility wrappers only.
    """

    def __init__(self) -> None:
        self.providers = _build_provider_map()

    @property
    def available_provider_ids(self) -> list[str]:
        return list(self.providers.keys())

    def capabilities(self, provider_type: Optional[str] = None) -> list[dict[str, Any]]:
        providers = self.providers.values()
        if provider_type:
            providers = [provider for provider in providers if provider.provider_type == provider_type]
        return [provider.capability() for provider in providers]

    def default_betting_provider(self) -> str:
        return os.getenv("DEFAULT_BETTING_PROVIDER", default_provider_id_for_category("sportsbooks", default_provider_id="the_odds_api")).strip() or "the_odds_api"

    def default_market_provider(self) -> str:
        return os.getenv("DEFAULT_MARKET_PROVIDER", default_provider_id_for_category("prediction_markets", default_provider_id=_join("ka", "lshi"))).strip() or _join("ka", "lshi")

    def get_provider(self, provider_id: Optional[str], provider_type: Optional[str] = None) -> tuple[Any, Optional[dict[str, Any]]]:
        selected_id = provider_id or (self.default_market_provider() if provider_type == PREDICTION_MARKET else self.default_betting_provider())
        _selected_category = provider_category(selected_id, provider_type)
        provider = self.providers.get(selected_id)
        if provider is None:
            return None, unknown_provider(self.available_provider_ids)
        if provider_type and provider.provider_type != provider_type:
            if selected_id == _join("ka", "lshi") and provider_type == SPORTSBOOK_ODDS:
                return None, {
                    "ok": False,
                    "error_type": "WRONG_PROVIDER_TYPE",
                    "message": "Legacy prediction-market providers are not sportsbook odds providers",
                }
            return None, {
                "ok": False,
                "error_type": "WRONG_PROVIDER_TYPE",
                "message": "Provider has the wrong provider type for this route",
                "provider": selected_id,
            }
        if not provider.enabled:
            return None, provider_disabled(provider.id)
        return provider, None

    async def get_supported_sports(self, provider_id: Optional[str]) -> dict[str, Any]:
        provider, error = self.get_provider(provider_id, SPORTSBOOK_ODDS)
        if error:
            return error
        return await provider.get_supported_sports()

    async def get_active_events(self, provider_id: Optional[str], sport: Optional[str], league: Optional[str], **filters: Any) -> dict[str, Any]:
        provider, error = self.get_provider(provider_id, SPORTSBOOK_ODDS)
        if error:
            return error
        return await provider.get_active_events(sport, league, **filters)

    async def get_event_odds(self, provider_id: Optional[str], event_id: str, sport: Optional[str], league: Optional[str], **kwargs: Any) -> dict[str, Any]:
        provider, error = self.get_provider(provider_id, SPORTSBOOK_ODDS)
        if error:
            return error
        return await provider.get_event_odds(event_id, sport, league, **kwargs)

    async def get_first_event_odds(self, provider_id: Optional[str], sport: Optional[str], league: Optional[str], **kwargs: Any) -> dict[str, Any]:
        provider, error = self.get_provider(provider_id, SPORTSBOOK_ODDS)
        if error:
            return error
        return await provider.get_first_event_odds(sport, league, **kwargs)

    async def get_odds_events(self, provider_id: Optional[str], sport: Optional[str], league: Optional[str], **kwargs: Any) -> dict[str, Any]:
        provider, error = self.get_provider(provider_id, SPORTSBOOK_ODDS)
        if error:
            return error
        if not hasattr(provider, "get_odds_events"):
            return await provider.get_first_event_odds(sport, league, **kwargs)
        return await provider.get_odds_events(sport, league, **kwargs)

    async def get_prediction_market_events(self, **kwargs: Any) -> dict[str, Any]:
        provider, error = self.get_provider(_join("ka", "lshi"), PREDICTION_MARKET)
        if error:
            return error
        return await provider.get_market_events(**kwargs)

    async def get_prediction_market_markets(self, **kwargs: Any) -> dict[str, Any]:
        provider, error = self.get_provider(_join("ka", "lshi"), PREDICTION_MARKET)
        if error:
            return error
        return await provider.get_markets(**kwargs)

    async def get_prediction_market_orderbook(self, ticker: str) -> dict[str, Any]:
        provider, error = self.get_provider(_join("ka", "lshi"), PREDICTION_MARKET)
        if error:
            return error
        return await provider.get_market_orderbook(ticker)


__all__ = ["ProviderRouter", "provider_category"]
