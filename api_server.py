import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from openai import OpenAI

from config import load_config, ConfigError
from kalshi_client import KALSHI_BASE_URL
from logger_setup import setup_logger
from odds_providers import lookup_provider_odds
from sharp_client import get_sharp_active_events

from main import (
    build_requests_session,
    get_stock_data,
    save_stock_snapshot,
    get_first_event_id,
    get_event_odds,
    ask_openai_to_analyze,
    save_analysis_to_csv,
    summarize_bets,
    initialize_bets_csv,
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
# Render's local filesystem can be temporary between deploys. CSV files are a
# fallback for now; a future DATABASE_URL-backed store can replace them safely.

ACTIVE_EVENTS_CACHE: dict[str, Any] = {
    "timestamp": 0,
    "key": None,
    "value": None,
}

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
        if not config.action_api_key:
            return JSONResponse(
                status_code=500,
                content={"ok": False, "message": "ACTION_API_KEY is not configured."}
            )

        x_action_key = request.headers.get("x-action-key")

        if not x_action_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing X-Action-Key header."}
            )

        if not secrets.compare_digest(x_action_key, config.action_api_key):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid action key."}
            )

    return await call_next(request)


def error_response(endpoint: str, error: Exception, message: str) -> dict[str, Any]:
    response = {
        "ok": False,
        "endpoint": endpoint,
        "error_type": type(error).__name__,
        "error": str(error),
        "message": message,
    }

    if os.getenv("DEBUG", "").lower() == "true":
        import traceback
        response["traceback"] = traceback.format_exc()

    return response


def get_cached_active_events() -> dict[str, Any]:
    cache_key = f"{config.default_sport}:{config.default_league}"
    now = time.time()

    if (
        ACTIVE_EVENTS_CACHE["key"] == cache_key
        and ACTIVE_EVENTS_CACHE["value"] is not None
        and now - ACTIVE_EVENTS_CACHE["timestamp"] < 30
    ):
        return ACTIVE_EVENTS_CACHE["value"]

    events_response = get_sharp_active_events(
        api_key=config.sharp_api_key,
        sport=config.default_sport,
        league=config.default_league,
        session=session,
        limit=20
    )
    ACTIVE_EVENTS_CACHE.update({
        "timestamp": now,
        "key": cache_key,
        "value": events_response,
    })
    return events_response


def extract_events(events_response: Any) -> list[dict[str, Any]]:
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

    return [event for event in events if isinstance(event, dict)]


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    external_ids = event.get("external_ids") or {}
    provider_hint = None

    if external_ids.get("kalshi") or "kalshi" in [str(book).lower() for book in event.get("books", [])]:
        provider_hint = "kalshi"
    elif external_ids:
        provider_hint = next(iter(external_ids.keys()))

    return {
        "id": event.get("id") or event.get("event_id") or event.get("game_id") or event.get("eventId"),
        "uuid": event.get("uuid"),
        "external_ids": external_ids,
        "sport": event.get("sport"),
        "league": event.get("league"),
        "home_team": event.get("home_team"),
        "away_team": event.get("away_team"),
        "start_time": event.get("start_time") or event.get("startTime"),
        "status": event.get("status"),
        "is_live": event.get("is_live") or event.get("isLive"),
        "book_count": event.get("book_count"),
        "market_count": event.get("market_count"),
        "markets": event.get("markets"),
        "books": event.get("books"),
        "provider_hint": provider_hint,
    }


def build_provider_candidates(event: dict[str, Any]) -> list[dict[str, str]]:
    internal_id = event.get("id") or event.get("event_id") or event.get("game_id") or event.get("eventId")
    uuid = event.get("uuid")
    external_ids = event.get("external_ids") or {}
    possible_ids = []

    for key in ("kalshi", "fanduel"):
        if external_ids.get(key):
            possible_ids.append({
                "provider_hint": key,
                "odds_lookup_id": str(external_ids[key])
            })

    for provider_name, provider_id in external_ids.items():
        if provider_id:
            possible_ids.append({
                "provider_hint": str(provider_name),
                "odds_lookup_id": str(provider_id)
            })

    if uuid:
        possible_ids.append({"provider_hint": "uuid", "odds_lookup_id": str(uuid)})

    if internal_id:
        possible_ids.append({"provider_hint": "internal_id", "odds_lookup_id": str(internal_id)})

    seen = set()
    deduped = []
    for item in possible_ids:
        odds_lookup_id = item["odds_lookup_id"]
        if odds_lookup_id in seen:
            continue
        seen.add(odds_lookup_id)
        deduped.append(item)

    return deduped


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


@app.get("/debug/config", operation_id="getDebugConfig")
def api_get_debug_config():
    return {
        "ok": True,
        "environment": {
            "ACTION_API_KEY": bool(os.getenv("ACTION_API_KEY")),
            "API_BASE_URL": bool(os.getenv("API_BASE_URL")),
            "SHARP_API_KEY": bool(os.getenv("SHARP_API_KEY")),
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "KALSHI_BASE_URL": bool(KALSHI_BASE_URL),
            "KALSHI_API_KEY_ID": bool(os.getenv("KALSHI_API_KEY_ID")),
            "KALSHI_PRIVATE_KEY_PEM": bool(os.getenv("KALSHI_PRIVATE_KEY_PEM")),
        },
        "base_url": "https://betting-stock-api-code-integration.onrender.com"
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
        events_response = get_cached_active_events()
        events = extract_events(events_response)

        return {
            "ok": events_response.get("ok", bool(events)) if isinstance(events_response, dict) else bool(events),
            "raw_response": events_response.get("raw_response", events_response) if isinstance(events_response, dict) else events_response,
            "events": [normalize_event(event) for event in events],
            "count": len(events),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    finally:
        object.__setattr__(config, "default_sport", original_sport)
        object.__setattr__(config, "default_league", original_league)


@app.get("/odds/first-event", operation_id="getFirstEventOdds")
def api_get_first_event_odds():
    start_time = time.time()
    max_elapsed_seconds = 10
    checked_event_ids = []
    checked_provider_ids = []
    lookup_results = []

    try:
        events_response = get_cached_active_events()
        events = extract_events(events_response)

        if not events:
            return {
                "ok": False,
                "message": "No active betting events found",
                "events_response": events_response,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "elapsed_seconds": round(time.time() - start_time, 2)
            }

        for event in events[:3]:
            if time.time() - start_time >= max_elapsed_seconds - 1:
                break

            if not isinstance(event, dict):
                continue

            internal_id = (
                event.get("id")
                or event.get("event_id")
                or event.get("game_id")
                or event.get("eventId")
            )

            if internal_id:
                checked_event_ids.append(str(internal_id))

            deduped_possible_ids = build_provider_candidates(event)

            for item in deduped_possible_ids[:3]:
                remaining_seconds = max_elapsed_seconds - (time.time() - start_time)
                if remaining_seconds <= 1:
                    return {
                        "ok": False,
                        "message": "No odds available within quick lookup limit",
                        "checked_event_ids": checked_event_ids,
                        "checked_provider_ids": checked_provider_ids,
                        "lookup_results": lookup_results,
                        "sample_event": events[0] if events else None,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "elapsed_seconds": round(time.time() - start_time, 2)
                    }

                odds_id = item["odds_lookup_id"]
                provider_hint = item["provider_hint"]
                checked_provider_ids.append(odds_id)

                try:
                    logger.info(f"Trying odds provider={provider_hint} lookup_id={odds_id}")
                    odds_response = lookup_provider_odds(
                        provider_hint=provider_hint,
                        lookup_id=odds_id,
                        sharp_api_key=config.sharp_api_key,
                        session=session
                    )
                    has_actual_odds = bool(odds_response.get("has_actual_odds"))
                    result_type = odds_response.get("result_type") or "no_data"
                    message = odds_response.get("message")
                    has_data = bool(has_actual_odds or odds_response.get("market") or odds_response.get("data"))

                    lookup_results.append({
                        "event_id": internal_id,
                        "provider_hint": provider_hint,
                        "odds_lookup_id": odds_id,
                        "has_data": has_data,
                        "raw_response": odds_response,
                        "error_type": odds_response.get("error_type"),
                        "error": odds_response.get("error")
                    })

                    if has_data:
                        response = {
                            "ok": True,
                            "event_id": internal_id,
                            "provider_hint": provider_hint,
                            "odds_lookup_id": odds_id,
                            "result_type": result_type,
                            "has_actual_odds": has_actual_odds,
                            "event": event,
                            "odds": odds_response,
                            "lookup_results": lookup_results,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                            "elapsed_seconds": round(time.time() - start_time, 2)
                        }

                        if message:
                            response["message"] = message

                        return response

                except Exception as lookup_error:
                    lookup_results.append({
                        "event_id": internal_id,
                        "provider_hint": provider_hint,
                        "odds_lookup_id": odds_id,
                        "has_data": False,
                        "error_type": type(lookup_error).__name__,
                        "error": str(lookup_error)
                    })

        return {
            "ok": False,
            "message": "No usable odds or market snapshot available within quick lookup limit",
            "checked_event_ids": checked_event_ids,
            "checked_provider_ids": checked_provider_ids,
            "lookup_results": lookup_results,
            "sample_event": events[0] if events else None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(time.time() - start_time, 2)
        }

    except Exception as error:
        return {
            "ok": False,
            "endpoint": "/odds/first-event",
            "error_type": type(error).__name__,
            "error": str(error),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(time.time() - start_time, 2)
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

    events = get_cached_active_events()
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
