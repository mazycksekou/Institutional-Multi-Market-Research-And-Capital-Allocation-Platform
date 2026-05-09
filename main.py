import csv
import os
import secrets
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from quant_engine import (
    capm_required_return,
    classify_bet,
    classify_stock,
    expected_value_dollars,
    expected_value_per_unit,
    exposure_check,
    implied_probability_from_american,
    kelly_fraction,
    stock_alpha,
    suggested_bet_size,
    american_to_decimal,
)

load_dotenv()

API_BASE_URL = "https://betting-stock-api-code-integration.onrender.com"
ODDS_BASE_URL = "https://api.the-odds-api.com/v4"
DEFAULT_BOOKMAKERS = os.getenv(
    "DEFAULT_BOOKMAKERS",
    "draftkings,fanduel,betmgm,caesars,espnbet,bet365",
)
DEFAULT_REGIONS = os.getenv("DEFAULT_REGIONS", "us")
DEFAULT_MARKETS = "h2h,spreads,totals"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
BETS_FILE = DATA_DIR / "bets.csv"

SPORT_ALIASES = {
    "mlb": "baseball_mlb",
    "baseball": "baseball_mlb",
    "major league baseball": "baseball_mlb",
    "nba": "basketball_nba",
    "basketball": "basketball_nba",
    "wnba": "basketball_wnba",
    "nfl": "americanfootball_nfl",
    "football": "americanfootball_nfl",
    "ncaaf": "americanfootball_ncaaf",
    "college football": "americanfootball_ncaaf",
    "ncaab": "basketball_ncaab",
    "college basketball": "basketball_ncaab",
    "ncaa basketball": "basketball_ncaab",
    "nhl": "icehockey_nhl",
    "hockey": "icehockey_nhl",
    "epl": "soccer_epl",
    "premier league": "soccer_epl",
    "english premier league": "soccer_epl",
    "mls": "soccer_usa_mls",
    "ufc": "mma_mixed_martial_arts",
    "mma": "mma_mixed_martial_arts",
    "atp": "tennis_atp",
    "wta": "tennis_wta",
    "tennis": "tennis_atp",
    "golf": "golf_pga",
    "pga": "golf_pga",
}

SPORT_LABELS = {
    "baseball_mlb": "MLB",
    "basketball_nba": "NBA",
    "basketball_wnba": "WNBA",
    "americanfootball_nfl": "NFL",
    "americanfootball_ncaaf": "NCAAF",
    "basketball_ncaab": "NCAAB",
    "icehockey_nhl": "NHL",
    "soccer_epl": "EPL",
    "soccer_usa_mls": "MLS",
    "mma_mixed_martial_arts": "UFC/MMA",
    "tennis_atp": "ATP",
    "tennis_wta": "WTA",
    "golf_pga": "PGA",
}

LINE_SNAPSHOTS: dict[str, dict[str, Any]] = {}

app = FastAPI(
    title="Betting Stock API",
    description="Sports odds and stock analysis API for Custom GPT Actions.",
    version="2.0.0",
    servers=[{"url": API_BASE_URL}],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BetAnalysisRequest(BaseModel):
    sport: str
    event: str
    pick: str
    market: str
    odds: int
    true_probability_pct: float
    stake: float
    bankroll: float
    correlation_group: str
    current_group_exposure: float = 0
    notes: Optional[str] = None


class StockAnalysisRequest(BaseModel):
    ticker: str
    current_price: float
    expected_stock_return_pct: float
    beta: float
    risk_free_rate_pct: float
    expected_market_return_pct: float
    planned_position_size: float
    portfolio_value: float
    notes: Optional[str] = None


class BetLogRequest(BaseModel):
    date: Optional[str] = None
    type: str = "bet"
    sport: Optional[str] = None
    event: Optional[str] = None
    pick: Optional[str] = None
    market: Optional[str] = None
    odds: Optional[int] = None
    stake: float = 0
    bankroll: Optional[float] = None
    true_probability_pct: Optional[float] = None
    implied_probability_pct: Optional[float] = None
    edge_pct: Optional[float] = None
    ev_per_100: Optional[float] = None
    ev_dollars: Optional[float] = None
    kelly_pct: Optional[float] = None
    suggested_stake: Optional[float] = None
    correlation_group: Optional[str] = None
    exposure_status: Optional[str] = None
    decision: Optional[str] = None
    result: Optional[str] = "pending"
    profit_or_loss: float = 0
    notes: Optional[str] = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def no_data_response(message: str, error_type: str = "NO_DATA", **extra: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "result_type": "no_data",
        "has_actual_odds": False,
        "message": message,
        "error_type": error_type,
        "updated_at": utc_now(),
        **extra,
    }


def provider_error_response(message: str, status_code: Optional[int] = None, raw_response: Any = None) -> dict[str, Any]:
    return {
        "ok": False,
        "result_type": "provider_error",
        "has_actual_odds": False,
        "message": message,
        "status_code": status_code,
        "raw_response": raw_response,
        "error_type": "PROVIDER_ERROR",
        "updated_at": utc_now(),
    }


def get_configured_action_key() -> str:
    return os.getenv("ACTION_API_KEY", "").strip()


def extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        return ""
    scheme, _, token = authorization.strip().partition(" ")
    if scheme.lower() != "bearer" or not token:
        return ""
    return token.strip()


async def require_action_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> None:
    action_key = get_configured_action_key()
    if not action_key:
        raise HTTPException(status_code=500, detail="API authentication is not configured")

    header_keys = [key.strip() for key in (x_api_key, extract_bearer_token(authorization)) if key and key.strip()]
    if not any(secrets.compare_digest(key, action_key) for key in header_keys):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def resolve_sport_key(sport: Optional[str], league: Optional[str]) -> tuple[Optional[str], Optional[str], Optional[dict[str, Any]]]:
    raw = (league or sport or "").strip()
    if not raw:
        return None, None, no_data_response("sport or league is required.", "SPORT_REQUIRED")

    normalized = " ".join(raw.lower().replace("_", " ").replace("-", " ").split())
    sport_key = SPORT_ALIASES.get(normalized)
    if not sport_key:
        return None, None, no_data_response(f"Unknown sport or league: {raw}", "UNKNOWN_SPORT")

    return sport_key, SPORT_LABELS.get(sport_key, raw.upper()), None


async def odds_api_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("ODDS_API_KEY", "")
    if not api_key:
        return provider_error_response("ODDS_API_KEY is required for sports odds.")

    request_params = {"apiKey": api_key, **{k: v for k, v in params.items() if v not in (None, "")}}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{ODDS_BASE_URL}{path}", params=request_params)
    except Exception as error:
        return provider_error_response(f"The Odds API request failed: {error}")

    try:
        raw_response = response.json()
    except ValueError:
        raw_response = {"text": response.text}

    if not response.is_success:
        return provider_error_response(
            f"The Odds API returned HTTP {response.status_code}.",
            status_code=response.status_code,
            raw_response=raw_response,
        )

    return {"ok": True, "raw_response": raw_response, "status_code": response.status_code}


def event_matches(event: dict[str, Any], team: Optional[str], home_team: Optional[str], away_team: Optional[str], event_date: Optional[str]) -> bool:
    home = str(event.get("home_team", "")).lower()
    away = str(event.get("away_team", "")).lower()
    commence_time = str(event.get("commence_time", ""))
    if team:
        needle = team.lower()
        if needle not in home and needle not in away:
            return False
    if home_team and home_team.lower() not in home:
        return False
    if away_team and away_team.lower() not in away:
        return False
    if event_date and not commence_time.startswith(event_date):
        return False
    return True


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event.get("id"),
        "id": event.get("id"),
        "sport_key": event.get("sport_key"),
        "sport_title": event.get("sport_title"),
        "commence_time": event.get("commence_time"),
        "home_team": event.get("home_team"),
        "away_team": event.get("away_team"),
    }


async def fetch_active_events_filtered(
    sport_key: str,
    league_label: str,
    team: Optional[str] = None,
    home_team: Optional[str] = None,
    away_team: Optional[str] = None,
    event_date: Optional[str] = None,
) -> dict[str, Any]:
    response = await odds_api_get(f"/sports/{sport_key}/events", {})
    if not response.get("ok"):
        return {
            **response,
            "sport_key": sport_key,
            "league": league_label,
            "count": 0,
            "events": [],
            "filters": {
                "team": team,
                "home_team": home_team,
                "away_team": away_team,
                "date": event_date,
            },
            "provider": "the_odds_api",
        }

    raw_events = response.get("raw_response")
    if not isinstance(raw_events, list):
        return provider_error_response("The Odds API returned an unexpected events payload.", response.get("status_code"), raw_events)

    events = [
        normalize_event(event)
        for event in raw_events
        if isinstance(event, dict) and event_matches(event, team, home_team, away_team, event_date)
    ]
    return {
        "ok": True,
        "result_type": "events",
        "sport_key": sport_key,
        "league": league_label,
        "count": len(events),
        "events": events,
        "filters": {
            "team": team,
            "home_team": home_team,
            "away_team": away_team,
            "date": event_date,
        },
        "updated_at": utc_now(),
        "provider": "the_odds_api",
        "message": "Active events returned for requested sport/league only." if events else "No active events found for requested filters.",
    }


def snapshot_key(event_id: str, bookmaker_key: str, market_key: str, outcome_name: str, point: Any) -> str:
    return "|".join([event_id, bookmaker_key, market_key, outcome_name, "" if point is None else str(point)])


def flatten_odds(event: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    event_id = str(event.get("id"))
    for bookmaker in event.get("bookmakers") or []:
        for market in bookmaker.get("markets") or []:
            for outcome in market.get("outcomes") or []:
                price = outcome.get("price")
                point = outcome.get("point")
                key = snapshot_key(event_id, bookmaker.get("key", ""), market.get("key", ""), outcome.get("name", ""), point)
                if key not in LINE_SNAPSHOTS:
                    LINE_SNAPSHOTS[key] = {
                        "first_seen_at": utc_now(),
                        "opening_price_american": price,
                        "opening_point": point,
                    }
                opening = LINE_SNAPSHOTS[key]
                rows.append({
                    "event_id": event_id,
                    "bookmaker_key": bookmaker.get("key"),
                    "bookmaker_title": bookmaker.get("title"),
                    "market_key": market.get("key"),
                    "outcome_name": outcome.get("name"),
                    "price_american": price,
                    "decimal_odds": american_to_decimal(price) if isinstance(price, int) else None,
                    "implied_probability": implied_probability_from_american(price) if isinstance(price, int) else None,
                    "point": point,
                    "last_update": market.get("last_update") or bookmaker.get("last_update"),
                    "first_seen_at": opening["first_seen_at"],
                    "opening_price_american": opening["opening_price_american"],
                    "opening_point": opening["opening_point"],
                    "price_movement": price - opening["opening_price_american"] if isinstance(price, int) and isinstance(opening["opening_price_american"], int) else None,
                    "point_movement": point - opening["opening_point"] if isinstance(point, (int, float)) and isinstance(opening["opening_point"], (int, float)) else None,
                })
    return rows


def best_prices(flat: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in flat:
        if row["market_key"] in {"spreads", "totals"}:
            key = (row["market_key"], row["outcome_name"], row["point"])
        else:
            key = (row["market_key"], row["outcome_name"])
        current = grouped.get(key)
        if current is None or (row.get("price_american") is not None and row["price_american"] > current.get("price_american", -100000)):
            grouped[key] = row
    return list(grouped.values())


async def fetch_event_odds(
    sport_key: str,
    league_label: str,
    event_id: str,
    markets: str = DEFAULT_MARKETS,
    bookmakers: str = DEFAULT_BOOKMAKERS,
) -> dict[str, Any]:
    response = await odds_api_get(
        f"/sports/{sport_key}/odds",
        {
            "regions": DEFAULT_REGIONS,
            "markets": markets,
            "oddsFormat": "american",
            "bookmakers": bookmakers,
        },
    )
    if not response.get("ok"):
        return {
            **response,
            "sport_key": sport_key,
            "league": league_label,
            "event_id": event_id,
            "provider": "the_odds_api",
        }

    raw_events = response.get("raw_response")
    if not isinstance(raw_events, list):
        return provider_error_response("The Odds API returned an unexpected odds payload.", response.get("status_code"), raw_events)

    matched = next((event for event in raw_events if str(event.get("id")) == str(event_id)), None)
    if not matched:
        return no_data_response(
            "No sportsbook odds found for requested sport/league/event.",
            sport_key=sport_key,
            league=league_label,
            event_id=event_id,
        )

    flat = flatten_odds(matched)
    if not flat:
        return no_data_response(
            "No sportsbook odds found for requested sport/league/event.",
            sport_key=sport_key,
            league=league_label,
            event_id=event_id,
        )

    return {
        "ok": True,
        "result_type": "odds",
        "has_actual_odds": True,
        "sport_key": sport_key,
        "league": league_label,
        "event_id": event_id,
        "event": normalize_event(matched),
        "odds": flat,
        "best_prices": best_prices(flat),
        "provider": "the_odds_api",
        "updated_at": utc_now(),
        "message": "Sportsbook odds returned for requested sport/league/event only.",
    }


def stock_data(ticker: str, period: str, interval: str) -> dict[str, Any]:
    try:
        history = yf.Ticker(ticker.upper()).history(period=period, interval=interval)
    except Exception as error:
        return {
            "ok": False,
            "timestamp": utc_now(),
            "ticker": ticker.upper(),
            "message": f"Could not fetch stock data for {ticker.upper()}.",
            "error_type": type(error).__name__,
            "error": str(error),
            "period": period,
            "interval": interval,
            "recent_history": {},
        }

    if history.empty:
        return {
            "ok": False,
            "timestamp": utc_now(),
            "ticker": ticker.upper(),
            "message": f"No stock data found for {ticker.upper()}",
            "period": period,
            "interval": interval,
            "recent_history": {},
        }

    latest = history.tail(1)
    recent = history[["Open", "High", "Low", "Close", "Volume"]].tail(5)
    recent.index = recent.index.astype(str)
    return {
        "ok": True,
        "timestamp": utc_now(),
        "ticker": ticker.upper(),
        "last_open": float(latest["Open"].iloc[0]),
        "last_high": float(latest["High"].iloc[0]),
        "last_low": float(latest["Low"].iloc[0]),
        "last_close": float(latest["Close"].iloc[0]),
        "volume": int(latest["Volume"].iloc[0]),
        "period": period,
        "interval": interval,
        "recent_history": recent.to_dict(orient="index"),
    }


@app.get("/", operation_id="root")
async def root():
    return {"ok": True, "service": "betting-stock-api", "message": "API is running."}


@app.get("/health", operation_id="healthCheck")
async def health_check():
    return {"ok": True, "status": "ok", "service": "betting-stock-api"}


@app.get("/ping", operation_id="ping")
async def ping():
    return {"ok": True}


@app.get("/api/debug/config", operation_id="getDebugConfig", dependencies=[Depends(require_action_key)])
async def debug_config():
    return {
        "ok": True,
        "environment": {
            "ODDS_API_KEY": bool(os.getenv("ODDS_API_KEY")),
            "ACTION_API_KEY": bool(os.getenv("ACTION_API_KEY")),
            "SHARP_API_KEY": bool(os.getenv("SHARP_API_KEY")),
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "ENABLE_KALSHI": os.getenv("ENABLE_KALSHI", "false").lower() == "true",
            "KALSHI_BASE_URL": bool(os.getenv("KALSHI_BASE_URL")),
            "KALSHI_API_KEY_ID": bool(os.getenv("KALSHI_API_KEY_ID")),
            "KALSHI_PRIVATE_KEY_PEM": bool(os.getenv("KALSHI_PRIVATE_KEY_PEM")),
        },
        "default_bookmakers": DEFAULT_BOOKMAKERS,
        "default_regions": DEFAULT_REGIONS,
    }


@app.get("/api/debug/auth-status", operation_id="getAuthStatus")
async def auth_status():
    return {
        "action_api_key_configured": bool(get_configured_action_key()),
        "accepted_headers": ["X-API-Key", "Authorization: Bearer"],
        "auth_dependency_loaded": True,
    }


@app.get("/api/betting/events/active", operation_id="getActiveBettingEvents", dependencies=[Depends(require_action_key)])
async def get_active_betting_events(
    sport: Optional[str] = Query(default=None, description="Required if league is not supplied."),
    league: Optional[str] = Query(default=None, description="Required if sport is not supplied."),
    team: Optional[str] = None,
    home_team: Optional[str] = None,
    away_team: Optional[str] = None,
    date: Optional[str] = Query(default=None),
):
    sport_key, league_label, error = resolve_sport_key(sport, league)
    if error:
        return error
    return await fetch_active_events_filtered(sport_key, league_label, team, home_team, away_team, date)


@app.get("/api/betting/events/{event_id}/odds", operation_id="getEventOdds", dependencies=[Depends(require_action_key)])
async def get_event_odds_endpoint(
    event_id: str,
    sport: Optional[str] = Query(default=None, description="Required if league is not supplied."),
    league: Optional[str] = Query(default=None, description="Required if sport is not supplied."),
    markets: str = DEFAULT_MARKETS,
    bookmakers: str = DEFAULT_BOOKMAKERS,
):
    sport_key, league_label, error = resolve_sport_key(sport, league)
    if error:
        return error
    return await fetch_event_odds(sport_key, league_label, event_id, markets, bookmakers)


@app.get("/api/betting/first-event-odds", operation_id="getFirstEventOdds", dependencies=[Depends(require_action_key)])
async def get_first_event_odds(
    sport: Optional[str] = Query(default=None, description="Required if league is not supplied."),
    league: Optional[str] = Query(default=None, description="Required if sport is not supplied."),
    team: Optional[str] = None,
    home_team: Optional[str] = None,
    away_team: Optional[str] = None,
    date: Optional[str] = Query(default=None),
    markets: str = DEFAULT_MARKETS,
    bookmakers: str = DEFAULT_BOOKMAKERS,
):
    sport_key, league_label, error = resolve_sport_key(sport, league)
    if error:
        return error
    events_response = await fetch_active_events_filtered(sport_key, league_label, team, home_team, away_team, date)
    if not events_response.get("ok"):
        return events_response
    events = events_response.get("events") or []
    if not events:
        return no_data_response("No matching events found for requested sport/league/filters.", sport_key=sport_key, league=league_label)
    return await fetch_event_odds(sport_key, league_label, events[0]["event_id"], markets, bookmakers)


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
    sport_key, league_label, error = resolve_sport_key(sport, league) if (sport or league) else (None, None, None)
    odds = error or no_data_response("sport or league was not supplied, so no betting odds were fetched.", "SPORT_REQUIRED")
    if sport_key:
        odds = await fetch_active_events_filtered(sport_key, league_label)
    return {"ok": True, "ticker": ticker.upper(), "stock_data": stock, "odds_data": odds}


@app.post("/api/bets/log", operation_id="logBet", dependencies=[Depends(require_action_key)])
async def log_bet(payload: BetLogRequest):
    row = payload.model_dump()
    row["date"] = row["date"] or date.today().isoformat()
    BETS_FILE.parent.mkdir(exist_ok=True)
    exists = BETS_FILE.exists()
    with BETS_FILE.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return {"ok": True, "message": "Bet logged.", "logbook_row": row}


@app.get("/api/bets/summary", operation_id="getBetSummary", dependencies=[Depends(require_action_key)])
async def get_bet_summary():
    if not BETS_FILE.exists():
        return {"ok": True, "count": 0, "summary": {"message": "No bets logged yet."}, "records": []}
    df = pd.read_csv(BETS_FILE)
    if df.empty:
        return {"ok": True, "count": 0, "summary": {"message": "No bets logged yet."}, "records": []}
    profit_col = "profit_or_loss" if "profit_or_loss" in df.columns else "profit_loss"
    df["stake"] = pd.to_numeric(df.get("stake", 0), errors="coerce").fillna(0)
    df[profit_col] = pd.to_numeric(df.get(profit_col, 0), errors="coerce").fillna(0)
    total_staked = float(df["stake"].sum())
    total_profit = float(df[profit_col].sum())
    return {
        "ok": True,
        "count": int(len(df)),
        "summary": {
            "total_bets": int(len(df)),
            "total_staked": round(total_staked, 2),
            "total_profit": round(total_profit, 2),
            "roi_percent": round((total_profit / total_staked * 100) if total_staked else 0, 2),
        },
        "records": df.tail(25).to_dict(orient="records"),
    }


@app.post("/quant/bet-analysis", operation_id="quantBetAnalysis", dependencies=[Depends(require_action_key)])
async def quant_bet_analysis(payload: BetAnalysisRequest):
    true_probability = payload.true_probability_pct / 100
    implied_probability = implied_probability_from_american(payload.odds)
    edge_pct = (true_probability - implied_probability) * 100
    ev_unit = expected_value_per_unit(payload.odds, true_probability)
    ev_dollars = expected_value_dollars(payload.odds, true_probability, payload.stake)
    kelly = kelly_fraction(payload.odds, true_probability)
    suggested = suggested_bet_size(payload.bankroll, kelly)
    exposure = exposure_check(payload.bankroll, suggested, payload.current_group_exposure)
    decision = classify_bet(edge_pct, ev_unit * 100, kelly * 100)
    analysis = {
        "implied_probability_pct": round(implied_probability * 100, 2),
        "true_probability_pct": round(payload.true_probability_pct, 2),
        "edge_pct": round(edge_pct, 2),
        "ev_per_100": round(ev_unit * 100, 2),
        "ev_dollars": round(ev_dollars, 2),
        "kelly_pct": round(kelly * 100, 2),
        "suggested_stake": round(suggested, 2),
        "decision": decision,
        "exposure": exposure,
    }
    logbook_row = {
        "date": date.today().isoformat(),
        "type": "bet",
        "sport": payload.sport,
        "event": payload.event,
        "pick": payload.pick,
        "market": payload.market,
        "odds": payload.odds,
        "stake": payload.stake,
        "bankroll": payload.bankroll,
        "true_probability_pct": analysis["true_probability_pct"],
        "implied_probability_pct": analysis["implied_probability_pct"],
        "edge_pct": analysis["edge_pct"],
        "ev_per_100": analysis["ev_per_100"],
        "ev_dollars": analysis["ev_dollars"],
        "kelly_pct": analysis["kelly_pct"],
        "suggested_stake": analysis["suggested_stake"],
        "correlation_group": payload.correlation_group,
        "exposure_status": exposure["message"],
        "decision": decision,
        "result": "pending",
        "profit_or_loss": 0,
        "notes": payload.notes,
    }
    return {"ok": True, "endpoint": "/quant/bet-analysis", "analysis": analysis, "logbook_row": logbook_row}


@app.post("/quant/stock-analysis", operation_id="quantStockAnalysis", dependencies=[Depends(require_action_key)])
async def quant_stock_analysis(payload: StockAnalysisRequest):
    required = capm_required_return(payload.risk_free_rate_pct, payload.beta, payload.expected_market_return_pct)
    alpha = stock_alpha(payload.expected_stock_return_pct, required)
    position_pct = (payload.planned_position_size / payload.portfolio_value * 100) if payload.portfolio_value else 0
    decision = classify_stock(alpha)
    analysis = {
        "ticker": payload.ticker.upper(),
        "capm_required_return_pct": round(required, 2),
        "expected_stock_return_pct": round(payload.expected_stock_return_pct, 2),
        "alpha_pct": round(alpha, 2),
        "position_pct": round(position_pct, 2),
        "decision": decision,
    }
    logbook_row = {
        "date": date.today().isoformat(),
        "type": "stock",
        "ticker": payload.ticker.upper(),
        "current_price": payload.current_price,
        "expected_stock_return_pct": payload.expected_stock_return_pct,
        "beta": payload.beta,
        "risk_free_rate_pct": payload.risk_free_rate_pct,
        "expected_market_return_pct": payload.expected_market_return_pct,
        "capm_required_return_pct": analysis["capm_required_return_pct"],
        "alpha_pct": analysis["alpha_pct"],
        "planned_position_size": payload.planned_position_size,
        "portfolio_value": payload.portfolio_value,
        "position_pct": analysis["position_pct"],
        "decision": decision,
        "exit_plan": "",
        "result": "pending",
        "profit_or_loss": 0,
        "notes": payload.notes,
    }
    return {"ok": True, "endpoint": "/quant/stock-analysis", "analysis": analysis, "logbook_row": logbook_row}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    generic_object_response = {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "additionalProperties": True,
                }
            }
        },
    }
    league_parameter = {
        "name": "league",
        "in": "query",
        "required": True,
        "description": "League code such as mlb, nba, nhl, nfl",
        "schema": {
            "type": "string",
            "example": "mlb",
        },
    }
    protected_security = [{"ApiKeyAuth": []}]

    schema = {
        "openapi": "3.1.0",
        "info": {
            "title": app.title,
            "description": "Minimal Custom GPT Action schema for betting event lookup.",
            "version": app.version,
        },
        "servers": [{"url": API_BASE_URL}],
        "paths": {
            "/health": {
                "get": {
                    "operationId": "healthCheck",
                    "summary": "Health Check",
                    "responses": {"200": generic_object_response},
                }
            },
            "/api/debug/config": {
                "get": {
                    "operationId": "debugConfig",
                    "summary": "Debug Config",
                    "security": protected_security,
                    "responses": {"200": generic_object_response},
                }
            },
            "/api/betting/events/active": {
                "get": {
                    "operationId": "getActiveBettingEvents",
                    "summary": "Get Active Betting Events",
                    "security": protected_security,
                    "parameters": [league_parameter],
                    "responses": {"200": generic_object_response},
                }
            },
            "/api/betting/first-event-odds": {
                "get": {
                    "operationId": "getFirstEventOdds",
                    "summary": "Get First Event Odds",
                    "security": protected_security,
                    "parameters": [league_parameter],
                    "responses": {"200": generic_object_response},
                }
            },
        },
        "components": {
            "schemas": {},
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                }
            }
        },
    }
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
