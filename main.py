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
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field

from betting_providers import aliases as betting_aliases
from betting_providers.base import PREDICTION_MARKET
from betting_providers.provider_router import ProviderRouter
from quant_engine import (
    american_to_implied_probability,
    capm_required_return,
    build_market_pricing_row,
    classify_bet,
    classify_edge,
    classify_stock,
    expected_value_dollars,
    expected_value_per_unit,
    exposure_check,
    implied_probability_from_american,
    kelly_fraction,
    probability_to_fair_american,
    stock_alpha,
    suggested_stake,
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
PROVIDER_ROUTER = ProviderRouter()

ACTION_SAFE_EVENT_KEYS: frozenset[str] = frozenset({
    "provider",
    "provider_type",
    "provider_event_id",
    "event_id",
    "id",
    "sport_key",
    "league",
    "commence_time",
    "home_team",
    "away_team",
    "event_ticker",
    "series_ticker",
    "title",
    "category",
    "status",
})


def _normalize_action_league_input(league: str) -> str:
    raw = (league or "").strip() or "baseball_mlb"
    if raw.lower().replace("-", "_") == "mlb":
        return "baseball_mlb"
    return raw


def _slim_events_for_action(events: Any, limit: int) -> list[dict[str, Any]]:
    if not isinstance(events, list):
        return []
    cap = max(0, min(int(limit), 100))
    out: list[dict[str, Any]] = []
    for ev in events[:cap]:
        if not isinstance(ev, dict):
            continue
        row = {k: ev[k] for k in ACTION_SAFE_EVENT_KEYS if k in ev}
        if not row:
            pid = ev.get("id") or ev.get("event_id") or ev.get("provider_event_id")
            if pid is not None:
                row = {"provider_event_id": pid, "event_id": pid, "id": pid}
        out.append(row)
    return out


ACTION_ODDS_LINE_KEYS: frozenset[str] = frozenset({
    "provider",
    "provider_type",
    "provider_event_id",
    "sport_key",
    "market",
    "sportsbook",
    "selection",
    "price_american",
    "price_decimal",
    "implied_probability",
    "point",
    "last_update",
})


def _parse_markets_requested(markets_csv: str) -> list[str]:
    parts = [p.strip() for p in (markets_csv or "").split(",") if p.strip()]
    return parts if parts else ["h2h", "spreads", "totals"]


def _action_build_markets_and_bookmakers(flat_odds: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(flat_odds, list):
        return [], []
    by_market: dict[str, list[dict[str, Any]]] = {}
    books: dict[str, dict[str, str]] = {}
    for row in flat_odds:
        if not isinstance(row, dict):
            continue
        slim = {k: row[k] for k in ACTION_ODDS_LINE_KEYS if k in row}
        mk = str(slim.get("market") or "unknown")
        by_market.setdefault(mk, []).append(slim)
        sb = slim.get("sportsbook")
        if sb is not None and str(sb) not in books:
            key = str(sb)
            books[key] = {"key": key, "title": key}
    markets_out = [{"market_key": k, "lines": v} for k, v in sorted(by_market.items())]
    bookmakers_out = sorted(books.values(), key=lambda b: b["key"])
    return markets_out, bookmakers_out


def _action_event_odds_fail(
    endpoint_id: str,
    event_id: str,
    league_val: str,
    provider_val: str,
    markets_requested: list[str],
    error: str,
    detail: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "endpoint": endpoint_id,
        "event_id": event_id,
        "league": league_val,
        "provider": provider_val,
        "markets_requested": markets_requested,
        "markets": [],
        "bookmakers": [],
        "error": error,
        "detail": detail,
    }


async def action_fetch_active_events_envelope(
    league: str,
    provider: Optional[str],
    limit: int,
) -> dict[str, Any]:
    endpoint_id = "getActiveBettingEvents"
    league_param = _normalize_action_league_input(league)
    provider_used = (provider or "").strip() or None
    default_provider = PROVIDER_ROUTER.default_betting_provider()
    resolved_provider = provider_used or default_provider
    sport_key_out: Optional[str] = None

    try:
        sport_key, _label, resolve_err = betting_aliases.resolve_sport_key(None, league_param)
        if resolve_err:
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "league": league_param,
                "provider": resolved_provider,
                "count": 0,
                "events": [],
                "error": str(resolve_err.get("error_type") or "UNKNOWN_SPORT"),
                "detail": str(resolve_err.get("message") or "Unknown sport or league."),
            }
        sport_key_out = sport_key

        payload = await PROVIDER_ROUTER.get_active_events(provider_used, None, league_param)

        if not isinstance(payload, dict):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "league": sport_key_out or league_param,
                "provider": resolved_provider,
                "count": 0,
                "events": [],
                "error": "INVALID_RESPONSE",
                "detail": "Provider returned an unexpected payload.",
            }

        if not payload.get("ok"):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "league": str(payload.get("sport_key") or sport_key_out or league_param),
                "provider": str(payload.get("provider") or resolved_provider),
                "count": 0,
                "events": [],
                "error": str(payload.get("error_type") or "PROVIDER_ERROR"),
                "detail": str(payload.get("message") or "Provider request failed."),
            }

        events_src = payload.get("events")
        if not isinstance(events_src, list) and isinstance(payload.get("data"), list):
            events_src = payload["data"]
        if not isinstance(events_src, list):
            events_src = []

        slim = _slim_events_for_action(events_src, limit)
        league_out = str(payload.get("sport_key") or sport_key_out or league_param)

        return {
            "ok": True,
            "endpoint": endpoint_id,
            "league": league_out,
            "provider": str(payload.get("provider") or resolved_provider),
            "count": len(slim),
            "events": slim,
            "error": None,
            "detail": None,
        }
    except Exception:
        return {
            "ok": False,
            "endpoint": endpoint_id,
            "league": str(sport_key_out or league_param),
            "provider": str(provider_used or default_provider),
            "count": 0,
            "events": [],
            "error": "UNEXPECTED_ERROR",
            "detail": "Active events request failed.",
        }


async def action_fetch_event_odds_envelope(
    event_id: str,
    league: str,
    provider: Optional[str],
    markets_csv: str,
    bookmakers_csv: str,
) -> dict[str, Any]:
    endpoint_id = "getEventOdds"
    league_param = _normalize_action_league_input(league)
    provider_used = (provider or "").strip() or None
    default_provider = PROVIDER_ROUTER.default_betting_provider()
    resolved_provider = provider_used or default_provider
    markets_requested = _parse_markets_requested(markets_csv)
    sport_key_out: Optional[str] = None

    try:
        sport_key, _label, resolve_err = betting_aliases.resolve_sport_key(None, league_param)
        if resolve_err:
            return _action_event_odds_fail(
                endpoint_id,
                event_id,
                league_param,
                resolved_provider,
                markets_requested,
                str(resolve_err.get("error_type") or "UNKNOWN_SPORT"),
                str(resolve_err.get("message") or "Unknown sport or league."),
            )
        sport_key_out = sport_key

        payload = await PROVIDER_ROUTER.get_event_odds(
            provider_used,
            event_id,
            None,
            league_param,
            markets=markets_csv or DEFAULT_MARKETS,
            bookmakers=bookmakers_csv or DEFAULT_BOOKMAKERS,
        )

        if not isinstance(payload, dict):
            return _action_event_odds_fail(
                endpoint_id,
                event_id,
                str(sport_key_out or league_param),
                resolved_provider,
                markets_requested,
                "INVALID_RESPONSE",
                "Provider returned an unexpected payload.",
            )

        if not payload.get("ok"):
            return _action_event_odds_fail(
                endpoint_id,
                event_id,
                str(payload.get("sport_key") or sport_key_out or league_param),
                str(payload.get("provider") or resolved_provider),
                markets_requested,
                str(payload.get("error_type") or "PROVIDER_ERROR"),
                str(payload.get("message") or "Provider request failed."),
            )

        flat = payload.get("odds")
        markets_blk, books_blk = _action_build_markets_and_bookmakers(flat)
        league_out = str(payload.get("sport_key") or sport_key_out or league_param)

        return {
            "ok": True,
            "endpoint": endpoint_id,
            "event_id": event_id,
            "league": league_out,
            "provider": str(payload.get("provider") or resolved_provider),
            "markets_requested": markets_requested,
            "markets": markets_blk,
            "bookmakers": books_blk,
            "error": None,
            "detail": None,
        }
    except HTTPException as exc:
        detail = exc.detail
        if not isinstance(detail, str):
            detail = "Request rejected."
        return _action_event_odds_fail(
            endpoint_id,
            event_id,
            str(sport_key_out or league_param),
            str(provider_used or default_provider),
            markets_requested,
            "HTTP_ERROR",
            detail,
        )
    except Exception:
        return _action_event_odds_fail(
            endpoint_id,
            event_id,
            str(sport_key_out or league_param),
            str(provider_used or default_provider),
            markets_requested,
            "UNEXPECTED_ERROR",
            "Event odds request failed.",
        )


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


class MarketPricingRequest(BaseModel):
    event: str
    provider: str
    sportsbook: str
    league: str
    market: str
    selection: str
    american_odds: int
    true_probability: float = Field(gt=0, lt=1)
    bankroll: float = Field(ge=0)
    stake: float = Field(ge=0)
    correlation_group: Optional[str] = None
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


@app.head("/", include_in_schema=False)
async def root_head():
    return {}


@app.get("/health", operation_id="healthCheck")
async def health_check():
    return {"ok": True, "status": "ok", "service": "betting-stock-api"}


@app.get("/ping", operation_id="ping")
async def ping():
    return {"ok": True}


@app.get("/debug/routes", include_in_schema=False)
async def debug_routes():
    paths = sorted({route.path for route in app.routes if isinstance(route, APIRoute)})
    return {"ok": True, "paths": paths, "count": len(paths)}


@app.get("/api/debug/config", operation_id="debugConfig", dependencies=[Depends(require_action_key)])
async def debug_config():
    return {
        "ok": True,
        "environment": {
            "ODDS_API_KEY": bool(os.getenv("ODDS_API_KEY")),
            "ODDS_API_ENABLED": os.getenv("ODDS_API_ENABLED", "true").lower() == "true",
            "ACTION_API_KEY": bool(os.getenv("ACTION_API_KEY")),
            "SHARP_API_KEY": bool(os.getenv("SHARP_API_KEY")),
            "SHARP_API_BASE_URL": bool(os.getenv("SHARP_API_BASE_URL")),
            "SHARP_API_ENABLED": os.getenv("SHARP_API_ENABLED", "false").lower() == "true",
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "KALSHI_ENABLED": os.getenv("KALSHI_ENABLED", "false").lower() == "true",
            "KALSHI_ENV": os.getenv("KALSHI_ENV", "demo"),
            "KALSHI_BASE_URL": bool(os.getenv("KALSHI_BASE_URL")),
            "KALSHI_API_KEY_ID": bool(os.getenv("KALSHI_API_KEY_ID")),
            "KALSHI_PRIVATE_KEY": bool(os.getenv("KALSHI_PRIVATE_KEY")),
        },
        "default_bookmakers": DEFAULT_BOOKMAKERS,
        "default_regions": DEFAULT_REGIONS,
        "default_betting_provider": PROVIDER_ROUTER.default_betting_provider(),
        "default_market_provider": PROVIDER_ROUTER.default_market_provider(),
    }


@app.get("/api/debug/auth-status", operation_id="getAuthStatus")
async def auth_status():
    return {
        "action_api_key_configured": bool(get_configured_action_key()),
        "accepted_headers": ["X-API-Key", "Authorization: Bearer"],
        "auth_dependency_loaded": True,
    }


@app.get("/api/betting/providers", operation_id="getBettingProviders", dependencies=[Depends(require_action_key)])
async def get_betting_providers():
    return {
        "ok": True,
        "default_provider": PROVIDER_ROUTER.default_betting_provider(),
        "providers": PROVIDER_ROUTER.capabilities(),
    }


@app.get("/api/betting/sports", operation_id="getSupportedBettingSports", dependencies=[Depends(require_action_key)])
async def get_supported_betting_sports(provider: Optional[str] = None):
    return await PROVIDER_ROUTER.get_supported_sports(provider)


@app.get("/api/betting/events/active", operation_id="getActiveBettingEventsRaw", dependencies=[Depends(require_action_key)])
async def get_active_betting_events(
    sport: Optional[str] = Query(default=None, description="Required if league is not supplied."),
    league: Optional[str] = Query(default=None, description="Required if sport is not supplied."),
    provider: Optional[str] = None,
    team: Optional[str] = None,
    home_team: Optional[str] = None,
    away_team: Optional[str] = None,
    date: Optional[str] = Query(default=None),
):
    return await PROVIDER_ROUTER.get_active_events(
        provider,
        sport,
        league,
        team=team,
        home_team=home_team,
        away_team=away_team,
        date=date,
    )


@app.get("/api/actions/betting/events/active", operation_id="getActiveBettingEvents", dependencies=[Depends(require_action_key)])
async def action_get_active_betting_events(
    league: str = Query(default="baseball_mlb", description="League or sport key (e.g. mlb, baseball_mlb)."),
    provider: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=100),
):
    return await action_fetch_active_events_envelope(league, provider, limit)


@app.get("/api/betting/events/{event_id}/odds", operation_id="getEventOddsRaw", dependencies=[Depends(require_action_key)])
async def get_event_odds_endpoint(
    event_id: str,
    sport: Optional[str] = Query(default=None, description="Required if league is not supplied."),
    league: Optional[str] = Query(default=None, description="Required if sport is not supplied."),
    provider: Optional[str] = None,
    markets: str = DEFAULT_MARKETS,
    bookmakers: str = DEFAULT_BOOKMAKERS,
):
    return await PROVIDER_ROUTER.get_event_odds(
        provider,
        event_id,
        sport,
        league,
        markets=markets,
        bookmakers=bookmakers,
    )


@app.get("/api/actions/betting/events/{event_id}/odds", operation_id="getEventOdds", dependencies=[Depends(require_action_key)])
async def action_get_event_odds(
    event_id: str,
    league: str = Query(default="baseball_mlb", description="League or sport key (e.g. mlb, baseball_mlb)."),
    provider: Optional[str] = None,
    markets: str = Query(default=DEFAULT_MARKETS),
):
    return await action_fetch_event_odds_envelope(
        event_id,
        league,
        provider,
        markets,
        DEFAULT_BOOKMAKERS,
    )


@app.get("/api/betting/first-event-odds", operation_id="getFirstEventOddsRaw", dependencies=[Depends(require_action_key)])
async def get_first_event_odds(
    sport: Optional[str] = Query(default=None, description="Required if league is not supplied."),
    league: Optional[str] = Query(default=None, description="Required if sport is not supplied."),
    provider: Optional[str] = None,
    team: Optional[str] = None,
    home_team: Optional[str] = None,
    away_team: Optional[str] = None,
    date: Optional[str] = Query(default=None),
    markets: str = DEFAULT_MARKETS,
    bookmakers: str = DEFAULT_BOOKMAKERS,
):
    return await PROVIDER_ROUTER.get_first_event_odds(
        provider,
        sport,
        league,
        team=team,
        home_team=home_team,
        away_team=away_team,
        date=date,
        markets=markets,
        bookmakers=bookmakers,
    )


@app.get("/api/actions/betting/first-event-odds", operation_id="getFirstEventOdds", dependencies=[Depends(require_action_key)])
async def action_get_first_event_odds(
    league: str = Query(default="baseball_mlb", description="League or sport key (e.g. mlb, baseball_mlb)."),
    provider: Optional[str] = None,
    markets: str = Query(default=DEFAULT_MARKETS),
):
    endpoint_id = "getFirstEventOdds"
    league_param = _normalize_action_league_input(league)
    provider_used = (provider or "").strip() or None

    try:
        active = await action_fetch_active_events_envelope(league, provider, 1)
        if not active.get("ok"):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "league": str(active.get("league") or league_param),
                "event": {},
                "odds": {},
                "error": str(active.get("error") or "ACTIVE_EVENTS_FAILED"),
                "detail": str(active.get("detail") or "Could not load active events."),
            }

        events = active.get("events") or []
        if not events:
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "league": str(active.get("league") or league_param),
                "event": {},
                "odds": {},
                "error": "NO_EVENTS",
                "detail": "No active events found for this league.",
            }

        first = events[0] if isinstance(events[0], dict) else {}
        eid = first.get("provider_event_id") or first.get("event_id") or first.get("id")
        if not eid:
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "league": str(active.get("league") or league_param),
                "event": first,
                "odds": {},
                "error": "NO_EVENT_ID",
                "detail": "First event is missing an id field.",
            }

        odds_env = await action_fetch_event_odds_envelope(
            str(eid),
            league,
            provider_used,
            markets,
            DEFAULT_BOOKMAKERS,
        )

        odds_body = {
            "markets_requested": odds_env.get("markets_requested") or _parse_markets_requested(markets),
            "markets": odds_env.get("markets") or [],
            "bookmakers": odds_env.get("bookmakers") or [],
        }

        if not odds_env.get("ok"):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "league": str(odds_env.get("league") or active.get("league") or league_param),
                "event": first,
                "odds": odds_body,
                "error": str(odds_env.get("error") or "ODDS_FAILED"),
                "detail": str(odds_env.get("detail") or "Odds request failed."),
            }

        return {
            "ok": True,
            "endpoint": endpoint_id,
            "league": str(odds_env.get("league") or active.get("league") or league_param),
            "event": first,
            "odds": odds_body,
            "error": None,
            "detail": None,
        }
    except HTTPException as exc:
        detail = exc.detail
        if not isinstance(detail, str):
            detail = "Request rejected."
        return {
            "ok": False,
            "endpoint": endpoint_id,
            "league": league_param,
            "event": {},
            "odds": {},
            "error": "HTTP_ERROR",
            "detail": detail,
        }
    except Exception:
        return {
            "ok": False,
            "endpoint": endpoint_id,
            "league": league_param,
            "event": {},
            "odds": {},
            "error": "UNEXPECTED_ERROR",
            "detail": "First-event odds request failed.",
        }


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
    return await PROVIDER_ROUTER.get_kalshi_events(status=status, series_ticker=series_ticker, limit=limit)


@app.get("/api/markets/kalshi/markets", operation_id="getKalshiMarkets", dependencies=[Depends(require_action_key)])
async def get_kalshi_markets(
    query: Optional[str] = None,
    event_ticker: Optional[str] = None,
    series_ticker: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    cursor: Optional[str] = None,
):
    return await PROVIDER_ROUTER.get_kalshi_markets(
        query=query,
        event_ticker=event_ticker,
        series_ticker=series_ticker,
        status=status,
        limit=limit,
        cursor=cursor,
    )


@app.get("/api/markets/kalshi/markets/{ticker}/orderbook", operation_id="getKalshiOrderbook", dependencies=[Depends(require_action_key)])
async def get_kalshi_orderbook(ticker: str):
    return await PROVIDER_ROUTER.get_kalshi_orderbook(ticker)


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


@app.post("/quant/market-pricing", operation_id="priceMarket", dependencies=[Depends(require_action_key)])
async def quant_market_pricing(payload: MarketPricingRequest):
    implied = american_to_implied_probability(payload.american_odds)
    implied_probability = implied["decimal"]
    edge = payload.true_probability - implied_probability
    ev_unit = expected_value_per_unit(payload.american_odds, payload.true_probability)
    kelly = kelly_fraction(payload.american_odds, payload.true_probability)
    suggested = suggested_stake(payload.bankroll, payload.american_odds, payload.true_probability)
    decision = classify_edge(edge * 100, ev_unit)
    risk_warning = "Stake is within the capped fractional Kelly risk limit."

    if suggested <= 0 and ev_unit <= 0:
        risk_warning = "This market has no positive expected value at the submitted probability."
    elif payload.bankroll and payload.stake > payload.bankroll * 0.05:
        decision = "OVEREXPOSED"
        risk_warning = "Submitted stake is above the correlation exposure guardrail."
    elif payload.stake > suggested and suggested >= 0:
        risk_warning = "Submitted stake is above the capped fractional Kelly recommendation."

    output = {
        "decimal_odds": round(american_to_decimal(payload.american_odds), 2),
        "implied_probability": round(implied_probability, 4),
        "implied_probability_percent": round(implied_probability * 100, 2),
        "true_probability_percent": round(payload.true_probability * 100, 2),
        "edge": round(edge, 4),
        "edge_percent": round(edge * 100, 2),
        "fair_american_odds": probability_to_fair_american(payload.true_probability),
        "ev_per_unit": round(ev_unit, 4),
        "ev_per_100": round(ev_unit * 100, 2),
        "kelly_fraction": round(kelly, 4),
        "kelly_percent": round(kelly * 100, 2),
        "suggested_stake": round(suggested, 2),
        "decision": decision,
        "risk_warning": risk_warning,
    }
    input_data = payload.model_dump()
    logbook_row = build_market_pricing_row(input_data, output)
    return {
        "ok": True,
        "event": payload.event,
        "provider": payload.provider,
        "sportsbook": payload.sportsbook,
        "league": payload.league,
        "market": payload.market,
        "selection": payload.selection,
        "american_odds": payload.american_odds,
        "decimal_odds": output["decimal_odds"],
        "implied_probability": output["implied_probability"],
        "implied_probability_percent": output["implied_probability_percent"],
        "true_probability": payload.true_probability,
        "true_probability_percent": output["true_probability_percent"],
        "edge": output["edge"],
        "edge_percent": output["edge_percent"],
        "fair_american_odds": output["fair_american_odds"],
        "ev_per_unit": output["ev_per_unit"],
        "ev_per_100": output["ev_per_100"],
        "kelly_fraction": output["kelly_fraction"],
        "kelly_percent": output["kelly_percent"],
        "suggested_stake": output["suggested_stake"],
        "decision": output["decision"],
        "risk_warning": output["risk_warning"],
        "logbook_row": logbook_row,
    }


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


PUBLIC_OPENAPI_PATH_METHODS = frozenset({
    ("/", "get"),
    ("/health", "get"),
    ("/ping", "get"),
    ("/api/debug/auth-status", "get"),
})


def _live_openapi_paths() -> set[str]:
    return {
        route.path
        for route in app.routes
        if isinstance(route, APIRoute) and route.include_in_schema
    }


def _attach_api_key_openapi_security(schema: dict[str, Any]) -> None:
    components = schema.setdefault("components", {})
    schemes = components.setdefault("securitySchemes", {})
    schemes["ApiKeyAuth"] = {"type": "apiKey", "in": "header", "name": "X-API-Key"}
    requirement = [{"ApiKeyAuth": []}]
    for path_key, path_item in schema.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "delete", "patch", "head", "options"}:
                continue
            if not isinstance(operation, dict):
                continue
            if (path_key, method) in PUBLIC_OPENAPI_PATH_METHODS:
                continue
            operation.setdefault("security", requirement)


def custom_openapi():
    cached = app.openapi_schema
    live_paths = _live_openapi_paths()
    if isinstance(cached, dict):
        cached_paths = set(cached.get("paths", {}))
        if cached_paths == live_paths:
            return cached

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description or "",
        routes=app.routes,
    )
    schema["info"]["description"] = "Minimal Custom GPT Action schema for betting event lookup."
    schema["servers"] = [{"url": API_BASE_URL}]
    _attach_api_key_openapi_security(schema)
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
