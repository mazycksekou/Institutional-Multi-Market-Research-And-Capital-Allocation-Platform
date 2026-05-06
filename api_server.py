import secrets
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query
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

try:
    config = load_config()
except ConfigError as error:
    raise RuntimeError(f"Config failed: {error}")

logger = setup_logger(config.app_log_file, config.log_level)
session = build_requests_session()
client = OpenAI(api_key=config.openai_api_key)

app = FastAPI(
    title="Betting Stock Bot API",
    description="Private API for stock tracking, betting odds, CSV logs, and ChatGPT analysis.",
    version="1.0.0",
    servers=[
        {"url": config.api_base_url}
    ],
)


def verify_action_key(x_action_key: Optional[str] = Header(default=None)):
    if not x_action_key:
        raise HTTPException(status_code=401, detail="Missing X-Action-Key header.")

    if not secrets.compare_digest(x_action_key, config.action_api_key):
        raise HTTPException(status_code=403, detail="Invalid action key.")


@app.get("/health", operation_id="healthCheck")
def health_check():
    return {
        "status": "ok",
        "service": "betting-stock-bot"
    }


@app.get("/stocks/{ticker}", operation_id="getStockData")
def api_get_stock_data(
    ticker: str,
    x_action_key: Optional[str] = Header(default=None)
):
    verify_action_key(x_action_key)

    stock_data = get_stock_data(
        config=config,
        logger=logger,
        ticker=ticker.upper()
    )

    save_stock_snapshot(config, stock_data)

    return stock_data


@app.get("/stocks/watchlist", operation_id="getWatchlistData")
def api_get_watchlist_data(
    x_action_key: Optional[str] = Header(default=None)
):
    verify_action_key(x_action_key)

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


@app.get("/odds/events", operation_id="getActiveBettingEvents")
def api_get_active_events(
    sport: Optional[str] = Query(default=None),
    league: Optional[str] = Query(default=None),
    x_action_key: Optional[str] = Header(default=None)
):
    verify_action_key(x_action_key)

    original_sport = config.default_sport
    original_league = config.default_league

    if sport:
        object.__setattr__(config, "default_sport", sport)

    if league:
        object.__setattr__(config, "default_league", league)

    events = get_active_events(config, logger, session)

    object.__setattr__(config, "default_sport", original_sport)
    object.__setattr__(config, "default_league", original_league)

    return events


@app.get("/odds/first-event", operation_id="getFirstEventOdds")
def api_get_first_event_odds(
    x_action_key: Optional[str] = Header(default=None)
):
    verify_action_key(x_action_key)

    events = get_active_events(config, logger, session)
    event_id = get_first_event_id(events)

    if not event_id:
        return {
            "error": "No event ID found.",
            "events_response": events
        }

    odds_data = get_event_odds(config, logger, session, event_id)

    return {
        "event_id": event_id,
        "odds": odds_data
    }


@app.get("/analyze", operation_id="analyzeStocksAndOdds")
def api_analyze(
    ticker: str = Query(default=None),
    x_action_key: Optional[str] = Header(default=None)
):
    verify_action_key(x_action_key)

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
def api_get_bet_summary(
    x_action_key: Optional[str] = Header(default=None)
):
    verify_action_key(x_action_key)

    initialize_bets_csv(config)

    return summarize_bets(config)