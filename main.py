import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import logging
import pandas as pd
import requests
import yfinance as yf
from openai import OpenAI
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import Config, load_config, ConfigError
from logger_setup import setup_logger

try:
    config = load_config()
except ConfigError as error:
    raise RuntimeError(f"Config failed: {error}")

logger = setup_logger(config.app_log_file, config.log_level)


def build_requests_session() -> requests.Session:
    """Build and return a configured requests session."""
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session

def get_stock_data(config: Config, logger: logging.Logger, ticker: str, period: str = None, interval: str = None) -> Dict[str, Any]:
    """Get stock data for a ticker."""
    if period is None:
        period = config.default_period
    if interval is None:
        interval = config.default_interval

    logger.info(f"Fetching stock data for {ticker} (period: {period}, interval: {interval})")

    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period, interval=interval)

        if history.empty:
            logger.warning(f"No stock data found for {ticker}")
            return {
                "ticker": ticker.upper(),
                "error": f"No stock data found for {ticker}"
            }

        latest = history.tail(1)

        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "ticker": ticker.upper(),
            "last_open": float(latest["Open"].iloc[0]),
            "last_high": float(latest["High"].iloc[0]),
            "last_low": float(latest["Low"].iloc[0]),
            "last_close": float(latest["Close"].iloc[0]),
            "volume": int(latest["Volume"].iloc[0]),
            "period": period,
            "interval": interval,
            "recent_history": history[["Open", "High", "Low", "Close", "Volume"]]
                .tail(5)
                .to_dict(orient="index")
        }
    except Exception as e:
        logger.error(f"Error fetching stock data for {ticker}: {e}")
        return {
            "ticker": ticker.upper(),
            "error": str(e)
        }

def save_stock_snapshot(config: Config, stock_data: Dict[str, Any]) -> None:
    """Save stock snapshot to CSV."""
    if stock_data.get("error"):
        row = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "ticker": stock_data.get("ticker"),
            "error": stock_data.get("error")
        }
    else:
        row = {
            "timestamp": stock_data["timestamp"],
            "ticker": stock_data["ticker"],
            "open": stock_data["last_open"],
            "high": stock_data["last_high"],
            "low": stock_data["last_low"],
            "close": stock_data["last_close"],
            "volume": stock_data["volume"],
            "period": stock_data["period"],
            "interval": stock_data["interval"]
        }

    df = pd.DataFrame([row])
    df.to_csv(
        config.stock_log_file,
        mode="a",
        header=not Path(config.stock_log_file).exists(),
        index=False
    )

def get_active_events(config: Config, logger: logging.Logger, session: requests.Session) -> Dict[str, Any]:
    """Get active betting events."""
    url = "https://api.sharpapi.io/api/v1/events"
    headers = {"X-API-Key": config.sharp_api_key}
    params = {
        "sport": config.default_sport,
        "league": config.default_league,
        "limit": 20
    }

    logger.info(f"Fetching active events for {config.default_sport}/{config.default_league}")

    try:
        response = session.get(url, headers=headers, params=params, timeout=config.request_timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching active events: {e}")
        return {"error": str(e)}

def get_event_odds(config: Config, logger: logging.Logger, session: requests.Session, event_id: str) -> Dict[str, Any]:
    """Get odds for a specific event."""
    url = f"https://api.sharpapi.io/api/v1/events/{event_id}/odds"
    headers = {"X-API-Key": config.sharp_api_key}
    params = {
        "sportsbook": "draftkings,fanduel,betmgm",
        "market": "moneyline",
        "limit": 50
    }

    logger.info(f"Fetching odds for event {event_id}")

    try:
        response = session.get(url, headers=headers, params=params, timeout=config.request_timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching event odds for {event_id}: {e}")
        return {"error": str(e)}

def get_first_event_id(events_response: Dict[str, Any]) -> str:
    """Extract the first event ID from events response."""
    if not isinstance(events_response, dict):
        return None

    events = events_response.get("data", [])

    if not events:
        return None

    first_event = events[0]

    return (
        first_event.get("id")
        or first_event.get("event_id")
        or first_event.get("eventId")
    )

def ask_openai_to_analyze(config: Config, logger: logging.Logger, client: OpenAI, stock_data: Dict, watchlist_data: List[Dict], odds_data: Dict) -> str:
    """Analyze stock and odds data using OpenAI."""
    def make_serializable(value):
        if isinstance(value, dict):
            return {str(k): make_serializable(v) for k, v in value.items()}
        if isinstance(value, list):
            return [make_serializable(v) for v in value]
        if isinstance(value, tuple):
            return [make_serializable(v) for v in value]
        if hasattr(value, "to_dict") and not isinstance(value, str):
            try:
                return make_serializable(value.to_dict())
            except Exception:
                pass
        if hasattr(value, "tolist") and not isinstance(value, str):
            try:
                return make_serializable(value.tolist())
            except Exception:
                pass
        try:
            json.dumps(value)
            return value
        except TypeError:
            return str(value)

    def compact_json(data, max_chars=6000):
        serializable_data = make_serializable(data)
        text = json.dumps(serializable_data, default=str)
        if len(text) > max_chars:
            return text[:max_chars] + "...TRUNCATED"
        return text

    prompt = f"""
Analyze this information like a practical betting and stock research assistant.

Main stock:
{compact_json(stock_data)}

Watchlist:
{compact_json(watchlist_data)}

Betting odds:
{compact_json(odds_data)}

Return this format:

1. Stock summary
2. Watchlist strength ranking
3. Betting market summary
4. Best value warning
5. No-bet warning
6. Risk level
7. What to track next
"""

    logger.info("Requesting analysis from OpenAI")

    try:
        response = client.chat.completions.create(
            model=config.openai_model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error getting OpenAI analysis: {e}")
        return f"Error: {str(e)}"

def save_analysis_to_csv(config: Config, stock_data: Dict, odds_data: Dict, analysis_text: str) -> None:
    """Save analysis to CSV."""
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "ticker": stock_data.get("ticker"),
        "last_open": stock_data.get("last_open"),
        "last_close": stock_data.get("last_close"),
        "volume": stock_data.get("volume"),
        "sport": config.default_sport,
        "league": config.default_league,
        "odds_json": json.dumps(odds_data, default=str)[:10000],  # Truncate if too long
        "analysis": analysis_text
    }

    df = pd.DataFrame([row])
    df.to_csv(
        config.analysis_log_file,
        mode="a",
        header=not Path(config.analysis_log_file).exists(),
        index=False
    )

def initialize_bets_csv(config: Config) -> None:
    """Initialize bets CSV if it doesn't exist."""
    bets_file_path = Path(config.bets_file)
    if bets_file_path.exists():
        return

    columns = [
        "date",
        "sport",
        "league",
        "game",
        "market",
        "pick",
        "odds_taken",
        "stake",
        "result",
        "profit_loss",
        "closing_odds",
        "sportsbook",
        "notes"
    ]

    pd.DataFrame(columns=columns).to_csv(bets_file_path, index=False)

def summarize_bets(config: Config) -> Dict[str, Any]:
    """Summarize betting results."""
    initialize_bets_csv(config)

    bets_file_path = Path(config.bets_file)
    if not bets_file_path.exists():
        return {"message": "No bets logged yet."}

    df = pd.read_csv(bets_file_path)

    if df.empty:
        return {"message": "No bets logged yet."}

    df["stake"] = pd.to_numeric(df["stake"], errors="coerce").fillna(0)
    df["profit_loss"] = pd.to_numeric(df["profit_loss"], errors="coerce").fillna(0)

    total_staked = df["stake"].sum()
    total_profit = df["profit_loss"].sum()
    total_bets = len(df)
    winning_bets = len(df[df["profit_loss"] > 0])
    losing_bets = len(df[df["profit_loss"] < 0])

    win_rate = (winning_bets / total_bets * 100) if total_bets > 0 else 0
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

    return {
        "total_bets": total_bets,
        "winning_bets": winning_bets,
        "losing_bets": losing_bets,
        "win_rate_percent": round(win_rate, 2),
        "total_staked": round(total_staked, 2),
        "total_profit": round(total_profit, 2),
        "roi_percent": round(roi, 2),
        "recent_bets": df.tail(5).to_dict(orient="records")
    }


def read_large_csv_in_chunks(file_path, chunksize=10000):
    for chunk in pd.read_csv(file_path, chunksize=chunksize):
        print(chunk.tail())


if __name__ == "__main__":
    session = build_requests_session()
    initialize_bets_csv(config)

    main_stock_data = get_stock_data(
        config=config,
        logger=logger,
        ticker=config.default_ticker
    )
    save_stock_snapshot(config, main_stock_data)

    watchlist_data = []
    for ticker in config.default_watchlist:
        ticker_data = get_stock_data(
            config=config,
            logger=logger,
            ticker=ticker
        )
        save_stock_snapshot(config, ticker_data)
        watchlist_data.append(ticker_data)

    events = get_active_events(config, logger, session)
    odds_data = {}

    event_id = get_first_event_id(events)
    if event_id:
        odds_data = get_event_odds(config, logger, session, event_id)

    analysis = ask_openai_to_analyze(
        config=config,
        logger=logger,
        client=OpenAI(api_key=config.openai_api_key),
        stock_data=main_stock_data,
        watchlist_data=watchlist_data,
        odds_data=odds_data
    )

    save_analysis_to_csv(
        config=config,
        stock_data=main_stock_data,
        odds_data=odds_data,
        analysis_text=analysis
    )

    bet_summary = summarize_bets(config)

    print("\nMAIN STOCK DATA:")
    print(main_stock_data)

    print("\nWATCHLIST DATA:")
    print(watchlist_data)

    print("\nODDS DATA:")
    print(odds_data)

    print("\nAI ANALYSIS:")
    print(analysis)

    print("\nBET SUMMARY:")
    print(bet_summary)

    print("\nFILES UPDATED:")
    print(config.stock_log_file)
    print(config.analysis_log_file)
    print(config.bets_file)
