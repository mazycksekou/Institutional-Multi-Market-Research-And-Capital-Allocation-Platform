from __future__ import annotations

from typing import Any, Optional

from src.connectors.errors import ConnectorDisabledError
from src.providers.compat import PREDICTION_MARKET, ProviderAdapter
from src.providers.prediction_markets.adapters import normalize_prediction_market_event as normalize_kalshi_event
from src.providers.prediction_markets.adapters import normalize_prediction_market_quote as normalize_kalshi_market


class KalshiApiAdapter(ProviderAdapter):
    id = "kalshi"
    name = "Kalshi"
    provider_type = PREDICTION_MARKET

    def __init__(self) -> None:
        self.base_url = "https://external-api.kalshi.com/trade-api/v2"
        self.api_key_id = ""
        self.private_key = ""

    @property
    def enabled(self) -> bool:
        return False

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    @property
    def private_configured(self) -> bool:
        return False

    def capability(self) -> dict[str, Any]:
        result = super().capability()
        result.update(
            {
                "supports_sports_list": False,
                "supports_events": True,
                "supports_odds": False,
                "supports_props": False,
                "supports_prediction_markets": True,
                "supports_orderbook": True,
            }
        )
        return result

    async def get_supported_sports(self) -> dict[str, Any]:
        raise ConnectorDisabledError("legacy Kalshi API adapter is disabled; use src.connectors.prediction_market_data")

    async def get_market_events(self, status: Optional[str] = None, series_ticker: Optional[str] = None, limit: int = 100) -> dict[str, Any]:
        raise ConnectorDisabledError("legacy Kalshi API adapter is disabled; use src.connectors.prediction_market_data")

    async def get_markets(
        self,
        query: Optional[str] = None,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        raise ConnectorDisabledError("legacy Kalshi API adapter is disabled; use src.connectors.prediction_market_data")

    async def search_markets(self, query: str, limit: int = 100) -> dict[str, Any]:
        raise ConnectorDisabledError("legacy Kalshi API adapter is disabled; use src.connectors.prediction_market_data")

    async def get_market_orderbook(self, ticker: str) -> dict[str, Any]:
        raise ConnectorDisabledError("legacy Kalshi API adapter is disabled; use src.connectors.prediction_market_data")

    def _public_get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        raise ConnectorDisabledError("legacy Kalshi API adapter is disabled; use src.connectors.prediction_market_data")

    def _extract_items(self, raw: Any, key: str) -> list[Any]:
        if isinstance(raw, dict):
            items = raw.get(key) or raw.get("data") or []
            return items if isinstance(items, list) else []
        return raw if isinstance(raw, list) else []


__all__ = [
    "KalshiApiAdapter",
    "normalize_kalshi_event",
    "normalize_kalshi_market",
]
