from __future__ import annotations

from typing import Any, Optional

from src.connectors.errors import ConnectorDisabledError
from src.connectors.odds_data import (
    build_odds_data_connector_configuration,
    describe_odds_data_connector_readiness,
)
from src.providers.compat import ProviderAdapter, SPORTSBOOK_ODDS


ODDS_DATA_CONNECTOR_CONFIGURATION = build_odds_data_connector_configuration(
    metadata={"legacy_module": "betting_providers.the_odds_api"},
)
ODDS_DATA_CONNECTOR_READINESS = describe_odds_data_connector_readiness()


class TheOddsApiAdapter(ProviderAdapter):
    id = "the_odds_api"
    name = "The Odds API"
    provider_type = SPORTSBOOK_ODDS

    def __init__(self) -> None:
        self.base_url = ""
        self.api_key = ""
        self.default_bookmakers = "draftkings,fanduel,betmgm,caesars,espnbet,bet365"
        self.default_regions = "us"
        self.default_markets = "h2h,spreads,totals"
        self._sports_cache: tuple[float, Any] | None = None

    @property
    def enabled(self) -> bool:
        return False

    @property
    def configured(self) -> bool:
        return False

    def capability(self) -> dict[str, Any]:
        result = super().capability()
        result.update(
            {
                "supports_sports_list": True,
                "supports_events": True,
                "supports_odds": True,
                "supports_props": False,
                "supports_prediction_markets": False,
            }
        )
        return result

    async def get_supported_sports(self) -> dict[str, Any]:
        raise ConnectorDisabledError("The Odds API live access is disabled; compatibility shell only")

    async def get_odds_events(
        self,
        sport: Optional[str],
        league: Optional[str],
        markets: Optional[str] = None,
        bookmakers: Optional[str] = None,
        regions: Optional[str] = None,
        odds_format: str = "american",
        limit: Optional[int] = None,
    ) -> dict[str, Any]:
        raise ConnectorDisabledError("The Odds API live access is disabled; compatibility shell only")

    async def get_active_events(self, sport: Optional[str], league: Optional[str], **filters: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("The Odds API live access is disabled; compatibility shell only")

    async def get_event_odds(
        self,
        event_id: str,
        sport: Optional[str],
        league: Optional[str],
        markets: Optional[str] = None,
        bookmakers: Optional[str] = None,
    ) -> dict[str, Any]:
        raise ConnectorDisabledError("The Odds API live access is disabled; compatibility shell only")

    async def get_first_event_odds(self, sport: Optional[str], league: Optional[str], **kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("The Odds API live access is disabled; compatibility shell only")
