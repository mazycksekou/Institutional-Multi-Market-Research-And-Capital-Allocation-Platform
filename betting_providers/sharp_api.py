import os
from typing import Any, Optional

import requests

from src.providers.compat import ProviderAdapter, SPORTSBOOK_ODDS, env_bool, method_not_implemented, provider_not_configured


class SharpApiAdapter(ProviderAdapter):
    id = "sharp_api"
    name = "Sharp API"
    provider_type = SPORTSBOOK_ODDS

    def __init__(self) -> None:
        self.api_key = os.getenv("SHARP_API_KEY", "").strip()
        self.base_url = os.getenv("SHARP_API_BASE_URL", "").strip().rstrip("/")

    @property
    def enabled(self) -> bool:
        return env_bool("SHARP_API_ENABLED", False)

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

    async def get_supported_sports(self) -> dict[str, Any]:
        return method_not_implemented(self.id, "Sharp API adapter exists, but endpoint mapping is not configured yet")

    async def get_active_events(self, sport: Optional[str], league: Optional[str], **filters: Any) -> dict[str, Any]:
        if not self.configured:
            return provider_not_configured(self.id)
        return self._get("/events", {"sport": sport, "league": league, "limit": filters.get("limit", 20)})

    async def get_event_odds(self, event_id: str, sport: Optional[str], league: Optional[str], **_: Any) -> dict[str, Any]:
        if not self.configured:
            return provider_not_configured(self.id)
        return self._get(f"/events/{event_id}/odds", {"sportsbook": "draftkings,fanduel,betmgm", "market": "moneyline", "limit": 50})

    async def get_first_event_odds(self, sport: Optional[str], league: Optional[str], **filters: Any) -> dict[str, Any]:
        events = await self.get_active_events(sport, league, **filters)
        if not events.get("ok"):
            return events
        data = events.get("data") or []
        if not data:
            return {
                "ok": False,
                "error_type": "NO_DATA",
                "provider": self.id,
                "message": "No Sharp API events returned for requested filters",
            }
        event_id = data[0].get("id") or data[0].get("event_id")
        if not event_id:
            return method_not_implemented(self.id, "Sharp API adapter exists, but endpoint mapping is not configured yet")
        return await self.get_event_odds(str(event_id), sport, league)

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.get(
                f"{self.base_url}{path}",
                headers={"X-API-Key": self.api_key},
                params={k: v for k, v in params.items() if v not in (None, "")},
                timeout=8,
            )
            try:
                raw = response.json()
            except ValueError:
                raw = {"text": response.text}
        except Exception as error:
            return {
                "ok": False,
                "provider": self.id,
                "error_type": type(error).__name__,
                "message": "Sharp API request failed",
            }
        data = raw.get("data") if isinstance(raw, dict) else raw
        return {
            "ok": response.ok,
            "provider": self.id,
            "provider_type": self.provider_type,
            "status_code": response.status_code,
            "data": data,
            "raw_response": raw,
            "message": "Sharp API request completed" if response.ok else f"Sharp API returned HTTP {response.status_code}",
            "error_type": None if response.ok else "PROVIDER_ERROR",
        }
