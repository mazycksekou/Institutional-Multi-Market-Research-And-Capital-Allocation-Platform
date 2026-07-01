from __future__ import annotations

from typing import Any, Optional

from fastapi import Depends

from src.providers import PREDICTION_MARKET


def register_market_metadata_routes(
    app: Any,
    *,
    require_action_key: Any,
    provider_router: Any,
) -> None:
    """
    Register compact market metadata and Kalshi read routes.

    Canonical owner: src/api/market_metadata_routes.py
    """
    PROVIDER_ROUTER = provider_router

    @app.get("/api/markets/providers", operation_id="getMarketProviders", dependencies=[Depends(require_action_key)])
    async def get_market_providers():
        return {
            "ok": True,
            "default_provider": PROVIDER_ROUTER.default_market_provider(),
            "providers": PROVIDER_ROUTER.capabilities(PREDICTION_MARKET),
        }


    @app.get("/api/markets/kalshi/events", operation_id="getKalshiEvents", dependencies=[Depends(require_action_key)])
    async def get_kalshi_events(
        status: Optional[str] = None,
        series_ticker: Optional[str] = None,
        limit: int = 100,
    ):
        return await PROVIDER_ROUTER.get_prediction_market_events(status=status, series_ticker=series_ticker, limit=limit)


    @app.get("/api/markets/kalshi/markets", operation_id="getKalshiMarkets", dependencies=[Depends(require_action_key)])
    async def get_kalshi_markets(
        query: Optional[str] = None,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
    ):
        return await PROVIDER_ROUTER.get_prediction_market_markets(
            query=query,
            event_ticker=event_ticker,
            series_ticker=series_ticker,
            status=status,
            limit=limit,
            cursor=cursor,
        )


    @app.get("/api/markets/kalshi/markets/{ticker}/orderbook", operation_id="getKalshiOrderbook", dependencies=[Depends(require_action_key)])
    async def get_kalshi_orderbook(ticker: str):
        return await PROVIDER_ROUTER.get_prediction_market_orderbook(ticker)
