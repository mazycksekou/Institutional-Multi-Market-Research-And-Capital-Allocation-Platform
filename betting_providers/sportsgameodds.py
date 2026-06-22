import os
from typing import Any, Optional

import httpx

from src.connectors.odds_data import (
    build_odds_data_connector_configuration,
    describe_odds_data_connector_readiness,
)
from src.providers.compat import ProviderAdapter, SPORTSBOOK_ODDS, clean_error, env_bool, provider_not_configured

# Canonical odds connector metadata for delete-proof redirection.
ODDS_DATA_CONNECTOR_CONFIGURATION = build_odds_data_connector_configuration(
    metadata={"legacy_module": "betting_providers.sportsgameodds"},
)
ODDS_DATA_CONNECTOR_READINESS = describe_odds_data_connector_readiness()


class SportsGameOddsAdapter(ProviderAdapter):
    id = "sportsgameodds"
    name = "SportsGameOdds"
    provider_type = SPORTSBOOK_ODDS

    def __init__(self) -> None:
        self.base_url = os.getenv("SPORTSGAMEODDS_BASE_URL", "https://api.sportsgameodds.com").rstrip("/")
        self.api_key = (os.getenv("SPORTSGAMEODDS_API_KEY") or "").strip()

    @property
    def enabled(self) -> bool:
        return env_bool("SPORTSGAMEODDS_ENABLED", True)

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    def capability(self) -> dict[str, Any]:
        result = super().capability()
        result.update({
            "supports_sports_list": False,
            "supports_events": True,
            "supports_odds": True,
            "supports_props": False,
            "supports_prediction_markets": False,
        })
        return result

    async def get_active_events(
        self,
        sport: Optional[str],
        league: Optional[str],
        **filters: Any,
    ) -> dict[str, Any]:
        if not self.configured:
            return provider_not_configured(self.id)
        limit = filters.get("limit") or filters.get("page_size") or 10
        try:
            limit_value = max(1, min(int(limit), 100))
        except (TypeError, ValueError):
            limit_value = 10
        params = {"oddsAvailable": "true", "limit": limit_value}
        headers = {
            "x-api-key": self.api_key,
            "Accept": "application/json",
            "User-Agent": "betting-stock-api/1.0",
        }
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(f"{self.base_url}/v1/events/", params=params, headers=headers)
        except Exception as error:
            return clean_error("PROVIDER_ERROR", f"SportsGameOdds request failed: {error}", provider=self.id)
        try:
            raw = response.json()
        except ValueError:
            raw = {"text": response.text}
        if not response.is_success:
            return clean_error(
                "PROVIDER_ERROR",
                f"SportsGameOdds returned HTTP {response.status_code}.",
                provider=self.id,
                status_code=response.status_code,
                raw_response=raw,
            )
        events = raw.get("data") if isinstance(raw, dict) and isinstance(raw.get("data"), list) else raw
        count = len(events) if isinstance(events, list) else 0
        return {
            "ok": True,
            "result_type": "events",
            "provider": self.id,
            "provider_type": self.provider_type,
            "source": self.name,
            "count": count,
            "events": events if isinstance(events, list) else [],
            "raw_response": raw,
        }
