from __future__ import annotations

from typing import Any, Optional

from src.connectors.errors import ConnectorDisabledError
from src.connectors.odds_data import (
    build_odds_data_connector_configuration,
    describe_odds_data_connector_readiness,
)
from src.providers.compat import ProviderAdapter, SPORTSBOOK_ODDS


ODDS_DATA_CONNECTOR_CONFIGURATION = build_odds_data_connector_configuration(
    metadata={"legacy_module": "betting_providers.sharp_api"},
)
ODDS_DATA_CONNECTOR_READINESS = describe_odds_data_connector_readiness()


class SharpApiAdapter(ProviderAdapter):
    id = "sharp_api"
    name = "Sharp API"
    provider_type = SPORTSBOOK_ODDS

    def __init__(self) -> None:
        self.api_key = ""
        self.base_url = ""

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

    async def get_supported_sports(self) -> dict[str, Any]:
        raise ConnectorDisabledError("Sharp API live access is disabled; compatibility shell only")

    async def get_active_events(self, sport: Optional[str], league: Optional[str], **filters: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("Sharp API live access is disabled; compatibility shell only")

    async def get_event_odds(self, event_id: str, sport: Optional[str], league: Optional[str], **_: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("Sharp API live access is disabled; compatibility shell only")

    async def get_first_event_odds(self, sport: Optional[str], league: Optional[str], **filters: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("Sharp API live access is disabled; compatibility shell only")
