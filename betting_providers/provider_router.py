from __future__ import annotations

from typing import Any

from src.providers.provider_router import ProviderRouter as _CanonicalProviderRouter
from src.providers.provider_router import provider_category


class ProviderRouter(_CanonicalProviderRouter):
    async def get_kalshi_events(self, **kwargs: Any) -> dict[str, Any]:
        return await self.get_prediction_market_events(**kwargs)

    async def get_kalshi_markets(self, **kwargs: Any) -> dict[str, Any]:
        return await self.get_prediction_market_markets(**kwargs)

    async def get_kalshi_orderbook(self, ticker: str) -> dict[str, Any]:
        return await self.get_prediction_market_orderbook(ticker)


__all__ = ["ProviderRouter", "provider_category"]
