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
from pydantic import BaseModel, ConfigDict, Field

from betting_providers import aliases as betting_aliases
from betting_providers.base import PREDICTION_MARKET
from betting_providers.provider_router import ProviderRouter
import bet_log
import bet_decision_engine
import market_pricing
import multi_sport_model_registry
import model_probability
import screenshot_intake
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


class EvaluateLineIn(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    sportsbook: str
    market: str
    selection: str
    line: Optional[float] = None
    odds_american: int
    model_probability: Optional[float] = None
    correlation_group: Optional[str] = None
    opening_odds_american: Optional[int] = None


class EvaluateLinesRequest(BaseModel):
    sport: str = Field(..., description="Sport key (e.g., 'baseball_mlb', 'basketball_nba')")
    event: str = Field(..., description="Event description or identifier")
    bankroll: float = Field(..., gt=0, description="Total bankroll amount for stake calculations")
    unit_size: float = Field(..., gt=0, description="Base betting unit size")
    risk_profile: str = Field(default="standard", description="Risk profile: 'conservative', 'standard', or 'aggressive'")
    lines: list[EvaluateLineIn] = Field(..., min_length=1, description="List of betting lines to evaluate")
    max_stake_pct: float = Field(default=0.02, gt=0, le=0.25, description="Maximum stake percentage of bankroll per bet")


class PriceEventRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    sport: str = Field(..., description="Sport key (e.g., 'baseball_mlb', 'basketball_nba')")
    event_id: str = Field(..., description="Unique event identifier")
    league: str = Field(..., description="League or sport key (e.g., 'mlb', 'baseball_mlb')")
    markets: str = Field(default="h2h,spreads,totals", description="Comma-separated list of markets to price")
    provider: Optional[str] = Field(None, description="Odds provider to use (defaults to configured provider)")
    bankroll: float = Field(default=1000, ge=0, description="Total bankroll amount for stake calculations")
    unit_size: float = Field(default=25, gt=0, description="Base betting unit size")
    risk_profile: str = Field(default="conservative", description="Risk profile: 'conservative', 'standard', or 'aggressive'")
    model_probabilities: Optional[dict[str, Any]] = Field(None, description="Optional model probabilities for pricing calculations")


class ModelProbabilityRequest(BaseModel):
    market_probability: Optional[float] = Field(None, gt=0, lt=1, description="Market probability (0-1), inferred from priced_rows if not provided")
    projection_probability: Optional[float] = Field(None, gt=0, lt=1, description="Model projection probability (0-1)")
    pitcher_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Pitcher-related probability adjustment (-0.1 to 0.1)")
    weather_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Weather-related probability adjustment (-0.1 to 0.1)")
    lineup_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Lineup-related probability adjustment (-0.1 to 0.1)")
    bullpen_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Bullpen-related probability adjustment (-0.1 to 0.1)")
    injury_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Injury-related probability adjustment (-0.1 to 0.1)")
    park_factor_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Park factor probability adjustment (-0.1 to 0.1)")
    umpire_adjustment: Optional[float] = Field(None, ge=-0.1, le=0.1, description="Umpire-related probability adjustment (-0.1 to 0.1)")
    player_prop_projection: Optional[float] = Field(None, gt=0, lt=1, description="Player prop projection probability (0-1)")
    sharp_market_probability: Optional[float] = Field(None, gt=0, lt=1, description="Sharp market probability (0-1)")
    closing_line_projection: Optional[float] = Field(None, gt=0, lt=1, description="Closing line projection probability (0-1)")
    priced_rows: Optional[list[dict[str, Any]]] = Field(None, description="List of priced rows with probability data for inference")


class AnalyzeEventRequest(BaseModel):
    sport: str = Field(..., description="Sport key (e.g., 'baseball_mlb', 'basketball_nba')")
    league: str = Field(..., description="League or sport key (e.g., 'mlb', 'baseball_mlb')")
    event_id: str = Field(..., description="Unique event identifier")
    markets: str = Field(default="h2h,spreads,totals", description="Comma-separated list of markets to analyze")
    provider: Optional[str] = Field(None, description="Odds provider to use (defaults to configured provider)")
    bankroll: float = Field(default=1000, ge=0, description="Total bankroll amount for stake calculations")
    unit_size: float = Field(default=25, gt=0, description="Base betting unit size")
    risk_profile: str = Field(default="conservative", description="Risk profile: 'conservative', 'standard', or 'aggressive'")
    max_stake_pct: float = Field(default=0.02, gt=0, le=0.25, description="Maximum stake percentage of bankroll per bet")
    independent_inputs: Optional[dict[str, Any]] = Field(None, description="Optional independent inputs for model probability calculations")


class SportAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())

    sport: Optional[Any] = Field(None, description="Official sport key. egaming is accepted as a backward-compatible alias for esports.")
    league: Optional[str] = Field(None, description="Optional league key.")
    market: Optional[Any] = Field(None, description="Market to analyze.")
    event_id: Optional[str] = Field(None, description="Optional event identifier.")
    home_team: Optional[str] = Field(None, description="Optional home team.")
    away_team: Optional[str] = Field(None, description="Optional away team.")
    player_name: Optional[str] = Field(None, description="Optional player name for prop analysis.")
    odds_american: Optional[Any] = Field(None, description="Optional American odds.")
    line: Optional[Any] = Field(None, description="Optional market line.")
    input_stats: Optional[Any] = Field(None, description="Optional model inputs. Missing required inputs force inactive_missing_data.")
    risk_profile: Optional[str] = Field("conservative", description="Risk profile: conservative, standard, or aggressive.")
    bankroll: Optional[Any] = Field(None, description="Optional bankroll.")
    unit_size: Optional[Any] = Field(None, description="Optional base unit size.")


class ScreenshotAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())

    source_type: Optional[str] = Field(None, description="parsed_fields, screenshot_text, ocr_text, or image_metadata.")
    sport: Optional[Any] = None
    league: Optional[Any] = None
    event: Optional[str] = None
    teams: Optional[list[str]] = None
    market: Optional[Any] = None
    selection: Optional[str] = None
    odds_american: Optional[Any] = None
    line: Optional[Any] = None
    total_line: Optional[Any] = None
    book: Optional[str] = None
    screenshot_text: Optional[str] = None
    visible_markets: Optional[list[Any]] = None
    visible_props: Optional[list[Any]] = None
    visible_alt_lines: Optional[list[Any]] = None
    bankroll: Optional[Any] = None
    unit_size: Optional[Any] = None
    risk_profile: Optional[str] = "conservative"
    input_stats: Optional[dict[str, Any]] = None


class ActionBetLogRequest(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())

    sport_key: Optional[str] = None
    event_id: Optional[str] = None
    event: Optional[str] = None
    sportsbook: Optional[str] = None
    market: Optional[Any] = None
    selection: Optional[str] = None
    line: Optional[float] = None
    odds_american: Optional[int] = None
    stake: float = 0
    unit_size: Optional[float] = None
    bankroll_at_bet: Optional[float] = None
    model_level: Optional[str] = None
    probability_type: Optional[str] = None
    model_probability: Optional[float] = None
    market_probability: Optional[float] = None
    final_probability: Optional[float] = None
    implied_probability: Optional[float] = None
    edge_percent: Optional[float] = None
    ev_per_100: Optional[float] = None
    kelly_percent: Optional[float] = None
    suggested_stake: Optional[float] = None
    decision: Optional[str] = None
    minimum_playable_odds: Optional[int] = None
    actual_odds_taken: Optional[int] = None
    closing_odds: Optional[int] = None
    result: Optional[str] = "pending"
    status: Optional[str] = None
    risk_profile: Optional[str] = None
    confidence: Optional[float | str] = None
    correlation_group: Optional[str] = None
    user_action: Optional[str] = None
    manual_override: bool = False
    confirmed_bets_allowed: Optional[bool] = None
    notes: Optional[str] = None


class ActionBetResultRequest(BaseModel):
    bet_id: str
    result: str
    closing_odds: Optional[int] = None


# Response Models for Action Endpoints
class ActiveEventsResponse(BaseModel):
    ok: bool
    endpoint: str
    league: str
    provider: str
    count: int
    events: list[dict[str, Any]]
    error: Optional[str] = None
    detail: Optional[str] = None


class EventOddsResponse(BaseModel):
    ok: bool
    endpoint: str
    event_id: str
    league: str
    provider: str
    markets_requested: list[str]
    markets: list[dict[str, Any]]
    bookmakers: list[str]
    error: Optional[str] = None
    detail: Optional[str] = None


class FirstEventOddsResponse(BaseModel):
    ok: bool
    endpoint: str
    event_id: str
    league: str
    provider: str
    markets_requested: list[str]
    markets: list[dict[str, Any]]
    bookmakers: list[str]
    error: Optional[str] = None
    detail: Optional[str] = None


class PriceEventResponse(BaseModel):
    ok: bool
    endpoint: str
    event_id: str
    league: str
    provider: str
    markets_requested: list[str]
    markets: list[dict[str, Any]]
    bookmakers: list[str]
    pricing: list[dict[str, Any]]
    error: Optional[str] = None
    detail: Optional[str] = None


class ModelProbabilityResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    ok: bool
    endpoint: str
    final_probability: Optional[float] = None
    probability_type: Optional[str] = None
    market_probability: Optional[float] = None
    active_inputs: list[str] = []
    missing_inputs: list[str] = []
    applied_adjustments: dict[str, float] = {}
    adjustment_cap_warnings: list[str] = []
    model_limitations: list[str] = []
    data_quality_score: Optional[float] = None
    confidence: Optional[str] = None
    confidence_grade: Optional[str] = None
    provider_status: dict[str, str] = {}
    results: Optional[list[dict[str, Any]]] = None
    processed_rows: Optional[int] = None
    successful_rows: Optional[int] = None
    failed_rows: Optional[int] = None
    error: Optional[str] = None
    detail: Optional[str] = None


class EvaluateLinesResponse(BaseModel):
    ok: bool
    endpoint: str
    results: list[dict[str, Any]]
    summary: dict[str, Any]
    error: Optional[str] = None
    detail: Optional[str] = None


class AnalyzeEventResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    ok: bool
    endpoint: str
    sport: str
    league: str
    event_id: str
    markets_requested: list[str]
    probability_type: Optional[str] = None
    confirmed_bets: list[dict[str, Any]] = []
    target_lines: list[dict[str, Any]] = []
    no_bets: list[dict[str, Any]] = []
    warnings: list[str] = []
    model_limitations: list[str] = []
    missing_inputs: list[str] = []
    active_inputs: list[str] = []
    market_summary: list[dict[str, Any]] = []
    evaluation_results: list[dict[str, Any]] = []
    log_ready_rows: list[dict[str, Any]] = []
    error: Optional[str] = None
    detail: Optional[str] = None
    step_failed: Optional[str] = None


class SportModelConfigResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    sport_key: str = Field(..., description="Canonical registry sport key used by Action-safe betting routes and governance checks.")
    display_name: str = Field(..., description="Human-readable sport or league name.")
    status: str = Field(..., description="Current build status for this sport's model pipeline.")
    model_level: str = Field(..., description="Model maturity level: not_built, market_derived_only, projection_ready, blended_ready, or fully_independent.")
    confirmed_bets_allowed: bool = Field(..., description="Whether analyze-event may place qualifying results in confirmed_bets for this sport.")
    supported_markets: list[str] = Field(..., description="Markets the registry recognizes for this sport, such as h2h, spreads, totals, or outrights.")
    supported_props: list[str] = Field(..., description="Prop markets supported by this sport model; empty when props are not connected.")
    required_independent_inputs: list[str] = Field(..., description="Independent data inputs required before this sport can be promoted for confirmed bets.")
    optional_independent_inputs: list[str] = Field(..., description="Additional independent inputs that can improve model quality but are not mandatory.")
    provider_needs: list[str] = Field(..., description="Provider capabilities still needed for market data, projections, injuries, history, and backtesting.")
    recommended_providers: list[str] = Field(..., description="Configured or recommended provider IDs; empty when no provider has been selected.")
    model_components: list[str] = Field(..., description="Pipeline components currently represented by the sport model configuration.")
    officials_module: dict[str, Any] = Field(..., description="Shared officials-context module with the sport-specific official type and betting-edge strength.")
    risk_notes: list[str] = Field(..., description="Sport-specific limitations and governance notes.")
    correlation_rules: list[str] = Field(..., description="Rules for grouping correlated exposure within this sport.")
    log_fields_required: list[str] = Field(..., description="Fields that must be present in logs before model promotion or bet governance review.")


class SportsModelRegistrySummaryResponse(BaseModel):
    total_sports: int = Field(..., description="Total number of sport configurations returned by the registry.")
    confirmed_bet_enabled_sports: int = Field(..., description="Count of sports currently allowed to produce confirmed_bets.")
    market_derived_only_sports: int = Field(..., description="Count of sports using only market-derived probabilities.")
    not_built_sports: int = Field(..., description="Count of sports that are registered but not built.")


class SportsModelRegistryResponse(BaseModel):
    ok: bool = Field(..., description="True when the registry response was generated successfully.")
    endpoint: str = Field(..., description="Stable Action operation identifier for this registry response.")
    sports: list[SportModelConfigResponse] = Field(..., description="Ordered list of sport model registry configurations.")
    summary: SportsModelRegistrySummaryResponse = Field(..., description="Aggregate counts by eligibility and model level.")
    global_rules: list[str] = Field(..., description="Governance rules that apply to every sport in the registry.")
    error: Optional[str] = Field(None, description="Machine-readable error code, or null on success.")
    detail: Optional[str] = Field(None, description="Human-readable error detail, or null on success.")


class SportAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())

    ok: bool = False
    endpoint: str = "analyzeSportModel"
    error: Optional[str] = None
    detail: Optional[str] = None
    sport: Optional[Any] = None
    model_name: Optional[str] = None
    model_used: Optional[str] = None
    model_family: Optional[str] = None
    market: Optional[str] = None
    projected_score: Optional[Any] = None
    projected_margin: Optional[Any] = None
    projected_total: Optional[Any] = None
    projected_team_points: Optional[Any] = None
    projected_opponent_points: Optional[Any] = None
    true_probability: Optional[float] = None
    estimated_true_probability: Optional[float] = None
    final_probability: Optional[float] = None
    model_probability: Optional[float] = None
    raw_model_probability: Optional[float] = None
    calibrated_model_probability: Optional[float] = None
    market_anchor_probability: Optional[float] = None
    probability_calibration_applied: bool = False
    probability_sanity_flags: list[str] = []
    probability_cap_reason: Optional[str] = None
    implied_probability: Optional[float] = None
    edge: Optional[float] = None
    edge_percent: Optional[float] = None
    confidence: Optional[Any] = None
    risk: Optional[Any] = None
    risk_level: str
    model_status: Optional[Any] = None
    status: Optional[str] = None
    decision: Optional[str] = None
    partial_model_mode: bool = False
    recommended_unit_size: float
    no_bet_flags: list[str]
    correlation_notes: list[str]
    model_components: list[str]
    missing_inputs: list[str]
    backtest_status: str
    calibration_status: str
    logbook_ready_row: dict[str, Any]
    component_statuses: dict[str, Any]
    advanced_edge_components: dict[str, Any]
    provider_needs: list[str]
    risk_controller: dict[str, Any]
    wee_willie_market_weakness_detector: dict[str, Any]
    social_sentiment_engine: dict[str, Any]
    crowdsourced_signal_engine: dict[str, Any]
    public_bias_detector: dict[str, Any]
    news_velocity_detector: dict[str, Any]
    rumor_risk_filter: dict[str, Any]
    market_narrative_tracker: dict[str, Any]
    sentiment_calibration_status: str
    crowd_signal_calibration_status: str
    sentiment_no_bet_flags: list[str]
    officiating_analysis: dict[str, Any] = {}
    officiating_module_status: Optional[str] = None
    officiating_edge_detected: bool = False
    officiating_adjustment_probability_points: float = 0
    adjusted_true_probability: Optional[float] = None
    affected_markets: list[str] = []
    officiating_confidence: Optional[Any] = None
    officiating_risk_flags: list[str] = []
    officiating_summary: Optional[str] = None
    officiating_no_bet_reason: Optional[str] = None
    officiating_logbook_fields: dict[str, Any] = {}
    confirmed_bets: list[dict[str, Any]] = []
    target_lines: list[dict[str, Any]] = []
    target_props: list[dict[str, Any]] = []
    target_alt_lines: list[dict[str, Any]] = []
    no_bets: list[dict[str, Any]] = []
    best_correlated_parlay: Optional[Any] = None
    value_ranking: list[Any] = []
    risk_ranking: list[Any] = []
    provider_enrichment: dict[str, Any] = {}
    manual_review_required: Optional[Any] = None
    manual_ticket_preview: Optional[dict[str, Any]] = None
    full_board_preview: dict[str, Any]


class ScreenshotAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())

    ok: bool
    endpoint: str
    partial_model_mode: bool
    parsed_ticket: dict[str, Any]
    provider_enrichment: dict[str, Any]
    model_analysis: dict[str, Any]
    full_board_preview: dict[str, Any]
    missing_inputs: list[Any]
    no_bets: list[dict[str, Any]]
    confirmed_bets: list[dict[str, Any]]
    suggested_stake: Optional[Any] = None
    implied_probability: Optional[Any] = None
    logbook_ready_rows: list[dict[str, Any]]
    error: Optional[str] = None
    detail: Optional[str] = None


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


@app.get("/api/actions/betting/events/active", operation_id="getActiveBettingEvents", dependencies=[Depends(require_action_key)], summary="Get Active Betting Events", description="Retrieve active betting events for a specific league and provider with optional filtering.")
async def action_get_active_betting_events(
    league: str = Query(default="baseball_mlb", description="League or sport key (e.g. mlb, baseball_mlb)."),
    provider: Optional[str] = Query(None, description="Odds provider to use (defaults to configured provider)"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of events to return"),
):
    return await action_fetch_active_events_envelope(league, provider, limit)


@app.get(
    "/api/actions/models/sports-registry",
    operation_id="getSportsModelRegistry",
    dependencies=[Depends(require_action_key)],
    response_model=SportsModelRegistryResponse,
    summary="Get Sports Model Registry",
    description=(
        "Return the multi-sport model registry, including model maturity, required independent inputs, "
        "provider needs, market support, logging requirements, and confirmed-bet governance eligibility."
    ),
)
async def action_get_sports_model_registry():
    return multi_sport_model_registry.get_sports_model_registry_response()


@app.post(
    "/api/actions/models/sport-analysis",
    operation_id="analyzeSportModel",
    dependencies=[Depends(require_action_key)],
    response_model=SportAnalysisResponse,
    summary="Analyze Sport Model",
    description=(
        "Return the registered sport-model architecture foundation for a sport and market. "
        "This endpoint does not connect live providers and cannot create confirmed bets without required inputs, "
        "backtest proof, risk approval, and clear no-bet flags."
    ),
)
async def action_analyze_sport_model(payload: SportAnalysisRequest):
    try:
        return multi_sport_model_registry.analyze_sport_model(payload.model_dump(exclude_none=True))
    except Exception as exc:
        sport = None
        try:
            sport = payload.model_dump(exclude_none=True).get("sport")
        except Exception:
            sport = None
        return multi_sport_model_registry.sport_analysis_failed_response(
            sport=sport,
            detail=f"Sport analysis failed safely: {type(exc).__name__}",
        )


@app.post(
    "/api/actions/ticket/screenshot-analysis",
    operation_id="analyzeTicketScreenshot",
    dependencies=[Depends(require_action_key)],
    response_model=ScreenshotAnalysisResponse,
    summary="Analyze Ticket Screenshot",
    description=(
        "Analyze sportsbook ticket fields parsed from a screenshot or OCR text. "
        "OCR is optional; ChatGPT may send structured parsed fields directly."
    ),
)
async def action_analyze_ticket_screenshot(payload: ScreenshotAnalysisRequest):
    try:
        return screenshot_intake.analyze_screenshot_ticket(payload.model_dump(exclude_none=True))
    except Exception as exc:
        return {
            "ok": False,
            "endpoint": "ticketScreenshotAnalysis",
            "partial_model_mode": True,
            "parsed_ticket": {},
            "provider_enrichment": {},
            "model_analysis": {},
            "full_board_preview": {
                "confirmed_bets": [],
                "target_lines": [],
                "target_props": [],
                "target_alt_lines": [],
                "no_bets": [{"reason": "screenshot_analysis_failed_safely"}],
                "best_correlated_parlay": None,
                "value_ranking": [],
                "risk_ranking": [],
                "missing_inputs": [],
                "manual_review_required": ["Manual review required after handled error."],
                "logbook_ready_rows": [],
            },
            "missing_inputs": ["screenshot_analysis_failed"],
            "no_bets": [{"reason": "screenshot_analysis_failed_safely", "detail": type(exc).__name__}],
            "confirmed_bets": [],
            "suggested_stake": 0,
            "implied_probability": None,
            "logbook_ready_rows": [],
            "error": "screenshot_analysis_failed",
            "detail": f"Screenshot analysis failed safely: {type(exc).__name__}",
        }


@app.post(
    "/api/actions/betting/log-bet",
    operation_id="logBet",
    dependencies=[Depends(require_action_key)],
    summary="Log Bet",
    description="Create and append a Sharpsbook-style betting log entry.",
)
async def action_log_bet(payload: ActionBetLogRequest):
    entry = bet_log.create_bet_log_entry(payload.model_dump(exclude_none=True))
    bet_log.append_bet_log_entry(entry)
    return {"ok": True, "endpoint": "logBet", "bet": entry}


@app.post(
    "/api/actions/betting/log-result",
    operation_id="logBetResult",
    dependencies=[Depends(require_action_key)],
    summary="Log Bet Result",
    description="Update an existing logged bet with its result and calculated profit/loss.",
)
async def action_log_bet_result(payload: ActionBetResultRequest):
    updated = bet_log.update_bet_result(
        bet_id=payload.bet_id,
        result=payload.result,
        closing_odds=payload.closing_odds,
    )
    if updated is None:
        return {
            "ok": False,
            "endpoint": "logBetResult",
            "error": "BET_NOT_FOUND",
            "detail": f"No bet log entry found for bet_id {payload.bet_id}.",
        }
    return {"ok": True, "endpoint": "logBetResult", "bet": updated}


@app.get(
    "/api/actions/betting/logs",
    operation_id="getBetLogs",
    dependencies=[Depends(require_action_key)],
    summary="Get Bet Logs",
    description="Read Sharpsbook-style betting log entries.",
)
async def action_get_bet_logs(limit: int = Query(default=100, ge=1, le=1000)):
    entries = bet_log.read_bet_log_entries()
    return {
        "ok": True,
        "endpoint": "getBetLogs",
        "count": len(entries),
        "logs": entries[-limit:],
    }


@app.get(
    "/api/actions/betting/performance-summary",
    operation_id="getPerformanceSummary",
    dependencies=[Depends(require_action_key)],
    summary="Get Performance Summary",
    description="Summarize betting performance, ROI, yield, CLV, and error counts.",
)
async def action_get_performance_summary():
    return {
        "ok": True,
        "endpoint": "getPerformanceSummary",
        "summary": bet_log.get_performance_summary(),
    }


@app.get(
    "/api/actions/betting/bankroll-summary",
    operation_id="getBankrollSummary",
    dependencies=[Depends(require_action_key)],
    summary="Get Bankroll Summary",
    description="Summarize bankroll movement from logged bets.",
)
async def action_get_bankroll_summary():
    return {
        "ok": True,
        "endpoint": "getBankrollSummary",
        "summary": bet_log.get_bankroll_summary(),
    }


@app.get(
    "/api/actions/betting/clv-report",
    operation_id="getCLVReport",
    dependencies=[Depends(require_action_key)],
    summary="Get CLV Report",
    description="Compare actual odds taken against closing odds when available.",
)
async def action_get_clv_report():
    return {
        "ok": True,
        "endpoint": "getCLVReport",
        "report": bet_log.get_clv_report(),
    }


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


@app.get("/api/actions/betting/events/{event_id}/odds", operation_id="getEventOdds", dependencies=[Depends(require_action_key)], summary="Get Event Odds", description="Retrieve betting odds for a specific event across specified markets and bookmakers.")
async def action_get_event_odds(
    event_id: str,
    league: str = Query(default="baseball_mlb", description="League or sport key (e.g. mlb, baseball_mlb)."),
    provider: Optional[str] = Query(None, description="Odds provider to use (defaults to configured provider)"),
    markets: str = Query(default=DEFAULT_MARKETS, description="Comma-separated list of markets to retrieve"),
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


@app.get("/api/actions/betting/first-event-odds", operation_id="getFirstEventOdds", dependencies=[Depends(require_action_key)], summary="Get First Event Odds", description="Retrieve odds for the first available event in a league across specified markets and bookmakers.")
async def action_get_first_event_odds(
    league: str = Query(default="baseball_mlb", description="League or sport key (e.g. mlb, baseball_mlb)."),
    provider: Optional[str] = Query(None, description="Odds provider to use (defaults to configured provider)"),
    markets: str = Query(default=DEFAULT_MARKETS, description="Comma-separated list of markets to retrieve"),
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


@app.post("/api/actions/betting/evaluate-lines", operation_id="evaluateBettingLines", dependencies=[Depends(require_action_key)], summary="Evaluate Betting Lines", description="Evaluate betting lines with stake recommendations based on bankroll, risk profile, and model probabilities.")
async def action_evaluate_betting_lines(payload: EvaluateLinesRequest):
    try:
        out = bet_decision_engine.evaluate_lines_payload(payload.model_dump())
        ok = bool(out.get("ok", True))
        return {
            "ok": ok,
            "sport": out.get("sport"),
            "event": out.get("event"),
            "risk_profile": out.get("risk_profile"),
            "error": out.get("error"),
            "detail": out.get("detail"),
            "results": out.get("results") or [],
        }
    except Exception as exc:
        return {
            "ok": False,
            "sport": getattr(payload, "sport", None),
            "event": getattr(payload, "event", None),
            "risk_profile": getattr(payload, "risk_profile", None),
            "error": "REQUEST_ERROR",
            "detail": str(exc),
            "results": [],
        }


@app.post("/api/actions/betting/price-event", operation_id="priceBettingEvent", dependencies=[Depends(require_action_key)], summary="Price Betting Event", description="Price a betting event with stake recommendations based on bankroll, risk profile, and optional model probabilities.")
async def action_price_betting_event(payload: PriceEventRequest):
    endpoint_id = "priceBettingEvent"
    markets_requested = _parse_markets_requested(payload.markets)

    try:
        # Fetch event odds using the same Action safe odds logic
        odds_response = await action_fetch_event_odds_envelope(
            event_id=payload.event_id,
            league=payload.league,
            provider=payload.provider,
            markets_csv=payload.markets,
            bookmakers_csv=DEFAULT_BOOKMAKERS,
        )

        if not odds_response.get("ok"):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "market_summary": [],
                "best_prices": [],
                "evaluation_ready_lines": [],
                "warnings": [],
                "error": odds_response.get("error", "ODDS_FETCH_FAILED"),
                "detail": odds_response.get("detail", "Failed to fetch event odds"),
            }

        # Extract flat odds from markets
        flat_odds = []
        for market_block in odds_response.get("markets", []):
            for line in market_block.get("lines", []):
                flat_odds.append(line)

        if not flat_odds:
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "market_summary": [],
                "best_prices": [],
                "evaluation_ready_lines": [],
                "warnings": ["No odds data found for event"],
                "error": "NO_ODDS_DATA",
                "detail": "No odds data available for the requested event",
            }

        # Create evaluation-ready lines with optional model probabilities
        evaluation_lines = market_pricing.create_evaluation_ready_lines(
            flat_odds,
            payload.model_probabilities
        )

        # Create market summary
        market_summary = market_pricing.create_market_summary(evaluation_lines)

        # Extract best prices for the response
        best_prices = []
        for summary in market_summary:
            for selection in summary.get("selections", []):
                best_prices.append({
                    "market": summary["market"],
                    "line": summary["line"],
                    "selection": selection["selection"],
                    "best_odds_american": selection["best_odds"],
                    "consensus_probability": selection["consensus_probability"],
                    "fair_odds_american": selection["fair_odds"]
                })

        # Check for warnings
        warnings = []
        if not evaluation_lines:
            warnings.append("No evaluation-ready lines created")

        # Check for stale lines
        stale_count = sum(1 for line in evaluation_lines if line.get("stale_line_flag", False))
        if stale_count > 0:
            warnings.append(f"{stale_count} lines flagged as potentially stale")

        return {
            "ok": True,
            "endpoint": endpoint_id,
            "sport": payload.sport,
            "league": payload.league,
            "event_id": payload.event_id,
            "markets_requested": markets_requested,
            "market_summary": market_summary,
            "best_prices": best_prices,
            "evaluation_ready_lines": evaluation_lines,
            "warnings": warnings,
            "error": None,
            "detail": None,
        }

    except Exception as exc:
        return {
            "ok": False,
            "endpoint": endpoint_id,
            "sport": payload.sport,
            "league": payload.league,
            "event_id": payload.event_id,
            "markets_requested": markets_requested,
            "market_summary": [],
            "best_prices": [],
            "evaluation_ready_lines": [],
            "warnings": [],
            "error": "UNEXPECTED_ERROR",
            "detail": str(exc),
        }


@app.post("/api/actions/betting/model-probability", operation_id="estimateModelProbability", dependencies=[Depends(require_action_key)], summary="Estimate Model Probability", description="Calculate blended probabilities with adjustments, confidence scoring, and transparency outputs for betting decisions.")
async def action_calculate_model_probability(payload: ModelProbabilityRequest):
    endpoint_id = "estimateModelProbability"

    try:
        # If no top-level market_probability provided, try to infer from priced_rows
        if payload.market_probability is None:
            if not payload.priced_rows or len(payload.priced_rows) == 0:
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "error": "missing_market_probability",
                    "detail": "market_probability was not provided and no priced rows were available",
                    "final_probability": None,
                    "probability_type": None,
                    "market_probability": None,
                    "active_inputs": [],
                    "missing_inputs": [],
                    "applied_adjustments": {},
                    "adjustment_cap_warnings": [],
                    "model_limitations": [],
                    "data_quality_score": None,
                    "confidence": None,
                    "confidence_grade": None,
                    "provider_status": {}
                }

            # Process each priced row individually
            results = []
            for row in payload.priced_rows:
                # Infer market probability from row with priority: no_vig -> consensus -> implied
                market_prob = None
                if "no_vig_probability" in row and row["no_vig_probability"] is not None:
                    market_prob = row["no_vig_probability"]
                elif "consensus_probability" in row and row["consensus_probability"] is not None:
                    market_prob = row["consensus_probability"]
                elif "implied_probability" in row and row["implied_probability"] is not None:
                    market_prob = row["implied_probability"]

                if market_prob is None:
                    # Skip this row with warning
                    results.append({
                        "ok": False,
                        "row": row,
                        "error": "missing_probability_in_row",
                        "detail": "Row does not contain no_vig_probability, consensus_probability, or implied_probability"
                    })
                    continue

                # Create independent inputs from request
                inputs = model_probability.IndependentInputs(
                    projection_probability=payload.projection_probability,
                    pitcher_adjustment=payload.pitcher_adjustment,
                    weather_adjustment=payload.weather_adjustment,
                    lineup_adjustment=payload.lineup_adjustment,
                    bullpen_adjustment=payload.bullpen_adjustment,
                    injury_adjustment=payload.injury_adjustment,
                    park_factor_adjustment=payload.park_factor_adjustment,
                    umpire_adjustment=payload.umpire_adjustment,
                    player_prop_projection=payload.player_prop_projection,
                    sharp_market_probability=payload.sharp_market_probability,
                    closing_line_projection=payload.closing_line_projection,
                )

                # Create probability response for this row
                response = model_probability.create_probability_response(
                    market_probability=market_prob,
                    inputs=inputs
                )
                response["row"] = row
                results.append(response)

            return {
                "ok": True,
                "endpoint": endpoint_id,
                "results": results,
                "processed_rows": len(payload.priced_rows),
                "successful_rows": len([r for r in results if r.get("ok", False)]),
                "failed_rows": len([r for r in results if not r.get("ok", False)])
            }

        else:
            # Use provided market_probability (fallback behavior)
            inputs = model_probability.IndependentInputs(
                projection_probability=payload.projection_probability,
                pitcher_adjustment=payload.pitcher_adjustment,
                weather_adjustment=payload.weather_adjustment,
                lineup_adjustment=payload.lineup_adjustment,
                bullpen_adjustment=payload.bullpen_adjustment,
                injury_adjustment=payload.injury_adjustment,
                park_factor_adjustment=payload.park_factor_adjustment,
                umpire_adjustment=payload.umpire_adjustment,
                player_prop_projection=payload.player_prop_projection,
                sharp_market_probability=payload.sharp_market_probability,
                closing_line_projection=payload.closing_line_projection,
            )

            # Create probability response
            response = model_probability.create_probability_response(
                market_probability=payload.market_probability,
                inputs=inputs
            )

            return response

    except Exception as exc:
        return {
            "ok": False,
            "endpoint": endpoint_id,
            "error": "UNEXPECTED_ERROR",
            "detail": str(exc),
            "final_probability": None,
            "probability_type": None,
            "market_probability": None,
            "active_inputs": [],
            "missing_inputs": [],
            "applied_adjustments": {},
            "adjustment_cap_warnings": [],
            "model_limitations": [],
            "data_quality_score": None,
            "confidence": None,
            "confidence_grade": None,
            "provider_status": {}
        }


@app.post("/api/actions/betting/analyze-event", operation_id="analyzeBettingEvent", dependencies=[Depends(require_action_key)], summary="Analyze Betting Event", description="Complete betting analysis pipeline: fetch odds, price event, estimate probabilities, and evaluate lines.")
async def action_analyze_betting_event(payload: AnalyzeEventRequest):
    endpoint_id = "analyzeBettingEvent"
    markets_requested = _parse_markets_requested(payload.markets)

    try:
        # Step 1: Fetch odds using Action safe odds logic
        step = "fetch_odds"
        odds_response = await action_fetch_event_odds_envelope(
            event_id=payload.event_id,
            league=payload.league,
            provider=payload.provider,
            markets_csv=payload.markets,
            bookmakers_csv=DEFAULT_BOOKMAKERS,
        )

        if not odds_response.get("ok"):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": None,
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [],
                "warnings": [f"Failed to fetch odds: {odds_response.get('detail', 'Unknown error')}"],
                "model_limitations": [],
                "missing_inputs": [],
                "active_inputs": [],
                "market_summary": [],
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": odds_response.get("error", "ODDS_FETCH_FAILED"),
                "detail": odds_response.get("detail", "Failed to fetch event odds"),
                "step_failed": step
            }

        # Step 2: Price the event using priceBettingEvent logic
        step = "price_event"
        price_request = PriceEventRequest(
            sport=payload.sport,
            event_id=payload.event_id,
            league=payload.league,
            markets=payload.markets,
            provider=payload.provider,
            bankroll=payload.bankroll,
            unit_size=payload.unit_size,
            risk_profile=payload.risk_profile,
            model_probabilities=None  # Will be set after model probability step
        )

        # Create a mock price response since we need model probabilities first
        price_response = await action_price_betting_event(price_request)

        if not price_response.get("ok"):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": None,
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [],
                "warnings": [f"Failed to price event: {price_response.get('detail', 'Unknown error')}"],
                "model_limitations": [],
                "missing_inputs": [],
                "active_inputs": [],
                "market_summary": price_response.get("market_summary", []),
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": price_response.get("error", "EVENT_PRICING_FAILED"),
                "detail": price_response.get("detail", "Failed to price betting event"),
                "step_failed": step
            }

        # Step 3: Estimate model probabilities
        step = "estimate_probabilities"
        model_request = ModelProbabilityRequest(
            market_probability=None,
            projection_probability=payload.independent_inputs.get("projection_probability") if payload.independent_inputs else None,
            pitcher_adjustment=payload.independent_inputs.get("pitcher_adjustment") if payload.independent_inputs else None,
            weather_adjustment=payload.independent_inputs.get("weather_adjustment") if payload.independent_inputs else None,
            lineup_adjustment=payload.independent_inputs.get("lineup_adjustment") if payload.independent_inputs else None,
            bullpen_adjustment=payload.independent_inputs.get("bullpen_adjustment") if payload.independent_inputs else None,
            injury_adjustment=payload.independent_inputs.get("injury_adjustment") if payload.independent_inputs else None,
            park_factor_adjustment=payload.independent_inputs.get("park_factor_adjustment") if payload.independent_inputs else None,
            umpire_adjustment=payload.independent_inputs.get("umpire_adjustment") if payload.independent_inputs else None,
            player_prop_projection=payload.independent_inputs.get("player_prop_projection") if payload.independent_inputs else None,
            sharp_market_probability=payload.independent_inputs.get("sharp_market_probability") if payload.independent_inputs else None,
            closing_line_projection=payload.independent_inputs.get("closing_line_projection") if payload.independent_inputs else None,
            priced_rows=price_response.get("evaluation_ready_lines", [])
        )

        model_response = await action_calculate_model_probability(model_request)

        if not model_response.get("ok"):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": None,
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [],
                "warnings": [f"Failed to estimate probabilities: {model_response.get('detail', 'Unknown error')}"],
                "model_limitations": model_response.get("model_limitations", []),
                "missing_inputs": model_response.get("missing_inputs", []),
                "active_inputs": model_response.get("active_inputs", []),
                "market_summary": price_response.get("market_summary", []),
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": model_response.get("error", "PROBABILITY_ESTIMATION_FAILED"),
                "detail": model_response.get("detail", "Failed to estimate model probabilities"),
                "step_failed": step
            }

        # Extract model probability results for matching
        model_results = model_response.get("results", [])
        probability_type = model_response.get("probability_type")
        if model_results:
            for result in model_results:
                if result.get("ok", False):
                    probability_type = result.get("probability_type", probability_type)
                    break

        if not model_results and probability_type != "market_derived":
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": probability_type,
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [],
                "warnings": ["Model probabilities were generated but could not be matched to evaluation lines."],
                "model_limitations": model_response.get("model_limitations", []),
                "missing_inputs": model_response.get("missing_inputs", []),
                "active_inputs": model_response.get("active_inputs", []),
                "market_summary": price_response.get("market_summary", []),
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": "model_probability_handoff_failed",
                "detail": "Model probabilities were generated but could not be matched to evaluation lines.",
                "step_failed": step
            }

        # Create a mapping key for matching model results to evaluation lines
        model_probability_map = {}
        for result in model_results:
            if result.get("ok", False) and "row" in result:
                row = result["row"]
                # Create matching key using sportsbook, market, selection, line, odds_american
                match_key = (
                    row.get("sportsbook"),
                    row.get("market"),
                    row.get("selection"),
                    row.get("line"),
                    row.get("odds_american")
                )
                model_probability_map[match_key] = result

        # Step 4: Evaluate lines using evaluateBettingLines logic
        step = "evaluate_lines"
        evaluation_ready_lines = price_response.get("evaluation_ready_lines", [])

        if not evaluation_ready_lines:
            return {
                "ok": True,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": model_response.get("probability_type", "unknown"),
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [{"reason": "No evaluation-ready lines available", "lines": []}],
                "warnings": ["No lines available for evaluation"],
                "model_limitations": model_response.get("model_limitations", []),
                "missing_inputs": model_response.get("missing_inputs", []),
                "active_inputs": model_response.get("active_inputs", []),
                "market_summary": price_response.get("market_summary", []),
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": None,
                "detail": "Analysis completed but no lines available for evaluation",
                "step_failed": None
            }

        # Filter and validate evaluation_ready_lines before passing to evaluateBettingLines
        valid_evaluation_lines = []
        validation_warnings = []

        for line in evaluation_ready_lines:
            # Check required fields
            sportsbook = line.get("sportsbook")
            market = line.get("market")
            selection = line.get("selection")
            odds_american = line.get("odds_american")

            # Skip rows with missing required fields
            if sportsbook is None or sportsbook == "unknown":
                validation_warnings.append("Skipped line because sportsbook was missing.")
                continue

            if odds_american is None:
                validation_warnings.append("Skipped line because odds_american was missing.")
                continue

            if market is None or selection is None:
                validation_warnings.append("Skipped line because market or selection was missing.")
                continue

            # Create matching key for this evaluation line
            match_key = (
                sportsbook,
                market,
                selection,
                line.get("line"),
                odds_american
            )

            # Find matching model probability result
            model_result = model_probability_map.get(match_key)

            # Determine model_probability based on probability type and line data.
            # Market-derived analysis must use the probability from this same line.
            if probability_type == "market_derived":
                model_probability = (
                    line.get("no_vig_probability")
                    if line.get("no_vig_probability") is not None
                    else line.get("consensus_probability")
                    if line.get("consensus_probability") is not None
                    else line.get("implied_probability")
                )
            elif model_result:
                model_probability = model_result.get("final_probability")
            else:
                model_probability = None

            # Validate model_probability
            if (
                model_probability is None
                or model_probability <= 0
                or model_probability >= 1
            ):
                validation_warnings.append("Skipped line because model_probability was invalid for evaluation.")
                continue

            # Create valid evaluation line with matched model probability
            valid_line = {
                "sportsbook": sportsbook,
                "market": market,
                "selection": selection,
                "line": line.get("line"),
                "odds_american": odds_american,
                "model_probability": model_probability,
                "no_vig_probability": line.get("no_vig_probability"),
                "consensus_probability": line.get("consensus_probability"),
                "implied_probability": line.get("implied_probability"),
                "correlation_group": line.get("correlation_group"),
                "opening_odds_american": line.get("opening_odds_american")
            }

            valid_evaluation_lines.append(valid_line)

        # If no valid lines, return error response
        if not valid_evaluation_lines:
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": model_response.get("probability_type", "unknown"),
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [],
                "warnings": validation_warnings,
                "model_limitations": model_response.get("model_limitations", []),
                "missing_inputs": model_response.get("missing_inputs", []),
                "active_inputs": model_response.get("active_inputs", []),
                "market_summary": price_response.get("market_summary", []),
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": "no_valid_evaluation_lines",
                "detail": "No valid sportsbook lines were available for evaluation.",
                "step_failed": "evaluate_lines"
            }

        evaluate_request = EvaluateLinesRequest(
            sport=payload.sport,
            event=f"{payload.league} - {payload.event_id}",
            bankroll=payload.bankroll,
            unit_size=payload.unit_size,
            risk_profile=payload.risk_profile,
            lines=valid_evaluation_lines,
            max_stake_pct=payload.max_stake_pct
        )

        evaluate_response = await action_evaluate_betting_lines(evaluate_request)

        if not evaluate_response.get("ok"):
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "markets_requested": markets_requested,
                "probability_type": model_response.get("probability_type", "unknown"),
                "confirmed_bets": [],
                "target_lines": [],
                "no_bets": [],
                "warnings": [f"Failed to evaluate lines: {evaluate_response.get('detail', 'Unknown error')}"],
                "model_limitations": model_response.get("model_limitations", []),
                "missing_inputs": model_response.get("missing_inputs", []),
                "active_inputs": model_response.get("active_inputs", []),
                "market_summary": price_response.get("market_summary", []),
                "evaluation_results": [],
                "log_ready_rows": [],
                "error": evaluate_response.get("error", "LINE_EVALUATION_FAILED"),
                "detail": evaluate_response.get("detail", "Failed to evaluate betting lines"),
                "step_failed": step
            }

        # Step 5: Process results and categorize bets
        evaluation_results = evaluate_response.get("results", [])
        confirmed_bets = []
        target_lines = []
        no_bets = []
        warnings = []
        registry_sport_key = payload.sport
        if not multi_sport_model_registry.is_supported_sport(registry_sport_key):
            registry_sport_key = payload.league
        sport_confirmed_bets_allowed = multi_sport_model_registry.confirmed_bets_allowed(registry_sport_key)
        sport_model_level = multi_sport_model_registry.classify_model_level(registry_sport_key)
        confirmed_bet_blocked_count = 0

        for result in evaluation_results:
            decision = result.get("decision")
            normalized_decision = decision.lower().strip() if isinstance(decision, str) else ""
            bet_like_decisions = {"bet", "strong_bet", "strong bet"}
            is_bet_like = normalized_decision in bet_like_decisions

            # Market-derived or registry-blocked sports cannot produce confirmed bets.
            if probability_type in {"market_derived", "market_derived_only"} or not sport_confirmed_bets_allowed:

                if is_bet_like:
                    result["decision"] = (
                        "target_market_derived"
                        if probability_type in {"market_derived", "market_derived_only"}
                        else "target_registry_blocked"
                    )
                    result["market_derived_only"] = probability_type in {"market_derived", "market_derived_only"}
                    result["confirmed_bets_allowed"] = False
                    result["model_level"] = sport_model_level
                    target_lines.append(result)
                    confirmed_bet_blocked_count += 1
                elif decision in ["TARGET", "WATCH"]:
                    target_lines.append(result)
                else:
                    no_bets.append(result)
            else:
                if decision == "BET":
                    confirmed_bets.append(result)
                elif decision in ["TARGET", "WATCH"]:
                    target_lines.append(result)
                else:
                    no_bets.append(result)

        if probability_type == "market_derived":
            warnings.append("Using market-derived probability only; no independent projection data was provided.")
            warnings.append("Line evaluated with market-derived probability only; not a confirmed betting recommendation.")
        elif probability_type == "market_derived_only":
            warnings.append("Using market-derived probability only; no independent projection data was provided.")
            warnings.append("Line evaluated with market-derived probability only; not a confirmed betting recommendation.")

        if confirmed_bet_blocked_count and not sport_confirmed_bets_allowed:
            warnings.append(
                "Confirmed bets are disabled for this sport in the model registry until independent projection inputs are connected."
            )

        # Add warnings for missing inputs
        if model_results:
            # Get missing inputs from first successful model result
            for result in model_results:
                if result.get("ok", False):
                    missing_inputs = result.get("missing_inputs", [])
                    if missing_inputs:
                        warnings.append(f"Missing model inputs: {', '.join(missing_inputs)}")
                    break

        # Add validation warnings
        warnings.extend(validation_warnings)

        # Get model data from first successful result
        model_limitations = []
        missing_inputs = []
        active_inputs = []
        if model_results:
            for result in model_results:
                if result.get("ok", False):
                    model_limitations = result.get("model_limitations", [])
                    missing_inputs = result.get("missing_inputs", [])
                    active_inputs = result.get("active_inputs", [])
                    break

        # Create log-ready rows
        log_ready_rows = []
        for result in evaluation_results:
            log_row = {
                "timestamp": utc_now(),
                "sport": payload.sport,
                "league": payload.league,
                "event_id": payload.event_id,
                "market": result.get("market"),
                "selection": result.get("selection"),
                "line": result.get("line"),
                "odds_american": result.get("odds_american"),
                "decision": result.get("decision"),
                "stake": result.get("stake"),
                "expected_value": result.get("expected_value"),
                "probability_type": probability_type,
                "final_probability": result.get("model_probability"),
                "risk_profile": payload.risk_profile,
                "bankroll": payload.bankroll,
                "unit_size": payload.unit_size
            }
            log_ready_rows.append(log_row)

        return {
            "ok": True,
            "endpoint": endpoint_id,
            "sport": payload.sport,
            "league": payload.league,
            "event_id": payload.event_id,
            "markets_requested": markets_requested,
            "probability_type": probability_type,
            "confirmed_bets": confirmed_bets,
            "target_lines": target_lines,
            "no_bets": no_bets,
            "warnings": warnings,
            "model_limitations": model_limitations,
            "missing_inputs": missing_inputs,
            "active_inputs": active_inputs,
            "market_summary": price_response.get("market_summary", []),
            "evaluation_results": evaluation_results,
            "log_ready_rows": log_ready_rows,
            "error": None,
            "detail": None,
            "step_failed": None
        }

    except Exception as exc:
        return {
            "ok": False,
            "endpoint": endpoint_id,
            "sport": payload.sport,
            "league": payload.league,
            "event_id": payload.event_id,
            "markets_requested": markets_requested,
            "probability_type": None,
            "confirmed_bets": [],
            "target_lines": [],
            "no_bets": [],
            "warnings": [f"Unexpected error during analysis: {str(exc)}"],
            "model_limitations": [],
            "missing_inputs": [],
            "active_inputs": [],
            "market_summary": [],
            "evaluation_results": [],
            "log_ready_rows": [],
            "error": "UNEXPECTED_ERROR",
            "detail": str(exc),
            "step_failed": "unknown"
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


@app.post("/api/bets/log", operation_id="logBetCsv", dependencies=[Depends(require_action_key)])
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


app.openapi = custom_openapi;
