import os
from typing import Any, Optional

from .base import PREDICTION_MARKET, SPORTSBOOK_ODDS, provider_disabled, unknown_provider
from .kalshi_api import KalshiApiAdapter
from .sharp_api import SharpApiAdapter
from .sportsgameodds import SportsGameOddsAdapter
from .the_odds_api import TheOddsApiAdapter


class ProviderRouter:
    def __init__(self) -> None:
        self.providers = {
            "the_odds_api": TheOddsApiAdapter(),
            "sportsgameodds": SportsGameOddsAdapter(),
            "sharp_api": SharpApiAdapter(),
            "kalshi": KalshiApiAdapter(),
        }

    @property
    def available_provider_ids(self) -> list[str]:
        return list(self.providers.keys())

    def capabilities(self, provider_type: Optional[str] = None) -> list[dict[str, Any]]:
        providers = self.providers.values()
        if provider_type:
            providers = [provider for provider in providers if provider.provider_type == provider_type]
        return [provider.capability() for provider in providers]

    def default_betting_provider(self) -> str:
        return os.getenv("DEFAULT_BETTING_PROVIDER", "the_odds_api").strip() or "the_odds_api"

    def default_market_provider(self) -> str:
        return os.getenv("DEFAULT_MARKET_PROVIDER", "kalshi").strip() or "kalshi"

    def get_provider(self, provider_id: Optional[str], provider_type: Optional[str] = None) -> tuple[Any, Optional[dict[str, Any]]]:
        selected_id = provider_id or (self.default_market_provider() if provider_type == PREDICTION_MARKET else self.default_betting_provider())
        provider = self.providers.get(selected_id)
        if provider is None:
            return None, unknown_provider(self.available_provider_ids)
        if provider_type and provider.provider_type != provider_type:
            if selected_id == "kalshi" and provider_type == SPORTSBOOK_ODDS:
                return None, {
                    "ok": False,
                    "error_type": "WRONG_PROVIDER_TYPE",
                    "message": "Kalshi is a prediction market provider, not a sportsbook odds provider",
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

    async def get_kalshi_events(self, **kwargs: Any) -> dict[str, Any]:
        provider, error = self.get_provider("kalshi", PREDICTION_MARKET)
        if error:
            return error
        return await provider.get_market_events(**kwargs)

    async def get_kalshi_markets(self, **kwargs: Any) -> dict[str, Any]:
        provider, error = self.get_provider("kalshi", PREDICTION_MARKET)
        if error:
            return error
        return await provider.get_markets(**kwargs)

    async def get_kalshi_orderbook(self, ticker: str) -> dict[str, Any]:
        provider, error = self.get_provider("kalshi", PREDICTION_MARKET)
        if error:
            return error
        return await provider.get_market_orderbook(ticker)
