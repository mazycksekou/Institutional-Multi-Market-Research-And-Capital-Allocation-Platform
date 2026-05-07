import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from openai import OpenAI

from config import load_config, ConfigError
from logger_setup import setup_logger

from main import (
    build_requests_session,
    get_stock_data,
    save_stock_snapshot,
    get_active_events,
    get_first_event_id,
    get_event_odds,
    ask_openai_to_analyze,
    save_analysis_to_csv,
    summarize_bets,
    initialize_bets_csv,
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

try:
    config = load_config()
except ConfigError as error:
    raise RuntimeError(f"Config failed: {error}")

logger = setup_logger(config.app_log_file, config.log_level)
session = build_requests_session()
client = OpenAI(api_key=config.openai_api_key)

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://betting-stock-api-code-integration.onrender.com"
).rstrip("/")

app = FastAPI(
    title="Betting Stock Bot API",
    description="Private API for stock tracking, betting odds, CSV logs, and ChatGPT analysis.",
    version="1.0.0",
    servers=[
        {
            "url": API_BASE_URL
        }
    ]
)

PUBLIC_PATHS = {
    "/",
    "/ping",
    "/ping/",
    "/health",
    "/health/",
    "/docs",
    "/docs/",
    "/openapi.json",
    "/redoc",
    "/redoc/"
}


@app.middleware("http")
async def require_action_key(request: Request, call_next):
    if request.url.path not in PUBLIC_PATHS:
        x_action_key = request.headers.get("x-action-key")

        if not x_action_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing X-Action-Key header."}
            )

        if not secrets.compare_digest(x_action_key, config.action_api_key):
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid action key."}
            )

    return await call_next(request)


@app.get("/ping", operation_id="ping")
def ping():
    return {"ok": True}


@app.get("/", include_in_schema=False)
def root():
    return {
        "status": "ok",
        "service": "betting-stock-api",
        "message": "Use /ping, /health, /docs, or /openapi.json"
    }


@app.get("/health", operation_id="healthCheck")
def health_check():
    return {
        "status": "ok",
        "service": "betting-stock-api",
        "message": "API is running"
    }


@app.get("/stocks/watchlist", operation_id="getWatchlistData")
def api_get_watchlist_data():
    watchlist_data = []

    for ticker in config.default_watchlist:
        stock_data = get_stock_data(
            config=config,
            logger=logger,
            ticker=ticker
        )

        save_stock_snapshot(config, stock_data)
        watchlist_data.append(stock_data)

    return {
        "watchlist": config.default_watchlist,
        "data": watchlist_data
    }


@app.get("/stocks/{ticker}", operation_id="getStockData")
def api_get_stock_data(ticker: str):
    stock_data = get_stock_data(
        config=config,
        logger=logger,
        ticker=ticker.upper()
    )

    save_stock_snapshot(config, stock_data)

    return stock_data


@app.get("/odds/events", operation_id="getActiveBettingEvents")
def api_get_active_events(
    sport: Optional[str] = Query(default=None),
    league: Optional[str] = Query(default=None)
):
    original_sport = config.default_sport
    original_league = config.default_league

    if sport:
        object.__setattr__(config, "default_sport", sport)

    if league:
        object.__setattr__(config, "default_league", league)

    try:
        return get_active_events(config, logger, session)
    finally:
        object.__setattr__(config, "default_sport", original_sport)
        object.__setattr__(config, "default_league", original_league)


@app.get("/odds/first-event", operation_id="getFirstEventOdds")
def api_get_first_event_odds():
    try:
        events_response = get_active_events(config, logger, session)

        if isinstance(events_response, dict):
            events = (
                events_response.get("events")
                or events_response.get("data")
                or []
            )
        else:
            events = events_response or []

        if isinstance(events, dict):
            events = events.get("events") or events.get("data") or []

        if not events:
            return {
                "ok": False,
                "message": "No active betting events found",
                "events_response": events_response,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

        checked_event_ids = []

        for event in events[:10]:
            if not isinstance(event, dict):
                continue

            event_id = (
                event.get("id")
                or event.get("event_id")
                or event.get("game_id")
                or event.get("eventId")
            )

            if not event_id:
                continue

            checked_event_ids.append(event_id)
            odds_response = get_event_odds(config, logger, session, event_id)

            odds_data = None
            if isinstance(odds_response, dict):
                odds_data = (
                    odds_response.get("data")
                    or odds_response.get("odds")
                    or odds_response.get("markets")
                    or odds_response.get("sportsbooks")
                )
            elif isinstance(odds_response, list):
                odds_data = odds_response

            if odds_data:
                return {
                    "ok": True,
                    "event_id": event_id,
                    "event": event,
                    "odds": odds_response,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }

        return {
            "ok": False,
            "message": "No odds available for active events",
            "checked_event_ids": checked_event_ids,
            "sample_event": events[0] if events else None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    except Exception as error:
        return {
            "ok": False,
            "endpoint": "/odds/first-event",
            "error_type": type(error).__name__,
            "error": str(error),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }


@app.get("/analyze", operation_id="analyzeStocksAndOdds")
def api_analyze(
    ticker: Optional[str] = Query(default=None)
):
    selected_ticker = ticker.upper() if ticker else config.default_ticker

    stock_data = get_stock_data(
        config=config,
        logger=logger,
        ticker=selected_ticker
    )

    save_stock_snapshot(config, stock_data)

    watchlist_data = []

    for item in config.default_watchlist:
        item_data = get_stock_data(
            config=config,
            logger=logger,
            ticker=item
        )

        save_stock_snapshot(config, item_data)
        watchlist_data.append(item_data)

    events = get_active_events(config, logger, session)
    event_id = get_first_event_id(events)

    odds_data = {}

    if event_id:
        odds_data = get_event_odds(config, logger, session, event_id)

    analysis = ask_openai_to_analyze(
        config=config,
        logger=logger,
        client=client,
        stock_data=stock_data,
        watchlist_data=watchlist_data,
        odds_data=odds_data
    )

    save_analysis_to_csv(
        config=config,
        stock_data=stock_data,
        odds_data=odds_data,
        analysis_text=analysis
    )

    return {
        "ticker": selected_ticker,
        "stock_data": stock_data,
        "watchlist_data": watchlist_data,
        "odds_data": odds_data,
        "analysis": analysis
    }


@app.get("/bets/summary", operation_id="getBetSummary")
def api_get_bet_summary():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    initialize_bets_csv(config)

    return summarize_bets(config)


from fastapi.openapi.utils import get_openapi


def custom_openapi():
    openapi_schema = get_openapi(
        title="Betting Stock Bot API",
        version="1.0.0",
        description="Private API for stock tracking, betting odds, CSV logs, and ChatGPT analysis.",
        routes=app.routes,
    )

    openapi_schema["servers"] = [
        {
            "url": "https://betting-stock-api-code-integration.onrender.com"
        }
    ]

    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict):
                operation["parameters"] = [
                    p for p in operation.get("parameters", [])
                    if p.get("name") != "x-action-key"
                ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi_schema = None
app.openapi = custom_openapi
