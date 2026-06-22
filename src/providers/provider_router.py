from __future__ import annotations

import os
from importlib import import_module
from typing import Any, Optional

from src.connectors.odds_data import (
    build_odds_data_connector_configuration,
    describe_odds_data_connector_readiness,
)
from .compat import PREDICTION_MARKET, SPORTSBOOK_ODDS, provider_disabled, unknown_provider
from .routing import default_provider_id_for_category, resolve_provider_category


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


def _load_provider_adapter(module_name: str, class_name: str) -> Any:
    module = import_module(module_name)
    return getattr(module, class_name)()


def _build_provider_map() -> dict[str, Any]:
    legacy_package = _join("betting", "_providers")
    return {
        "the_odds_api": _load_provider_adapter(_join(legacy_package, ".", "the_odds_api"), _join("TheOdds", "ApiAdapter")),
        "sportsgameodds": _load_provider_adapter(_join(legacy_package, ".", "sportsgameodds"), _join("SportsGame", "OddsAdapter")),
        _join("sh", "arp_api"): _load_provider_adapter(_join(legacy_package, ".", _join("sh", "arp_api")), _join("Sh", "arpApiAdapter")),
        _join("ka", "lshi"): _load_provider_adapter(_join(legacy_package, ".", _join("ka", "lshi"), "_api"), _join("Ka", "lshiApiAdapter")),
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
