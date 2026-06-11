from typing import Any, Optional

from fastapi import Depends, Query


def register_stock_analysis_routes(
    app: Any,
    *,
    require_action_key: Any,
    provider_router: Any,
    stock_data_fn: Any,
    no_data_response_fn: Any,
) -> None:
    """
    Register stock/basic analysis routes.

    Canonical owner: src/api/stock_analysis_routes.py
    """
    PROVIDER_ROUTER = provider_router
    stock_data = stock_data_fn
    no_data_response = no_data_response_fn

    @app.get("/api/stocks/{ticker}", operation_id="getStockData", dependencies=[Depends(require_action_key)])
    async def get_stock_data(ticker: str, period: str = "1mo", interval: str = "1d"):
        return stock_data(ticker, period, interval)


    @app.get("/api/watchlist", operation_id="getWatchlistData", dependencies=[Depends(require_action_key)])
    async def get_watchlist_data(
        tickers: str = Query(default="AAPL,NVDA,TSLA,SPY,QQQ"),
        period: str = "1mo",
        interval: str = "1d",
    ):
        symbols = [ticker.strip().upper() for ticker in tickers.split(",") if ticker.strip()]
        return {"ok": True, "tickers": symbols, "data": [stock_data(ticker, period, interval) for ticker in symbols]}


    @app.get("/api/analyze", operation_id="analyzeStocksAndOdds", dependencies=[Depends(require_action_key)])
    async def analyze(ticker: str = "NVDA", league: Optional[str] = None, sport: Optional[str] = None):
        stock = stock_data(ticker, "1mo", "1d")
        odds = no_data_response("sport or league was not supplied, so no betting odds were fetched.", "SPORT_REQUIRED")
        if sport or league:
            odds = await PROVIDER_ROUTER.get_active_events(None, sport, league)
        return {"ok": True, "ticker": ticker.upper(), "stock_data": stock, "odds_data": odds}
