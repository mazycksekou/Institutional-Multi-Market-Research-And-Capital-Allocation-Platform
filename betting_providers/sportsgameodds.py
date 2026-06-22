from __future__ import annotations

from typing import Any, Optional

from src.connectors.errors import ConnectorDisabledError
from src.connectors.odds_data import (
    build_odds_data_connector_configuration,
    describe_odds_data_connector_readiness,
)
from src.providers.compat import ProviderAdapter, SPORTSBOOK_ODDS


ODDS_DATA_CONNECTOR_CONFIGURATION = build_odds_data_connector_configuration(
    metadata={"legacy_module": "betting_providers.sportsgameodds"},
)
ODDS_DATA_CONNECTOR_READINESS = describe_odds_data_connector_readiness()


class SportsGameOddsAdapter(ProviderAdapter):
    id = "sportsgameodds"
    name = "SportsGameOdds"
    provider_type = SPORTSBOOK_ODDS

    def __init__(self) -> None:
        self.base_url = ""
        self.api_key = ""

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
                "supports_sports_list": False,
                "supports_events": True,
                "supports_odds": True,
                "supports_props": False,
                "supports_prediction_markets": False,
            }
        )
        return result

    async def get_active_events(
        self,
        sport: Optional[str],
        league: Optional[str],
        **filters: Any,
    ) -> dict[str, Any]:
        raise ConnectorDisabledError("SportsGameOdds live access is disabled; compatibility shell only")
