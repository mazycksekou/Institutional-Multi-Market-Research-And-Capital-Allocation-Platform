import os
from typing import Any, Optional

import requests

from .base import ProviderAdapter, PREDICTION_MARKET, env_bool, method_not_implemented, provider_not_configured
from .normalization import normalize_kalshi_event, normalize_kalshi_market


class KalshiApiAdapter(ProviderAdapter):
    id = "kalshi"
    name = "Kalshi"
    provider_type = PREDICTION_MARKET

    def __init__(self) -> None:
        env = os.getenv("KALSHI_ENV", "demo").strip().lower()
        default_base = "https://demo-api.kalshi.co/trade-api/v2" if env == "demo" else "https://api.elections.kalshi.com/trade-api/v2"
        self.base_url = os.getenv("KALSHI_BASE_URL", default_base).strip().rstrip("/")
        self.api_key_id = os.getenv("KALSHI_API_KEY_ID", "").strip()
        self.private_key = os.getenv("KALSHI_PRIVATE_KEY", "").strip()

    @property
    def enabled(self) -> bool:
        return env_bool("KALSHI_ENABLED", False)

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    @property
    def private_configured(self) -> bool:
        return bool(self.api_key_id and self.private_key)

    def capability(self) -> dict[str, Any]:
        result = super().capability()
        result.update({
            "supports_sports_list": False,
            "supports_events": True,
            "supports_odds": False,
            "supports_props": False,
            "supports_prediction_markets": True,
            "supports_orderbook": True,
        })
        return result

    async def get_supported_sports(self) -> dict[str, Any]:
        return {
            "ok": False,
            "error_type": "WRONG_PROVIDER_TYPE",
            "message": "Kalshi is a prediction market provider, not a sportsbook odds provider",
        }

    async def get_market_events(self, status: Optional[str] = None, series_ticker: Optional[str] = None, limit: int = 100) -> dict[str, Any]:
        response = self._public_get("/events", {"status": status, "series_ticker": series_ticker, "limit": limit})
        if not response.get("ok"):
            return response
        raw = response.get("raw_response")
        events = self._extract_items(raw, "events")
        return {
            "ok": True,
            "provider": self.id,
            "provider_type": self.provider_type,
            "count": len(events),
            "events": [normalize_kalshi_event(event) for event in events if isinstance(event, dict)],
            "raw_response": raw,
        }

    async def get_markets(
        self,
        query: Optional[str] = None,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        params = {
            "query": query,
            "event_ticker": event_ticker,
            "series_ticker": series_ticker,
            "status": status,
            "limit": limit,
            "cursor": cursor,
        }
        response = self._public_get("/markets", params)
        if not response.get("ok"):
            return response
        raw = response.get("raw_response")
        markets = self._extract_items(raw, "markets")
        return {
            "ok": True,
            "provider": self.id,
            "provider_type": self.provider_type,
            "count": len(markets),
            "markets": [normalize_kalshi_market(market) for market in markets if isinstance(market, dict)],
            "cursor": raw.get("cursor") if isinstance(raw, dict) else None,
            "raw_response": raw,
        }

    async def search_markets(self, query: str, limit: int = 100) -> dict[str, Any]:
        return await self.get_markets(query=query, limit=limit)

    async def get_market_orderbook(self, ticker: str) -> dict[str, Any]:
        response = self._public_get(f"/markets/{ticker}/orderbook", {})
        if response.get("error_type") in {"PROVIDER_ERROR"} and response.get("status_code") in {401, 403}:
            if not self.private_configured:
                return provider_not_configured(self.id)
            return method_not_implemented(self.id, "Kalshi private request signing is not implemented yet")
        if not response.get("ok"):
            return response
        return {
            "ok": True,
            "provider": self.id,
            "provider_type": self.provider_type,
            "market_ticker": ticker,
            "orderbook": response.get("raw_response"),
        }

    def _public_get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.configured:
            return provider_not_configured(self.id)
        try:
            response = requests.get(
                f"{self.base_url}{path}",
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
                "message": "Kalshi request failed",
            }
        if not response.ok:
            return {
                "ok": False,
                "provider": self.id,
                "error_type": "PROVIDER_ERROR",
                "message": f"Kalshi returned HTTP {response.status_code}",
                "status_code": response.status_code,
                "raw_response": raw,
            }
        return {"ok": True, "provider": self.id, "status_code": response.status_code, "raw_response": raw}

    def _extract_items(self, raw: Any, key: str) -> list[Any]:
        if isinstance(raw, dict):
            items = raw.get(key) or raw.get("data") or []
            return items if isinstance(items, list) else []
        return raw if isinstance(raw, list) else []
