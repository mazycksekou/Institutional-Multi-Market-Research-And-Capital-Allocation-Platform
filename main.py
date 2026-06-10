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
import automation_scheduler
import bet_log
import bet_decision_engine
import market_pricing
import multi_sport_model_registry
import model_probability
import screenshot_intake
from automation_scheduler.data_paths import get_runtime_data_path, get_automation_data_dir
from automation_scheduler.response_compactor import (
    compact_advanced_red_team_response,
    compact_calibration_response,
    compact_calibration_collector_response,
    compact_cfbd_adapter_verification_response,
    compact_data_availability_tiers_response,
    compact_deepseek_review_response,
    compact_data_source_coverage_response,
    compact_data_source_env_vars_response,
    compact_data_source_health_response,
    compact_data_source_priorities_response,
    compact_data_source_registry_response,
    compact_data_source_research_lanes_response,
    compact_public_apis_expansion_report_response,
    compact_outcome_ingest_response,
    compact_outcome_import_response,
    compact_outcomes_response,
    compact_balance_sheet_risk_response,
    compact_baseball_impact_diagnostics_response,
    compact_baseball_impact_readiness_response,
    compact_basketball_player_impact_readiness_response,
    compact_basketball_player_impact_response,
    compact_broker_quality_response,
    compact_combat_impact_diagnostics_response,
    compact_combat_impact_readiness_response,
    compact_micro_outcome_calibration_response,
    compact_pattern_calibration_response,
    compact_pattern_detection_response,
    compact_pattern_review_queue_response,
    compact_small_account_review_response,
    compact_settlement_discovery_response,
    compact_provider_status,
    compact_governance_inventory,
    compact_governance_report,
    compact_health_response,
    compact_institutional_execution_response,
    compact_institutional_lab_health_response,
    compact_institutional_lab_run_response,
    compact_institutional_report_response,
    compact_intelligence_readiness_response,
    compact_extreme_randomness_diagnostics_response,
    compact_extreme_randomness_report_response,
    compact_football_impact_diagnostics_response,
    compact_football_impact_readiness_response,
    compact_golf_impact_diagnostics_response,
    compact_golf_impact_readiness_response,
    compact_hockey_impact_diagnostics_response,
    compact_hockey_impact_readiness_response,
    compact_manifold_map_response,
    compact_manifold_review_response,
    compact_performance_health,
    compact_performance_report,
    compact_provider_health_response,
    compact_provider_registry_response,
    compact_review_queue_response,
    compact_run_once_response,
    compact_soccer_impact_diagnostics_response,
    compact_soccer_impact_readiness_response,
    compact_strategy_readiness_response,
    compact_tennis_impact_diagnostics_response,
    compact_tennis_impact_readiness_response,
    compact_validation_response,
    redact_and_limit_payload,
)
from model_governance.governance_health import get_governance_health
from model_governance.model_inventory import get_model_inventory
from model_governance.governance_report import generate_governance_report
from model_governance.model_validation_report import build_model_validation_report
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
DATA_DIR = get_automation_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)
BETS_FILE = get_runtime_data_path("bets.csv")

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
    "mixed martial arts": "mma_mixed_martial_arts",
    "combat sports": "mma_mixed_martial_arts",
    "boxing": "boxing",
    "atp": "tennis_atp",
    "wta": "tennis_wta",
    "tennis": "tennis_atp",
    "golf": "golf_pga",
    "pga": "golf_pga",
    "pga_tour": "golf_pga",
    "liv": "golf_pga",
    "liv_golf": "golf_pga",
    "dp_world_tour": "golf_pga",
    "european_tour": "golf_pga",
    "lpga": "golf_pga",
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
    "boxing": "Boxing",
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
    input_stats: Optional[Any] = None


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
    input_normalizer: Optional[str] = Field(None, description="Shared screenshot/direct input normalizer registered for confirmed-capable sports.")
    screenshot_alias_test_payload: Optional[dict[str, Any]] = Field(None, description="Live-style alias payload used to enforce screenshot normalization parity.")


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
    stake: Optional[Any] = None
    implied_probability: Optional[Any] = None
    confidence: Optional[Any] = None
    decision: Optional[str] = None
    status: Optional[str] = None
    logbook_ready_rows: list[dict[str, Any]]
    error: Optional[str] = None
    detail: Optional[str] = None


class AutomationRunOnceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    run_key: Optional[str] = None
    injected_data: dict[str, Any] = Field(default_factory=dict)


class AutomationOutcomeIngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    persist: bool = False
    source: str = "local_manual"
    records: list[dict[str, Any]] = Field(default_factory=list)


class AutomationOutcomeLocalSettlementImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    persist: bool = False
    source: str = "local_repo_migration"
    migration_version: str = "kalshi_outcome_migration_v1"
    records: list[dict[str, Any]] = Field(default_factory=list)
    supporting_paper_decisions: list[dict[str, Any]] = Field(default_factory=list)


class AutomationSettlementDiscoveryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    pending_rows: list[dict[str, Any]] = Field(default_factory=list)
    imported_rows: list[dict[str, Any]] = Field(default_factory=list)
    use_kalshi_snapshot: bool = True
    write_local_report: bool = False


class AutomationCalibrationCollectorRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    persist_outcomes: bool = False
    max_new_contracts: Optional[int] = 50
    target_daily_new_contracts: Optional[int] = 250
    hard_cap_daily_new_contracts: Optional[int] = 500
    max_markets_scanned: Optional[int] = 25000
    include_short_term: bool = True
    include_medium_term: bool = True
    include_long_term: bool = True
    adaptive_throttle: bool = True
    deepseek_review: bool = False


class AutomationCalibrationCollectorScheduledRunRequest(BaseModel):
    model_config = ConfigDict(extra="allow", protected_namespaces=())

    trigger_type: Optional[str] = "scheduled_endpoint"
    target_daily_new_contracts: Optional[int] = 250
    hard_cap_daily_new_contracts: Optional[int] = 500
    max_new_contracts_per_cycle: Optional[int] = 50
    max_markets_scanned: Optional[int] = 25000
    adaptive_throttle: bool = True
    include_short_term: bool = True
    include_medium_term: bool = True
    include_long_term: bool = True
    deepseek_review: bool = False


class AutomationDeepSeekReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    collector_cycle_report: dict[str, Any] = Field(default_factory=dict)
    daily_report: dict[str, Any] = Field(default_factory=dict)
    calibration_report: dict[str, Any] = Field(default_factory=dict)
    sampled_contracts: list[dict[str, Any]] = Field(default_factory=list)
    candidate: dict[str, Any] = Field(default_factory=dict)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    core_model_action: Optional[str] = None
    enabled: Optional[bool] = None
    review_queue_summary: dict[str, Any] = Field(default_factory=dict)
    outcome_summary: dict[str, Any] = Field(default_factory=dict)
    provider_health_summary: dict[str, Any] = Field(default_factory=dict)
    manifold_cluster_summary: dict[str, Any] = Field(default_factory=dict)
    markov_hmm_summary: dict[str, Any] = Field(default_factory=dict)
    sportsbook_full_board_summary: dict[str, Any] = Field(default_factory=dict)
    stock_crypto_pattern_summary: dict[str, Any] = Field(default_factory=dict)
    kalshi_prediction_market_summary: dict[str, Any] = Field(default_factory=dict)
    small_account_summary: dict[str, Any] = Field(default_factory=dict)
    security_readiness_summary: dict[str, Any] = Field(default_factory=dict)
    strategy_readiness_summary: dict[str, Any] = Field(default_factory=dict)
    trap_no_bet_summary: dict[str, Any] = Field(default_factory=dict)


class AutomationDeepSeekRedTeamRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    candidate: dict[str, Any] = Field(default_factory=dict)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    enabled: Optional[bool] = None
    review_queue_summary: dict[str, Any] = Field(default_factory=dict)
    calibration_summary: dict[str, Any] = Field(default_factory=dict)
    outcome_summary: dict[str, Any] = Field(default_factory=dict)
    provider_health_summary: dict[str, Any] = Field(default_factory=dict)
    manifold_cluster_summary: dict[str, Any] = Field(default_factory=dict)
    markov_hmm_summary: dict[str, Any] = Field(default_factory=dict)
    sportsbook_full_board_summary: dict[str, Any] = Field(default_factory=dict)
    stock_crypto_pattern_summary: dict[str, Any] = Field(default_factory=dict)
    kalshi_prediction_market_summary: dict[str, Any] = Field(default_factory=dict)
    small_account_summary: dict[str, Any] = Field(default_factory=dict)
    security_readiness_summary: dict[str, Any] = Field(default_factory=dict)
    strategy_readiness_summary: dict[str, Any] = Field(default_factory=dict)
    trap_no_bet_summary: dict[str, Any] = Field(default_factory=dict)


class AutomationAdvancedShapeDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    candidate: dict[str, Any] = Field(default_factory=dict)
    historical_records: list[dict[str, Any]] = Field(default_factory=list)
    labeled_records: list[dict[str, Any]] = Field(default_factory=list)
    calibration_records: list[dict[str, Any]] = Field(default_factory=list)
    sequences: dict[str, Any] = Field(default_factory=dict)
    provider: Optional[str] = None
    persist: bool = False


class AutomationBasketballPlayerImpactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    candidate: dict[str, Any] = Field(default_factory=dict)
    outcome_records: list[dict[str, Any]] = Field(default_factory=list)
    red_team_provider: Optional[str] = None


class AutomationExtremeSignalDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    candidate: dict[str, Any] = Field(default_factory=dict)
    baseline_values: list[Any] = Field(default_factory=list)
    matrix_payload: dict[str, Any] = Field(default_factory=dict)


class AutomationFootballImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "americanfootball_nfl"
    market_type: str = "spread"
    dry_run: bool = True
    team_context: dict[str, Any] = Field(default_factory=dict)
    player_context: dict[str, Any] = Field(default_factory=dict)
    play_drive_context: dict[str, Any] = Field(default_factory=dict)
    personnel_context: dict[str, Any] = Field(default_factory=dict)
    matchup_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationHockeyImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "icehockey_nhl"
    market_type: str = "moneyline"
    dry_run: bool = True
    game_context: dict[str, Any] = Field(default_factory=dict)
    team_context: dict[str, Any] = Field(default_factory=dict)
    skater_context: dict[str, Any] = Field(default_factory=dict)
    goalie_context: dict[str, Any] = Field(default_factory=dict)
    line_context: dict[str, Any] = Field(default_factory=dict)
    pair_context: dict[str, Any] = Field(default_factory=dict)
    special_teams_context: dict[str, Any] = Field(default_factory=dict)
    transition_context: dict[str, Any] = Field(default_factory=dict)
    shot_quality_context: dict[str, Any] = Field(default_factory=dict)
    matchup_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationSoccerImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "soccer"
    market_type: str = "three_way_moneyline"
    dry_run: bool = True
    game_context: dict[str, Any] = Field(default_factory=dict)
    team_context: dict[str, Any] = Field(default_factory=dict)
    player_context: dict[str, Any] = Field(default_factory=dict)
    lineup_context: dict[str, Any] = Field(default_factory=dict)
    tactical_context: dict[str, Any] = Field(default_factory=dict)
    possession_value_context: dict[str, Any] = Field(default_factory=dict)
    shot_quality_context: dict[str, Any] = Field(default_factory=dict)
    pressing_context: dict[str, Any] = Field(default_factory=dict)
    transition_context: dict[str, Any] = Field(default_factory=dict)
    set_piece_context: dict[str, Any] = Field(default_factory=dict)
    goalkeeper_context: dict[str, Any] = Field(default_factory=dict)
    referee_context: dict[str, Any] = Field(default_factory=dict)
    matchup_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationBaseballImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "baseball_mlb"
    market_type: str = "moneyline"
    dry_run: bool = True
    game_context: dict[str, Any] = Field(default_factory=dict)
    team_context: dict[str, Any] = Field(default_factory=dict)
    pitcher_context: dict[str, Any] = Field(default_factory=dict)
    batter_context: dict[str, Any] = Field(default_factory=dict)
    lineup_context: dict[str, Any] = Field(default_factory=dict)
    bullpen_context: dict[str, Any] = Field(default_factory=dict)
    catcher_context: dict[str, Any] = Field(default_factory=dict)
    defense_context: dict[str, Any] = Field(default_factory=dict)
    baserunning_context: dict[str, Any] = Field(default_factory=dict)
    park_weather_context: dict[str, Any] = Field(default_factory=dict)
    umpire_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationGolfImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "golf"
    market_type: str = "top_20"
    dry_run: bool = True
    tournament_context: dict[str, Any] = Field(default_factory=dict)
    player_context: dict[str, Any] = Field(default_factory=dict)
    strokes_gained_context: dict[str, Any] = Field(default_factory=dict)
    off_tee_context: dict[str, Any] = Field(default_factory=dict)
    approach_context: dict[str, Any] = Field(default_factory=dict)
    around_green_context: dict[str, Any] = Field(default_factory=dict)
    putting_context: dict[str, Any] = Field(default_factory=dict)
    course_context: dict[str, Any] = Field(default_factory=dict)
    weather_context: dict[str, Any] = Field(default_factory=dict)
    wave_context: dict[str, Any] = Field(default_factory=dict)
    field_context: dict[str, Any] = Field(default_factory=dict)
    form_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    simulation_context: dict[str, Any] = Field(default_factory=dict)
    tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationCombatImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "combat_sports"
    market_type: str = "moneyline"
    dry_run: bool = True
    bout_context: dict[str, Any] = Field(default_factory=dict)
    fighter_a_context: dict[str, Any] = Field(default_factory=dict)
    fighter_b_context: dict[str, Any] = Field(default_factory=dict)
    striking_context: dict[str, Any] = Field(default_factory=dict)
    grappling_context: dict[str, Any] = Field(default_factory=dict)
    phase_context: dict[str, Any] = Field(default_factory=dict)
    damage_context: dict[str, Any] = Field(default_factory=dict)
    pace_cardio_context: dict[str, Any] = Field(default_factory=dict)
    matchup_context: dict[str, Any] = Field(default_factory=dict)
    ruleset_context: dict[str, Any] = Field(default_factory=dict)
    judging_referee_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    film_tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationTennisImpactDiagnosticsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    sport: str = "tennis"
    market_type: str = "moneyline"
    dry_run: bool = True
    match_context: dict[str, Any] = Field(default_factory=dict)
    player_a_context: dict[str, Any] = Field(default_factory=dict)
    player_b_context: dict[str, Any] = Field(default_factory=dict)
    serve_context: dict[str, Any] = Field(default_factory=dict)
    return_context: dict[str, Any] = Field(default_factory=dict)
    surface_context: dict[str, Any] = Field(default_factory=dict)
    format_context: dict[str, Any] = Field(default_factory=dict)
    pressure_context: dict[str, Any] = Field(default_factory=dict)
    tiebreak_context: dict[str, Any] = Field(default_factory=dict)
    matchup_context: dict[str, Any] = Field(default_factory=dict)
    conditions_context: dict[str, Any] = Field(default_factory=dict)
    availability_context: dict[str, Any] = Field(default_factory=dict)
    incentive_context: dict[str, Any] = Field(default_factory=dict)
    calibration_context: dict[str, Any] = Field(default_factory=dict)
    point_context: dict[str, Any] = Field(default_factory=dict)
    tracking_context: dict[str, Any] = Field(default_factory=dict)


class AutomationManifoldMapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    item: dict[str, Any] = Field(default_factory=dict)
    historical_records: list[dict[str, Any]] = Field(default_factory=list)


class AutomationCrossAssetManifoldReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    persist: bool = True
    max_items: int = 250
    items: list[dict[str, Any]] = Field(default_factory=list)
    historical_records: list[dict[str, Any]] = Field(default_factory=list)


class AutomationPatternDetectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    items: list[dict[str, Any]] = Field(default_factory=list)


class AutomationSmallAccountReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    persist_queue: bool = False
    session_state: dict[str, Any] = Field(default_factory=dict)
    items: list[dict[str, Any]] = Field(default_factory=list)


class DataSourceVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    module: Optional[str] = None
    persist_report: bool = True


class NcaafCfbdVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    season: Optional[int] = None
    week: Optional[int] = None
    max_records: int = 5
    fetch_live_sample: bool = False
    sample_profile: str = "games_tiny"
    max_provider_calls: int = 1
    include_games: bool = True
    include_team_stats: bool = False
    include_advanced_stats: bool = False
    include_rankings: bool = False
    include_lines: bool = False


class InstitutionalLabRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    dry_run: bool = True
    asset_classes: list[str] = Field(default_factory=lambda: ["prediction_market", "stock", "bond", "major_asset", "sportsbook"])
    read_existing_outputs_only: bool = True
    persist_lab_report: bool = True
    persist_outcomes: bool = False
    deepseek_review: bool = False
    execution_simulation: bool = False


class InstitutionalDeepSeekReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    report: dict[str, Any] = Field(default_factory=dict)
    enabled: Optional[bool] = None


class InstitutionalExecutionSimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    simulation_only: Optional[bool] = None
    live_execution_requested: bool = False
    candidate_id: Optional[str] = None
    asset_class: Optional[str] = None
    provider: Optional[str] = None
    human_command: str = "simulate_only"
    max_theoretical_risk: float = 0
    submit_live_order: bool = False
    provider_write: bool = False
    execution_allowed: bool = False
    live_execution_enabled: bool = False
    auto_execution_enabled: bool = False
    auto_bet_enabled: bool = False
    auto_trade_enabled: bool = False
    kalshi_order_execution_enabled: bool = False
    sportsbook_bet_execution_enabled: bool = False
    broker_order_execution_enabled: bool = False


class PerformanceBacktestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    model_id: str = Field(min_length=1, max_length=120)
    historical_rows_path: Optional[str] = None
    rows: Optional[list[dict[str, Any]]] = None
    dry_run: bool = True


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


@app.get("/api/automation/health", operation_id="getAutomationSchedulerHealth")
async def get_automation_scheduler_health():
    health = automation_scheduler.get_scheduler_health()
    return compact_health_response(health)


@app.get("/api/automation/security-readiness", operation_id="getAutomationSecurityReadiness")
async def get_automation_security_readiness_endpoint():
    return automation_scheduler.get_security_readiness()


@app.get("/api/automation/intelligence-readiness", operation_id="getAutomationIntelligenceReadiness")
async def get_automation_intelligence_readiness_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = automation_scheduler.get_intelligence_readiness()
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_intelligence_readiness_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/strategy-readiness", operation_id="getAutomationStrategyReadiness")
async def get_automation_strategy_readiness_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=50)):
    cap = min(max(int(limit), 1), 100 if verbose else 50)
    payload = automation_scheduler.get_strategy_readiness()
    compact = compact_strategy_readiness_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/basketball-player-impact-readiness", operation_id="getAutomationBasketballPlayerImpactReadiness")
async def get_automation_basketball_player_impact_readiness_endpoint(
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=20),
):
    cap = min(max(int(limit), 1), 100 if verbose else 20)
    payload = automation_scheduler.get_basketball_player_impact_readiness()
    compact = compact_basketball_player_impact_readiness_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/basketball-player-impact", operation_id="runAutomationBasketballPlayerImpact")
async def automation_basketball_player_impact_endpoint(
    payload: AutomationBasketballPlayerImpactRequest,
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=20),
):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="basketball player-impact analysis only supports dry_run=true")
    cap = min(max(int(limit), 1), 100 if verbose else 20)
    result = automation_scheduler.run_automation_basketball_player_impact(
        candidate=payload.candidate,
        outcome_records=payload.outcome_records,
        red_team_provider=payload.red_team_provider,
    )
    compact = compact_basketball_player_impact_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/advanced-red-team-report", operation_id="getAutomationAdvancedRedTeamReport")
async def get_automation_advanced_red_team_report_endpoint(
    provider: Optional[str] = Query(default=None),
    persist_report: bool = Query(default=False),
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    payload = automation_scheduler.get_automation_advanced_red_team_report(
        provider=provider,
        persist_report=persist_report,
        max_items=cap,
    )
    compact = compact_advanced_red_team_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/extreme-randomness-report", operation_id="getAutomationExtremeRandomnessReport")
async def get_automation_extreme_randomness_report_endpoint(
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    payload = automation_scheduler.get_extreme_randomness_report()
    compact = compact_extreme_randomness_report_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/football-impact-readiness", operation_id="getAutomationFootballImpactReadiness")
async def get_automation_football_impact_readiness_endpoint(
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    payload = automation_scheduler.get_football_impact_readiness()
    compact = compact_football_impact_readiness_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/football-impact-diagnostics", operation_id="runAutomationFootballImpactDiagnostics")
async def automation_football_impact_diagnostics_endpoint(
    payload: AutomationFootballImpactDiagnosticsRequest,
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="football impact diagnostics only supports dry_run=true")
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    result = automation_scheduler.run_football_impact_diagnostics(
        sport=payload.sport,
        market_type=payload.market_type,
        team_context=payload.team_context,
        player_context=payload.player_context,
        play_drive_context=payload.play_drive_context,
        personnel_context=payload.personnel_context,
        matchup_context=payload.matchup_context,
        availability_context=payload.availability_context,
        incentive_context=payload.incentive_context,
        calibration_context=payload.calibration_context,
        tracking_context=payload.tracking_context,
        dry_run=True,
    )
    compact = compact_football_impact_diagnostics_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/soccer-impact-readiness", operation_id="getAutomationSoccerImpactReadiness")
async def get_automation_soccer_impact_readiness_endpoint(
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    payload = automation_scheduler.get_soccer_impact_readiness()
    compact = compact_soccer_impact_readiness_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/soccer-impact-diagnostics", operation_id="runAutomationSoccerImpactDiagnostics")
async def automation_soccer_impact_diagnostics_endpoint(
    payload: AutomationSoccerImpactDiagnosticsRequest,
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="soccer impact diagnostics only supports dry_run=true")
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    result = automation_scheduler.run_soccer_impact_diagnostics(
        sport=payload.sport,
        market_type=payload.market_type,
        game_context=payload.game_context,
        team_context=payload.team_context,
        player_context=payload.player_context,
        lineup_context=payload.lineup_context,
        tactical_context=payload.tactical_context,
        possession_value_context=payload.possession_value_context,
        shot_quality_context=payload.shot_quality_context,
        pressing_context=payload.pressing_context,
        transition_context=payload.transition_context,
        set_piece_context=payload.set_piece_context,
        goalkeeper_context=payload.goalkeeper_context,
        referee_context=payload.referee_context,
        matchup_context=payload.matchup_context,
        availability_context=payload.availability_context,
        incentive_context=payload.incentive_context,
        calibration_context=payload.calibration_context,
        tracking_context=payload.tracking_context,
        dry_run=True,
    )
    compact = compact_soccer_impact_diagnostics_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/hockey-impact-readiness", operation_id="getAutomationHockeyImpactReadiness")
async def get_automation_hockey_impact_readiness_endpoint(
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    payload = automation_scheduler.get_hockey_impact_readiness()
    compact = compact_hockey_impact_readiness_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/hockey-impact-diagnostics", operation_id="runAutomationHockeyImpactDiagnostics")
async def automation_hockey_impact_diagnostics_endpoint(
    payload: AutomationHockeyImpactDiagnosticsRequest,
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="hockey impact diagnostics only supports dry_run=true")
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    result = automation_scheduler.run_hockey_impact_diagnostics(
        sport=payload.sport,
        market_type=payload.market_type,
        game_context=payload.game_context,
        team_context=payload.team_context,
        skater_context=payload.skater_context,
        goalie_context=payload.goalie_context,
        line_context=payload.line_context,
        pair_context=payload.pair_context,
        special_teams_context=payload.special_teams_context,
        transition_context=payload.transition_context,
        shot_quality_context=payload.shot_quality_context,
        matchup_context=payload.matchup_context,
        availability_context=payload.availability_context,
        incentive_context=payload.incentive_context,
        calibration_context=payload.calibration_context,
        tracking_context=payload.tracking_context,
        dry_run=True,
    )
    compact = compact_hockey_impact_diagnostics_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/baseball-impact-readiness", operation_id="getAutomationBaseballImpactReadiness")
async def get_automation_baseball_impact_readiness_endpoint(
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=50),
):
    cap = min(max(int(limit), 1), 100 if verbose else 50)
    payload = automation_scheduler.get_baseball_impact_readiness()
    compact = compact_baseball_impact_readiness_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/baseball-impact-diagnostics", operation_id="runAutomationBaseballImpactDiagnostics")
async def automation_baseball_impact_diagnostics_endpoint(
    payload: AutomationBaseballImpactDiagnosticsRequest,
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="baseball impact diagnostics only supports dry_run=true")
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    result = automation_scheduler.run_baseball_impact_diagnostics(
        sport=payload.sport,
        market_type=payload.market_type,
        game_context=payload.game_context,
        team_context=payload.team_context,
        pitcher_context=payload.pitcher_context,
        batter_context=payload.batter_context,
        lineup_context=payload.lineup_context,
        bullpen_context=payload.bullpen_context,
        catcher_context=payload.catcher_context,
        defense_context=payload.defense_context,
        baserunning_context=payload.baserunning_context,
        park_weather_context=payload.park_weather_context,
        umpire_context=payload.umpire_context,
        availability_context=payload.availability_context,
        incentive_context=payload.incentive_context,
        calibration_context=payload.calibration_context,
        tracking_context=payload.tracking_context,
        dry_run=True,
    )
    compact = compact_baseball_impact_diagnostics_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/golf-impact-readiness", operation_id="getAutomationGolfImpactReadiness")
async def get_automation_golf_impact_readiness_endpoint(
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=50),
):
    cap = min(max(int(limit), 1), 100 if verbose else 50)
    payload = automation_scheduler.get_golf_impact_readiness()
    compact = compact_golf_impact_readiness_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/golf-impact-diagnostics", operation_id="runAutomationGolfImpactDiagnostics")
async def automation_golf_impact_diagnostics_endpoint(
    payload: AutomationGolfImpactDiagnosticsRequest,
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="golf impact diagnostics only supports dry_run=true")
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    result = automation_scheduler.run_golf_impact_diagnostics(
        sport=payload.sport,
        market_type=payload.market_type,
        tournament_context=payload.tournament_context,
        player_context=payload.player_context,
        strokes_gained_context=payload.strokes_gained_context,
        off_tee_context=payload.off_tee_context,
        approach_context=payload.approach_context,
        around_green_context=payload.around_green_context,
        putting_context=payload.putting_context,
        course_context=payload.course_context,
        weather_context=payload.weather_context,
        wave_context=payload.wave_context,
        field_context=payload.field_context,
        form_context=payload.form_context,
        availability_context=payload.availability_context,
        incentive_context=payload.incentive_context,
        calibration_context=payload.calibration_context,
        simulation_context=payload.simulation_context,
        tracking_context=payload.tracking_context,
        dry_run=True,
    )
    compact = compact_golf_impact_diagnostics_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/combat-impact-readiness", operation_id="getAutomationCombatImpactReadiness")
async def get_automation_combat_impact_readiness_endpoint(
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=50),
):
    cap = min(max(int(limit), 1), 100 if verbose else 50)
    payload = automation_scheduler.get_combat_impact_readiness()
    compact = compact_combat_impact_readiness_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/combat-impact-diagnostics", operation_id="runAutomationCombatImpactDiagnostics")
async def automation_combat_impact_diagnostics_endpoint(
    payload: AutomationCombatImpactDiagnosticsRequest,
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="combat impact diagnostics only supports dry_run=true")
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    result = automation_scheduler.run_combat_impact_diagnostics(
        sport=payload.sport,
        market_type=payload.market_type,
        bout_context=payload.bout_context,
        fighter_a_context=payload.fighter_a_context,
        fighter_b_context=payload.fighter_b_context,
        striking_context=payload.striking_context,
        grappling_context=payload.grappling_context,
        phase_context=payload.phase_context,
        damage_context=payload.damage_context,
        pace_cardio_context=payload.pace_cardio_context,
        matchup_context=payload.matchup_context,
        ruleset_context=payload.ruleset_context,
        judging_referee_context=payload.judging_referee_context,
        availability_context=payload.availability_context,
        incentive_context=payload.incentive_context,
        calibration_context=payload.calibration_context,
        film_tracking_context=payload.film_tracking_context,
        dry_run=True,
    )
    compact = compact_combat_impact_diagnostics_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/tennis-impact-readiness", operation_id="getAutomationTennisImpactReadiness")
async def get_automation_tennis_impact_readiness_endpoint(
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=50),
):
    cap = min(max(int(limit), 1), 100 if verbose else 50)
    payload = automation_scheduler.get_tennis_impact_readiness()
    compact = compact_tennis_impact_readiness_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/tennis-impact-diagnostics", operation_id="runAutomationTennisImpactDiagnostics")
async def automation_tennis_impact_diagnostics_endpoint(
    payload: AutomationTennisImpactDiagnosticsRequest,
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="tennis impact diagnostics only supports dry_run=true")
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    result = automation_scheduler.run_tennis_impact_diagnostics(
        sport=payload.sport,
        market_type=payload.market_type,
        match_context=payload.match_context,
        player_a_context=payload.player_a_context,
        player_b_context=payload.player_b_context,
        serve_context=payload.serve_context,
        return_context=payload.return_context,
        surface_context=payload.surface_context,
        format_context=payload.format_context,
        pressure_context=payload.pressure_context,
        tiebreak_context=payload.tiebreak_context,
        matchup_context=payload.matchup_context,
        conditions_context=payload.conditions_context,
        availability_context=payload.availability_context,
        incentive_context=payload.incentive_context,
        calibration_context=payload.calibration_context,
        point_context=payload.point_context,
        tracking_context=payload.tracking_context,
        dry_run=True,
    )
    compact = compact_tennis_impact_diagnostics_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/extreme-signal-diagnostics", operation_id="runAutomationExtremeSignalDiagnostics")
async def automation_extreme_signal_diagnostics_endpoint(
    payload: AutomationExtremeSignalDiagnosticsRequest,
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="extreme signal diagnostics only supports dry_run=true")
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    result = automation_scheduler.run_extreme_randomness_diagnostics(
        candidate=payload.candidate,
        baseline_values=payload.baseline_values or None,
        matrix_payload=payload.matrix_payload or None,
    )
    compact = compact_extreme_randomness_diagnostics_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/advanced-shape-diagnostics", operation_id="runAutomationAdvancedShapeDiagnostics")
async def automation_advanced_shape_diagnostics_endpoint(
    payload: AutomationAdvancedShapeDiagnosticsRequest,
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="advanced shape diagnostics only supports dry_run=true")
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    result = automation_scheduler.run_automation_advanced_shape_diagnostics(
        candidate=payload.candidate,
        historical_records=payload.historical_records,
        labeled_records=payload.labeled_records,
        calibration_records=payload.calibration_records,
        sequences=payload.sequences,
        provider=payload.provider,
        persist=payload.persist,
    )
    compact = compact_advanced_red_team_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/review-queue", operation_id="getAutomationSchedulerReviewQueue")
async def get_automation_scheduler_review_queue(
    provider: str = Query(default="all"),
    market_type: str = Query(default="all"),
    reason: Optional[str] = Query(default=None),
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    queue = automation_scheduler.get_scheduler_review_queue(
        provider=provider,
        market_type=market_type,
        reason=reason,
        limit=min(max(int(limit), 1), 100 if verbose else 10),
    )
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_review_queue_response(queue, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(queue, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/calibration", operation_id="getAutomationCalibration")
async def get_automation_calibration_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = automation_scheduler.get_automation_calibration_report()
    compact = compact_calibration_response(payload)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/outcomes/ingest", operation_id="ingestAutomationOutcomes")
async def ingest_automation_outcomes_endpoint(payload: AutomationOutcomeIngestRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    result = automation_scheduler.ingest_automation_outcomes(
        payload.records,
        source=payload.source,
        dry_run=payload.dry_run,
        persist=payload.persist,
    )
    compact = compact_outcome_ingest_response(result)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/outcomes/import-local-settlements", operation_id="importLocalKalshiSettlements")
async def import_local_kalshi_settlements_endpoint(
    payload: AutomationOutcomeLocalSettlementImportRequest,
    x_collector_token: Optional[str] = Header(default=None, alias="X-Collector-Token"),
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    if payload.persist and not payload.dry_run:
        from automation_scheduler.collector_scheduled_runner import validate_cron_token

        ok, status_code, rejection = validate_cron_token(x_collector_token)
        if not ok:
            raise HTTPException(status_code=status_code, detail=compact_outcome_import_response(rejection or {}))
    result = automation_scheduler.import_local_settlement_outcomes(
        payload.records,
        supporting_paper_decisions=payload.supporting_paper_decisions,
        source=payload.source,
        migration_version=payload.migration_version,
        dry_run=payload.dry_run,
        persist=payload.persist,
    )
    compact = compact_outcome_import_response(result)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/outcomes", operation_id="getAutomationOutcomes")
async def get_automation_outcomes_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    payload = automation_scheduler.get_automation_outcomes(limit=cap)
    compact = compact_outcomes_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/outcomes/discover-settlements", operation_id="discoverAutomationOutcomeSettlements")
async def discover_automation_outcome_settlements_endpoint(payload: AutomationSettlementDiscoveryRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="settlement discovery only supports dry_run=true")
    result = automation_scheduler.discover_automation_outcome_completions(
        pending_rows=payload.pending_rows or None,
        imported_rows=payload.imported_rows or None,
        use_kalshi_snapshot=payload.use_kalshi_snapshot,
        write_local_report=payload.write_local_report,
    )
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_settlement_discovery_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/calibration-collector/run", operation_id="runAutomationCalibrationCollector")
async def run_automation_calibration_collector_endpoint(payload: AutomationCalibrationCollectorRunRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    result = automation_scheduler.run_automation_calibration_collector(
        dry_run=payload.dry_run,
        persist_outcomes=payload.persist_outcomes,
        max_new_contracts=payload.max_new_contracts,
        target_daily_new_contracts=payload.target_daily_new_contracts,
        hard_cap_daily_new_contracts=payload.hard_cap_daily_new_contracts,
        max_markets_scanned=payload.max_markets_scanned,
        include_short_term=payload.include_short_term,
        include_medium_term=payload.include_medium_term,
        include_long_term=payload.include_long_term,
        adaptive_throttle=payload.adaptive_throttle,
        deepseek_review=payload.deepseek_review,
    )
    if not bool(result.get("ok", True)) and result.get("status") == "invalid_request":
        raise HTTPException(status_code=400, detail=compact_calibration_collector_response(result, limit=limit))
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_calibration_collector_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/calibration-collector/scheduled-run", operation_id="runScheduledAutomationCalibrationCollector")
async def run_automation_calibration_collector_scheduled_endpoint(
    payload: AutomationCalibrationCollectorScheduledRunRequest,
    x_collector_token: Optional[str] = Header(default=None, alias="X-Collector-Token"),
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    from automation_scheduler.collector_scheduled_runner import validate_cron_token

    ok, status_code, rejection = validate_cron_token(x_collector_token)
    if not ok:
        raise HTTPException(status_code=status_code, detail=compact_calibration_collector_response(rejection or {}, limit=limit))
    request_payload = payload.model_dump()
    result = automation_scheduler.run_automation_calibration_collector_scheduled(request_payload)
    if not bool(result.get("ok", True)) and result.get("status") == "invalid_request":
        raise HTTPException(status_code=400, detail=compact_calibration_collector_response(result, limit=limit))
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_calibration_collector_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/deepseek-review", operation_id="reviewAutomationWithDeepSeek")
async def automation_deepseek_review_endpoint(payload: AutomationDeepSeekReviewRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    result = automation_scheduler.run_automation_deepseek_review(
        collector_cycle_report=payload.collector_cycle_report,
        daily_report=payload.daily_report,
        calibration_report=payload.calibration_report,
        sampled_contracts=payload.sampled_contracts,
        candidate=payload.candidate or None,
        candidates=payload.candidates or None,
        core_model_action=payload.core_model_action,
        enabled=payload.enabled,
        review_queue_summary=payload.review_queue_summary,
        outcome_summary=payload.outcome_summary,
        provider_health_summary=payload.provider_health_summary,
        manifold_cluster_summary=payload.manifold_cluster_summary,
        markov_hmm_summary=payload.markov_hmm_summary,
        sportsbook_full_board_summary=payload.sportsbook_full_board_summary,
        stock_crypto_pattern_summary=payload.stock_crypto_pattern_summary,
        kalshi_prediction_market_summary=payload.kalshi_prediction_market_summary,
        small_account_summary=payload.small_account_summary,
        security_readiness_summary=payload.security_readiness_summary,
        strategy_readiness_summary=payload.strategy_readiness_summary,
        trap_no_bet_summary=payload.trap_no_bet_summary,
    )
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_deepseek_review_response(result)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/deepseek-red-team", operation_id="redTeamAutomationWithDeepSeek")
async def automation_deepseek_red_team_endpoint(payload: AutomationDeepSeekRedTeamRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    result = automation_scheduler.run_automation_deepseek_red_team(
        candidate=payload.candidate or None,
        candidates=payload.candidates or None,
        enabled=payload.enabled,
        review_queue_summary=payload.review_queue_summary,
        calibration_summary=payload.calibration_summary,
        outcome_summary=payload.outcome_summary,
        provider_health_summary=payload.provider_health_summary,
        manifold_cluster_summary=payload.manifold_cluster_summary,
        markov_hmm_summary=payload.markov_hmm_summary,
        sportsbook_full_board_summary=payload.sportsbook_full_board_summary,
        stock_crypto_pattern_summary=payload.stock_crypto_pattern_summary,
        kalshi_prediction_market_summary=payload.kalshi_prediction_market_summary,
        small_account_summary=payload.small_account_summary,
        security_readiness_summary=payload.security_readiness_summary,
        strategy_readiness_summary=payload.strategy_readiness_summary,
        trap_no_bet_summary=payload.trap_no_bet_summary,
    )
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_deepseek_review_response(result)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/deepseek-disagreements", operation_id="getDeepSeekDisagreements")
async def automation_deepseek_disagreements_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=100)):
    cap = min(max(int(limit), 1), 500 if verbose else 100)
    result = automation_scheduler.get_deepseek_disagreements(limit=cap)
    compact = compact_deepseek_review_response(result)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/deepseek-daily-report", operation_id="getDeepSeekDailyReport")
async def automation_deepseek_daily_report_endpoint(report_date: Optional[str] = Query(default=None), enabled: Optional[bool] = Query(default=None), persist_report: bool = Query(default=True), verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    result = automation_scheduler.get_deepseek_daily_report(
        report_date=report_date,
        enabled=enabled,
        persist_report=persist_report,
    )
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_deepseek_review_response(result)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/manifold-map", operation_id="mapAutomationManifoldState")
async def automation_manifold_map_endpoint(payload: AutomationManifoldMapRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    result = automation_scheduler.map_automation_manifold_item(
        payload.item,
        historical_records=payload.historical_records or None,
    )
    compact = compact_manifold_map_response(result)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/manifold-clusters", operation_id="getAutomationManifoldClusters")
async def automation_manifold_clusters_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=25)):
    cap = min(max(int(limit), 1), 100 if verbose else 25)
    result = automation_scheduler.get_automation_manifold_clusters(limit=cap)
    if verbose or include_debug:
        result["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return result


@app.get("/api/automation/manifold-calibration", operation_id="getAutomationManifoldCalibration")
async def automation_manifold_calibration_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=25)):
    cap = min(max(int(limit), 1), 100 if verbose else 25)
    result = automation_scheduler.get_automation_manifold_calibration(limit=cap)
    if verbose or include_debug:
        result["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return result


@app.get("/api/automation/manifold-no-bet-traps", operation_id="getAutomationManifoldNoBetTraps")
async def automation_manifold_no_bet_traps_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=25)):
    cap = min(max(int(limit), 1), 100 if verbose else 25)
    result = automation_scheduler.get_automation_manifold_no_bet_traps(limit=cap)
    if verbose or include_debug:
        result["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return result


@app.post("/api/automation/cross-asset-manifold-review", operation_id="reviewAutomationCrossAssetManifold")
async def automation_cross_asset_manifold_review_endpoint(payload: AutomationCrossAssetManifoldReviewRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="cross-asset manifold review only supports dry_run=true")
    result = automation_scheduler.run_automation_cross_asset_manifold_review(
        payload.items,
        historical_records=payload.historical_records or None,
        persist=bool(payload.persist),
        max_items=payload.max_items,
    )
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_manifold_review_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/pattern-detect", operation_id="detectSmallAccountPatterns")
async def detect_small_account_patterns_endpoint(payload: AutomationPatternDetectRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="pattern detection only supports dry_run=true")
    result = automation_scheduler.run_small_account_pattern_detection(payload.items)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_pattern_detection_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/small-account-review", operation_id="runSmallAccountReview")
async def run_small_account_review_endpoint(payload: AutomationSmallAccountReviewRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="small-account review only supports dry_run=true")
    result = automation_scheduler.run_small_account_review_cycle(
        payload.items,
        session_state=payload.session_state,
        persist_queue=payload.persist_queue,
    )
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_small_account_review_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/pattern-review-queue", operation_id="getSmallAccountPatternReviewQueue")
async def get_small_account_pattern_review_queue_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    payload = automation_scheduler.get_small_account_pattern_review_queue(limit=cap)
    compact = compact_pattern_review_queue_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/pattern-calibration", operation_id="getSmallAccountPatternCalibration")
async def get_small_account_pattern_calibration_endpoint(limit: int = Query(default=10)):
    cap = min(max(int(limit), 1), 100)
    payload = automation_scheduler.get_small_account_pattern_calibration()
    return compact_pattern_calibration_response(payload, limit=cap)


@app.get("/api/automation/micro-outcome-calibration", operation_id="getSmallAccountMicroOutcomeCalibration")
async def get_small_account_micro_outcome_calibration_endpoint(limit: int = Query(default=10)):
    cap = min(max(int(limit), 1), 100)
    payload = automation_scheduler.get_small_account_micro_outcome_calibration()
    return compact_micro_outcome_calibration_response(payload, limit=cap)


@app.get("/api/automation/broker-quality", operation_id="getSmallAccountBrokerQuality")
async def get_small_account_broker_quality_endpoint(limit: int = Query(default=10)):
    cap = min(max(int(limit), 1), 100)
    payload = automation_scheduler.get_broker_quality()
    return compact_broker_quality_response(payload, limit=cap)


@app.get("/api/automation/balance-sheet-risk/{symbol}", operation_id="getSmallAccountBalanceSheetRisk")
async def get_small_account_balance_sheet_risk_endpoint(symbol: str):
    payload = automation_scheduler.get_balance_sheet_risk(symbol)
    return compact_balance_sheet_risk_response(payload)


@app.get("/api/automation/data-sources/registry", operation_id="getAutomationDataSourceRegistry")
async def get_data_source_registry_endpoint(
    module: Optional[str] = Query(default=None),
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=100),
):
    payload = automation_scheduler.get_data_source_registry_snapshot(module=module)
    cap = min(max(int(limit), 1), 100)
    compact = compact_data_source_registry_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/data-sources/coverage", operation_id="getAutomationDataSourceCoverage")
async def get_data_source_coverage_endpoint(
    module: Optional[str] = Query(default=None),
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=100),
):
    payload = automation_scheduler.get_data_source_coverage_snapshot(module=module)
    cap = min(max(int(limit), 1), 100)
    compact = compact_data_source_coverage_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/data-sources/research-lanes", operation_id="getAutomationDataSourceResearchLanes")
async def get_data_source_research_lanes_endpoint(
    module: Optional[str] = Query(default=None),
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=100),
):
    payload = automation_scheduler.get_data_source_research_lanes_snapshot(module=module)
    cap = min(max(int(limit), 1), 100)
    compact = compact_data_source_research_lanes_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/data-sources/env-vars", operation_id="getAutomationDataSourceEnvVars")
async def get_data_source_env_vars_endpoint(
    module: Optional[str] = Query(default=None),
    limit: int = Query(default=500),
):
    payload = automation_scheduler.get_data_source_env_var_registry(module=module)
    cap = min(max(int(limit), 1), 500)
    return compact_data_source_env_vars_response(payload, limit=cap)


@app.get("/api/automation/data-sources/priorities", operation_id="getAutomationDataSourcePriorities")
async def get_data_source_priorities_endpoint(
    module: Optional[str] = Query(default=None),
    limit: int = Query(default=50),
):
    cap = min(max(int(limit), 1), 100)
    payload = automation_scheduler.get_data_source_priorities_snapshot(module=module, limit=cap)
    return compact_data_source_priorities_response(payload, limit=cap)


@app.get("/api/automation/data-sources/public-apis-expansion-report", operation_id="getPublicApisExpansionReport")
async def get_public_apis_expansion_report_endpoint(
    module: Optional[str] = Query(default=None),
    persist_report: bool = Query(default=False),
    limit: int = Query(default=100),
):
    cap = min(max(int(limit), 1), 100)
    payload = automation_scheduler.get_public_apis_expansion_report(module=module, persist_report=persist_report)
    return compact_public_apis_expansion_report_response(payload, limit=cap)


@app.get("/api/automation/data-sources/data-availability/tiers", operation_id="getAutomationDataAvailabilityTiers")
async def get_data_availability_tiers_endpoint(
    module: Optional[str] = Query(default=None),
    persist_report: bool = Query(default=False),
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=100),
):
    cap = min(max(int(limit), 1), 100)
    payload = automation_scheduler.get_data_availability_tiers_report(module=module, persist_report=persist_report)
    compact = compact_data_availability_tiers_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/data-sources/health", operation_id="getAutomationDataSourceHealth")
async def get_data_source_health_endpoint():
    payload = automation_scheduler.get_data_source_registry_health()
    return compact_data_source_health_response(payload)


@app.post(
    "/api/automation/data-sources/adapters/ncaaf/cfbd/verify",
    operation_id="verifyNcaafCfbdAdapter",
)
async def verify_ncaaf_cfbd_adapter_endpoint(
    payload: NcaafCfbdVerifyRequest,
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    result = automation_scheduler.verify_ncaaf_cfbd_adapter(
        dry_run=payload.dry_run,
        season=payload.season,
        week=payload.week,
        max_records=payload.max_records,
        fetch_live_sample=payload.fetch_live_sample,
        sample_profile=payload.sample_profile,
        max_provider_calls=payload.max_provider_calls,
        include_games=payload.include_games,
        include_team_stats=payload.include_team_stats,
        include_advanced_stats=payload.include_advanced_stats,
        include_rankings=payload.include_rankings,
        include_lines=payload.include_lines,
    )
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_cfbd_adapter_verification_response(result)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/data-sources/verify", operation_id="verifyAutomationDataSourceRegistry")
async def verify_data_source_registry_endpoint(payload: DataSourceVerifyRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=100)):
    result = automation_scheduler.verify_data_source_registry(module=payload.module, persist_report=payload.persist_report)
    cap = min(max(int(limit), 1), 100)
    compact = compact_data_source_registry_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/institutional-lab/health", operation_id="getInstitutionalLabHealth")
async def get_institutional_lab_health_endpoint():
    payload = automation_scheduler.get_institutional_lab_health()
    return compact_institutional_lab_health_response(payload)


@app.post("/api/automation/institutional-lab/run", operation_id="runInstitutionalLab")
async def run_institutional_lab_endpoint(payload: InstitutionalLabRunRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="institutional lab only supports dry_run=true")
    if payload.read_existing_outputs_only is not True:
        raise HTTPException(status_code=400, detail="institutional lab only supports read_existing_outputs_only=true")
    result = automation_scheduler.run_institutional_lab(
        dry_run=payload.dry_run,
        asset_classes=payload.asset_classes,
        read_existing_outputs_only=payload.read_existing_outputs_only,
        persist_lab_report=payload.persist_lab_report,
        persist_outcomes=payload.persist_outcomes,
        deepseek_review=payload.deepseek_review,
        execution_simulation=payload.execution_simulation,
    )
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_institutional_lab_run_response(result, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/institutional-lab/report", operation_id="getInstitutionalLabReport")
async def get_institutional_lab_report_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = automation_scheduler.get_institutional_lab_report()
    compact = compact_institutional_report_response(payload)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/institutional-lab/daily-report", operation_id="getInstitutionalLabDailyReport")
async def get_institutional_lab_daily_report_endpoint(report_date: Optional[str] = Query(default=None), verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = automation_scheduler.get_institutional_lab_daily_report(report_date=report_date)
    compact = compact_institutional_report_response(payload)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/institutional-lab/deepseek-review", operation_id="reviewInstitutionalLabWithDeepSeek")
async def institutional_lab_deepseek_review_endpoint(payload: InstitutionalDeepSeekReviewRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    result = automation_scheduler.run_institutional_deepseek_review(report=payload.report, enabled=payload.enabled)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_deepseek_review_response(result)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/institutional-lab/execution-desk/simulate", operation_id="simulateInstitutionalExecutionDesk")
async def institutional_execution_desk_simulate_endpoint(payload: InstitutionalExecutionSimulationRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    request_payload = payload.model_dump()
    try:
        result = automation_scheduler.simulate_institutional_execution(request_payload)
    except ValueError as exc:
        from automation_scheduler.institutional_execution_desk import rejection_response

        result = rejection_response(str(exc))
        raise HTTPException(status_code=400, detail=compact_institutional_execution_response(result)) from exc
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_institutional_execution_response(result)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/automation/institutional-lab/audit", operation_id="getInstitutionalLabAudit")
async def get_institutional_lab_audit_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    payload = automation_scheduler.get_institutional_lab_audit(limit=cap)
    compact = {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "total_count": int(payload.get("total_count", 0)),
        "count": int(payload.get("count", 0)),
        "items": list(payload.get("items", []))[:cap],
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "raw_payload_included": False,
    }
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/automation/run-once", operation_id="runAutomationSchedulerOnce")
async def run_automation_scheduler_once(payload: AutomationRunOnceRequest, verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="automation scheduler run-once only supports dry_run=true")
    try:
        result = automation_scheduler.run_scheduler_once(
            injected_data=payload.injected_data,
            dry_run=payload.dry_run,
            run_key=payload.run_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    compact = compact_run_once_response(result)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/governance/health", operation_id="getGovernanceHealth")
async def get_governance_health_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = {"ok": True, **get_governance_health()}
    compact = compact_health_response(payload)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/governance/inventory", operation_id="getGovernanceInventory")
async def get_governance_inventory_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = {"ok": True, "inventory": get_model_inventory()}
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_governance_inventory(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/governance/report", operation_id="getGovernanceReport")
async def get_governance_report_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = {"ok": True, **generate_governance_report()}
    compact = compact_governance_report(payload)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/governance/validate", operation_id="validateGovernanceDryRun")
async def validate_governance_endpoint(payload: dict[str, Any], verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    model_id = str(payload.get("model_id") or "unknown_model")
    activation_tier = str(payload.get("activation_tier") or "research_only")
    result = {
        "ok": True,
        "dry_run": True,
        "validation": build_model_validation_report(model_id=model_id, activation_tier=activation_tier),
    }
    compact = compact_validation_response(result)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.get("/api/performance/health", operation_id="getPerformanceHealth")
async def get_performance_health_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = {"ok": True, **automation_scheduler.get_performance_health()}
    compact = compact_performance_health(payload)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/performance/report", operation_id="getPerformanceReport")
async def get_performance_report_endpoint(
    model_id: str = Query(default="default_model"),
    historical_rows_path: Optional[str] = Query(default=None),
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    compact_payload = automation_scheduler.get_performance_report(
        model_id=model_id,
        historical_rows_path=historical_rows_path,
    )
    compact = compact_performance_report(compact_payload)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(compact_payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/performance/backtest", operation_id="runPerformanceBacktest")
async def run_performance_backtest_endpoint(
    payload: PerformanceBacktestRequest,
    verbose: bool = Query(default=False),
    include_debug: bool = Query(default=False),
    limit: int = Query(default=10),
):
    if payload.dry_run is not True:
        raise HTTPException(status_code=400, detail="performance backtest only supports dry_run=true")
    result = automation_scheduler.run_performance_backtest(
        model_id=payload.model_id,
        historical_rows_path=payload.historical_rows_path,
        rows=payload.rows,
    )
    compact = compact_performance_report(result["compact_report"])
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(result, limit=cap, verbose=verbose)
    return compact


@app.post("/api/performance/paper-summary", operation_id="runPerformancePaperSummary")
async def run_performance_paper_summary_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = automation_scheduler.get_paper_summary()
    compact = compact_performance_health({"ok": True, **automation_scheduler.get_performance_health()})
    compact["status"] = payload.get("status", "paper_tracking")
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/providers/health", operation_id="getProvidersHealth")
async def get_providers_health_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = automation_scheduler.get_provider_health()
    compact = compact_provider_health_response(payload)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/providers/registry", operation_id="getProvidersRegistry")
async def get_providers_registry_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = automation_scheduler.get_provider_registry_snapshot()
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    compact = compact_provider_registry_response(payload, limit=cap)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/providers/sharp/health", operation_id="getSharpProviderHealth")
async def get_sharp_provider_health_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = automation_scheduler.get_sharp_provider_health()
    compact = compact_provider_status(payload)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/providers/sharp/snapshot", operation_id="createSharpProviderSnapshot")
async def create_sharp_provider_snapshot_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = automation_scheduler.run_sharp_provider_snapshot()
    compact = compact_provider_status(payload)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.get("/api/providers/kalshi/health", operation_id="getKalshiProviderHealth")
async def get_kalshi_provider_health_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = automation_scheduler.get_kalshi_provider_health()
    compact = compact_provider_status(payload)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


@app.post("/api/providers/kalshi/snapshot", operation_id="createKalshiProviderSnapshot")
async def create_kalshi_provider_snapshot_endpoint(verbose: bool = Query(default=False), include_debug: bool = Query(default=False), limit: int = Query(default=10)):
    payload = automation_scheduler.run_kalshi_provider_snapshot()
    compact = compact_provider_status(payload)
    cap = min(max(int(limit), 1), 100 if verbose else 10)
    if verbose or include_debug:
        compact["debug"] = redact_and_limit_payload(payload, limit=cap, verbose=verbose)
    return compact


PUBLIC_OPENAPI_PATH_METHODS = frozenset({
    ("/", "get"),
    ("/health", "get"),
    ("/ping", "get"),
    ("/api/debug/auth-status", "get"),
    ("/api/automation/health", "get"),
    ("/api/automation/security-readiness", "get"),
    ("/api/automation/intelligence-readiness", "get"),
    ("/api/automation/strategy-readiness", "get"),
    ("/api/automation/basketball-player-impact-readiness", "get"),
    ("/api/automation/basketball-player-impact", "post"),
    ("/api/automation/football-impact-readiness", "get"),
    ("/api/automation/football-impact-diagnostics", "post"),
    ("/api/automation/soccer-impact-readiness", "get"),
    ("/api/automation/soccer-impact-diagnostics", "post"),
    ("/api/automation/hockey-impact-readiness", "get"),
    ("/api/automation/hockey-impact-diagnostics", "post"),
    ("/api/automation/baseball-impact-readiness", "get"),
    ("/api/automation/baseball-impact-diagnostics", "post"),
    ("/api/automation/golf-impact-readiness", "get"),
    ("/api/automation/golf-impact-diagnostics", "post"),
    ("/api/automation/combat-impact-readiness", "get"),
    ("/api/automation/combat-impact-diagnostics", "post"),
    ("/api/automation/tennis-impact-readiness", "get"),
    ("/api/automation/tennis-impact-diagnostics", "post"),
    ("/api/automation/advanced-red-team-report", "get"),
    ("/api/automation/extreme-randomness-report", "get"),
    ("/api/automation/extreme-signal-diagnostics", "post"),
    ("/api/automation/advanced-shape-diagnostics", "post"),
    ("/api/automation/review-queue", "get"),
    ("/api/automation/calibration", "get"),
    ("/api/automation/outcomes", "get"),
    ("/api/automation/outcomes/ingest", "post"),
    ("/api/automation/outcomes/import-local-settlements", "post"),
    ("/api/automation/outcomes/discover-settlements", "post"),
    ("/api/automation/calibration-collector/run", "post"),
    ("/api/automation/calibration-collector/scheduled-run", "post"),
    ("/api/automation/deepseek-review", "post"),
    ("/api/automation/deepseek-red-team", "post"),
    ("/api/automation/deepseek-disagreements", "get"),
    ("/api/automation/deepseek-daily-report", "get"),
    ("/api/automation/data-sources/registry", "get"),
    ("/api/automation/data-sources/coverage", "get"),
    ("/api/automation/data-sources/research-lanes", "get"),
    ("/api/automation/data-sources/env-vars", "get"),
    ("/api/automation/data-sources/priorities", "get"),
    ("/api/automation/data-sources/public-apis-expansion-report", "get"),
    ("/api/automation/data-sources/data-availability/tiers", "get"),
    ("/api/automation/data-sources/health", "get"),
    ("/api/automation/data-sources/adapters/ncaaf/cfbd/verify", "post"),
    ("/api/automation/data-sources/verify", "post"),
    ("/api/automation/institutional-lab/health", "get"),
    ("/api/automation/institutional-lab/run", "post"),
    ("/api/automation/institutional-lab/report", "get"),
    ("/api/automation/institutional-lab/daily-report", "get"),
    ("/api/automation/institutional-lab/deepseek-review", "post"),
    ("/api/automation/institutional-lab/execution-desk/simulate", "post"),
    ("/api/automation/institutional-lab/audit", "get"),
    ("/api/automation/run-once", "post"),
    ("/api/performance/health", "get"),
    ("/api/performance/report", "get"),
    ("/api/performance/backtest", "post"),
    ("/api/performance/paper-summary", "post"),
    ("/api/providers/health", "get"),
    ("/api/providers/registry", "get"),
    ("/api/providers/sharp/health", "get"),
    ("/api/providers/sharp/snapshot", "post"),
    ("/api/providers/kalshi/health", "get"),
    ("/api/providers/kalshi/snapshot", "post"),
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

import os
import json
import urllib.parse
import urllib.request
import urllib.error
from fastapi.responses import JSONResponse


@app.get("/odds/live")
def odds_live(limit: int = 10):
    api_key = os.getenv("SPORTSGAMEODDS_API_KEY")

    if not api_key:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "SPORTSGAMEODDS_API_KEY is missing"
            }
        )

    params = urllib.parse.urlencode({
        "oddsAvailable": "true",
        "limit": limit
    })

    url = f"https://api.sportsgameodds.com/v1/events/?{params}"

    try:
        request = urllib.request.Request(
            url,
            headers={
                "x-api-key": api_key,
                "Accept": "application/json",
                "User-Agent": "betting-stock-api/1.0"
            }
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

        return {
            "ok": True,
            "source": "SportsGameOdds",
            "endpoint": "/odds/live",
            "limit": limit,
            "data": data
        }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")

        return JSONResponse(
            status_code=e.code,
            content={
                "ok": False,
                "provider": "SportsGameOdds",
                "status_code": e.code,
                "error": error_body
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "provider": "SportsGameOdds",
                "error": str(e)
            }
        )


import os
import json
import urllib.parse
import urllib.request
import urllib.error
from fastapi.responses import JSONResponse


@app.get("/odds/the-odds-api/live")
def the_odds_api_live(
    sport: str = "basketball_nba",
    regions: str = "us",
    markets: str = "h2h,spreads,totals",
    odds_format: str = "american"
):
    api_key = os.getenv("THE_ODDS_API_KEY") or os.getenv("ODDS_API_KEY")

    if not api_key:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "THE_ODDS_API_KEY is missing"
            }
        )

    params = urllib.parse.urlencode({
        "apiKey": api_key,
        "regions": regions,
        "markets": markets,
        "oddsFormat": odds_format
    })

    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds?{params}"

    try:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "betting-stock-api/1.0"
            }
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

        return {
            "ok": True,
            "source": "The Odds API",
            "sport": sport,
            "regions": regions,
            "markets": markets,
            "odds_format": odds_format,
            "data": data
        }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")

        return JSONResponse(
            status_code=e.code,
            content={
                "ok": False,
                "provider": "The Odds API",
                "status_code": e.code,
                "error": error_body
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "provider": "The Odds API",
                "error": str(e)
            }
        )

@app.get("/odds/the-odds-api/test")
def the_odds_api_test():
    import os
    import json
    import urllib.request
    import urllib.error
    from fastapi.responses import JSONResponse

    api_key = os.getenv("THE_ODDS_API_KEY") or os.getenv("ODDS_API_KEY")

    if not api_key:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "THE_ODDS_API_KEY is missing"
            }
        )

    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={api_key}"

    try:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "betting-stock-api/1.0"
            }
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

            return {
                "ok": True,
                "source": "The Odds API",
                "requests_remaining": response.headers.get("x-requests-remaining"),
                "requests_used": response.headers.get("x-requests-used"),
                "sports_count": len(data),
                "sample": data[:5]
            }

    except urllib.error.HTTPError as e:
        return JSONResponse(
            status_code=e.code,
            content={
                "ok": False,
                "provider": "The Odds API",
                "status_code": e.code,
                "error": e.read().decode("utf-8")
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "provider": "The Odds API",
                "error": str(e)
            }
        )

# --- Math catalog endpoint: lists models/calculations/regression tools in repo ---
@app.get("/math/catalog")
def math_catalog(
    sport: str = "basketball_nba",
    include_all: bool = False,
    max_files: int = 120
):
    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parent

    exclude_dirs = {
        ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
        ".cursor", ".uv-cache-checks", ".uv-python-checks",
        "data", "reports"
    }

    priority_files = {
        "model_probability.py",
        "quant_engine.py",
        "market_pricing.py",
        "edge_engine.py",
        "bet_decision_engine.py",
        "risk_engine.py",
        "staking_engine.py",
        "full_board_engine.py",
        "multi_sport_model_registry.py",
        "model_blender.py",
        "odds_providers.py",
        "sharp_client.py",
        "kalshi_client.py",
        "logbook_engine.py",
        "bankroll_engine.py"
    }

    priority_dirs = {
        "math_models",
        "providers",
        "betting_providers",
        "live_market_intelligence",
        "research_engine",
        "model_governance"
    }

    sport_keywords = {
        "basketball_nba": [
            "nba", "basketball", "possession", "pace", "offensive_rating",
            "defensive_rating", "efg", "turnover", "rebound", "free_throw",
            "usage", "minutes", "shot_quality", "fatigue", "four factors"
        ],
        "basketball_wnba": [
            "wnba", "basketball", "possession", "pace", "usage", "minutes",
            "shot_quality", "fatigue", "four factors"
        ],
        "baseball_mlb": [
            "mlb", "baseball", "pitcher", "batter", "runs", "strikeout",
            "walk", "barrel", "hard_hit", "park", "weather", "poisson"
        ],
        "americanfootball_nfl": [
            "nfl", "football", "spread", "yards", "epa", "success_rate",
            "pace", "trench", "pressure", "rush", "pass"
        ],
        "icehockey_nhl": [
            "nhl", "hockey", "goalie", "shots", "xg", "power_play",
            "penalty_kill", "royal_road"
        ]
    }

    general_math_terms = [
        "regression", "linear", "logistic", "ridge", "lasso",
        "poisson", "bivariate", "monte_carlo", "simulation",
        "bayesian", "elo", "markov", "z_score", "standard_deviation",
        "correlation", "kelly", "staking", "edge", "ev", "expected_value",
        "implied_probability", "no_vig", "fair_probability",
        "closing_line", "clv", "risk", "variance"
    ]

    technique_patterns = {
        "Implied probability": ["implied_probability", "american_to_prob", "odds_to_prob"],
        "No-vig / fair probability": ["no_vig", "novig", "fair_probability", "remove_vig"],
        "Expected value / EV": ["expected_value", "ev", "edge"],
        "Kelly / staking": ["kelly", "stake", "staking"],
        "Risk management": ["risk", "bankroll", "exposure"],
        "Linear regression": ["linear_regression", "linear regression"],
        "Logistic regression": ["logistic_regression", "logistic regression"],
        "Ridge / Lasso regression": ["ridge", "lasso"],
        "Poisson model": ["poisson"],
        "Bivariate Poisson": ["bivariate"],
        "Monte Carlo simulation": ["monte_carlo", "simulation"],
        "Bayesian model": ["bayesian"],
        "Elo / rating model": ["elo", "rating"],
        "Markov model": ["markov"],
        "Correlation model": ["correlation"],
        "Possession model": ["possession"],
        "Pace model": ["pace"],
        "Four Factors": ["four factors", "efg", "turnover", "rebound", "free_throw"],
        "Shot quality": ["shot_quality", "shot quality"],
        "Fatigue / rest adjustment": ["fatigue", "rest", "travel"],
        "Injury / minutes adjustment": ["injury", "minutes", "usage"],
        "Market weakness detector": ["market_weakness", "weakness"],
        "CLV / closing line value": ["clv", "closing_line"]
    }

    def simple_signature(node):
        try:
            args = []
            all_args = list(getattr(node.args, "posonlyargs", [])) + list(node.args.args)
            for arg in all_args:
                args.append(arg.arg)
            if node.args.vararg:
                args.append("*" + node.args.vararg.arg)
            for arg in node.args.kwonlyargs:
                args.append(arg.arg)
            if node.args.kwarg:
                args.append("**" + node.args.kwarg.arg)
            return "(" + ", ".join(args) + ")"
        except Exception:
            return "()"

    def short_doc(node):
        doc = ast.get_docstring(node) or ""
        doc = " ".join(doc.split())
        return doc[:300]

    sport_key = sport.lower()
    keywords = sport_keywords.get(sport_key, []) + general_math_terms

    modules = []
    techniques_found = set()
    files_checked = 0

    for path in root.rglob("*.py"):
        rel = path.relative_to(root)
        rel_text = str(rel).replace("\\", "/")
        parts = set(rel.parts)

        if parts & exclude_dirs:
            continue

        if path.name == "main.py":
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        lower_text = text.lower()
        lower_rel = rel_text.lower()

        is_priority = (
            path.name in priority_files
            or any(lower_rel.startswith(d.lower() + "/") for d in priority_dirs)
        )

        sport_match = any(k.lower() in lower_text or k.lower() in lower_rel for k in keywords)

        if not include_all and not is_priority and not sport_match:
            continue

        try:
            tree = ast.parse(text)
        except Exception as e:
            modules.append({
                "module": rel_text,
                "parse_error": str(e),
                "functions": [],
                "classes": [],
                "techniques": []
            })
            continue

        module_techniques = []
        for label, patterns in technique_patterns.items():
            if any(p.lower() in lower_text for p in patterns):
                module_techniques.append(label)
                techniques_found.add(label)

        functions = []
        classes = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({
                    "name": node.name,
                    "signature": simple_signature(node),
                    "doc": short_doc(node)
                })

            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append({
                            "name": item.name,
                            "signature": simple_signature(item),
                            "doc": short_doc(item)
                        })

                classes.append({
                    "name": node.name,
                    "doc": short_doc(node),
                    "methods": methods[:30]
                })

        if functions or classes or module_techniques:
            modules.append({
                "module": rel_text,
                "techniques": module_techniques,
                "functions": functions[:40],
                "classes": classes[:20]
            })

        files_checked += 1

        if files_checked >= max_files:
            break

    return {
        "ok": True,
        "sport": sport,
        "mode": "repo_math_catalog",
        "message": "This lists math/model/regression code found in your repo. It does not execute bets.",
        "files_checked": files_checked,
        "modules_found": len(modules),
        "techniques_found": sorted(list(techniques_found)),
        "modules": modules
    }

# --- End math catalog endpoint ---


# --- Live opportunity scanner: arb, middles, line shopping, no-vig edge ---
@app.get("/odds/opportunities/live")
def odds_opportunities_live(
    sport: str = "basketball_nba",
    regions: str = "us",
    markets: str = "h2h,spreads,totals",
    odds_format: str = "american",
    limit: int = 30,
    arb_stake: float = 100.0,
    near_arb_max_hold_percent: float = 1.25,
    value_edge_min_percent: float = 0.25,
    middle_min_width: float = 0.5
):
    import json
    import os
    import urllib.error
    import urllib.parse
    import urllib.request
    from fastapi.responses import JSONResponse
    from src.core.opportunity_scanner import scan_opportunities

    api_key = os.getenv("THE_ODDS_API_KEY") or os.getenv("ODDS_API_KEY")
    if not api_key:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "Missing THE_ODDS_API_KEY or ODDS_API_KEY"},
        )

    params = urllib.parse.urlencode({
        "apiKey": api_key,
        "regions": regions,
        "markets": markets,
        "oddsFormat": odds_format,
    })
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds?{params}"

    try:
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "betting-stock-api/1.0"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            events = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return JSONResponse(
            status_code=e.code,
            content={
                "ok": False,
                "provider": "The Odds API",
                "status_code": e.code,
                "error": e.read().decode("utf-8"),
            },
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

    events = events[:limit]
    scan = scan_opportunities(
        events,
        stake=arb_stake,
        min_edge=value_edge_min_percent / 100.0,
        near_arb_max_hold_percent=near_arb_max_hold_percent,
        middle_min_width=middle_min_width,
    )
    return {
        "ok": True,
        "source": "The Odds API",
        "sport": sport,
        "regions": regions,
        "markets": markets,
        "events_checked": len(events),
        **scan,
    }

# --- End live opportunity scanner ---


LIVE_CARD_STATUSES = {
    "NO_MODEL",
    "MODEL_METADATA_MISMATCH",
    "INSUFFICIENT_HISTORY",
    "NO_BET",
    "WATCHLIST",
    "MODEL_VALUE",
    "CONFIRMED_BACKTESTED_EDGE",
}


def _sports_master_db_path() -> Path:
    return Path(os.getenv("SPORTS_MASTER_DB_PATH", "data/sports_master.db"))


def _predict_model_probabilities(model: Any, matrix: list[list[float]]) -> list[float]:
    raw = model.predict_proba(matrix)
    if isinstance(raw, list):
        return [float(value) for value in raw]
    return [float(value) for value in raw[:, 1]]


@app.get("/model/backtest")
def model_backtest(
    sport: str = "basketball_nba",
    market: str = "h2h",
    start_year: int = 2024,
    min_edge: float = 0.01,
    min_train_rows: int = 40,
):
    from src.core.backtester import run_walk_forward_backtest

    return run_walk_forward_backtest(
        db_path=_sports_master_db_path(),
        sport_key=sport,
        market=market,
        start_year=start_year,
        min_edge=min_edge,
        min_train_rows=min_train_rows,
    )


@app.get("/model/live-card")
def model_live_card(
    sport: str = "basketball_nba",
    market: str = "h2h",
    min_edge: float = 0.01,
    regions: str = "us",
    odds_format: str = "american",
    limit: int = 25,
):
    import json
    import os
    import urllib.error
    import urllib.parse
    import urllib.request
    from fastapi.responses import JSONResponse
    from src.core.backtester import load_model_bundle, load_model_metadata
    from src.core.math_utils import edge_percent, expected_value
    from src.sports.nba_features import build_live_features_matrix, get_feature_columns

    model_version = "v1"
    bundle = load_model_bundle(sport, model_version=model_version)
    metadata = load_model_metadata(sport, model_version=model_version)
    if bundle is None or metadata is None:
        return {
            "ok": True,
            "status": "NO_MODEL",
            "sport": sport,
            "market": market,
            "message": "No local calibrated model artifact is available. Run /model/backtest first.",
        }

    expected_columns = get_feature_columns()
    mismatch_reasons = []
    if bundle.get("sport_key") != sport or metadata.get("sport_key") != sport:
        mismatch_reasons.append("sport_key")
    if bundle.get("market") != market or metadata.get("market") != market:
        mismatch_reasons.append("market")
    if list(bundle.get("feature_columns") or []) != expected_columns:
        mismatch_reasons.append("feature_columns")
    if mismatch_reasons:
        return {
            "ok": True,
            "status": "MODEL_METADATA_MISMATCH",
            "sport": sport,
            "market": market,
            "mismatch_reasons": mismatch_reasons,
        }

    if metadata.get("status") == "INSUFFICIENT_HISTORY" or int(metadata.get("training_rows") or 0) < 40:
        return {
            "ok": True,
            "status": "INSUFFICIENT_HISTORY",
            "sport": sport,
            "market": market,
            "training_rows": metadata.get("training_rows", 0),
            "message": "The model artifact exists but does not have enough historical training rows.",
        }

    api_key = os.getenv("THE_ODDS_API_KEY") or os.getenv("ODDS_API_KEY")
    if not api_key:
        return {
            "ok": True,
            "status": "NO_BET",
            "sport": sport,
            "market": market,
            "message": "Live odds provider is not configured.",
        }

    params = urllib.parse.urlencode({
        "apiKey": api_key,
        "regions": regions,
        "markets": market,
        "oddsFormat": odds_format,
    })
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds?{params}"
    try:
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "betting-stock-api/1.0"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            events = json.loads(response.read().decode("utf-8"))[:limit]
    except urllib.error.HTTPError as e:
        return JSONResponse(
            status_code=e.code,
            content={
                "ok": True,
                "status": "NO_BET",
                "provider": "The Odds API",
                "status_code": e.code,
                "error": e.read().decode("utf-8"),
            },
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": True, "status": "NO_BET", "error": str(e)})

    live_matrix = build_live_features_matrix(events)
    rows = live_matrix.get("rows") or []
    matrix = live_matrix.get("matrix") or []
    if not rows or not matrix:
        return {
            "ok": True,
            "status": "NO_BET",
            "sport": sport,
            "market": market,
            "events_checked": len(events),
            "cards": [],
            "message": "No live h2h rows were available for scoring.",
        }

    model = bundle["model"]
    calibrator = bundle.get("calibrator")
    model_probs = _predict_model_probabilities(model, matrix)
    calibrated_probs = calibrator.predict_proba(model_probs) if calibrator else model_probs

    qualified_bets = int(metadata.get("qualified_bets") or 0)
    historical_roi = float(metadata.get("roi") or 0.0)
    avg_clv = metadata.get("avg_clv_percent")
    avg_clv_value = float(avg_clv) if avg_clv is not None else None
    confirmation_ready = qualified_bets >= 500 and historical_roi > 0 and avg_clv_value is not None and avg_clv_value > 0

    cards = []
    for row, model_prob, calibrated_prob in zip(rows, model_probs, calibrated_probs):
        implied = float(row.get("implied_probability") or 0.5)
        edge = float(calibrated_prob) - implied
        ev = expected_value(row["price_american"], float(calibrated_prob), stake=100.0)
        if edge >= min_edge and ev > 0:
            status = "CONFIRMED_BACKTESTED_EDGE" if confirmation_ready else "MODEL_VALUE"
        elif edge > 0 or ev > 0:
            status = "WATCHLIST"
        else:
            status = "NO_BET"

        cards.append({
            "status": status,
            "event_id": row.get("event_id"),
            "event": row.get("event"),
            "market": market,
            "selection": row.get("selection"),
            "best_book": row.get("best_book"),
            "best_odds": row.get("price_american"),
            "model_probability": round(float(model_prob), 6),
            "calibrated_probability": round(float(calibrated_prob), 6),
            "implied_probability": round(implied, 6),
            "edge_percent": round(edge_percent(float(calibrated_prob), implied), 3),
            "ev_per_100": round(ev, 4),
            "confirmation_blockers": [] if status == "CONFIRMED_BACKTESTED_EDGE" else [
                "requires_500_qualified_historical_model_bets_positive_roi_positive_avg_clv_current_positive_ev"
            ],
        })

    status_rank = {
        "CONFIRMED_BACKTESTED_EDGE": 6,
        "MODEL_VALUE": 5,
        "WATCHLIST": 4,
        "NO_BET": 3,
        "INSUFFICIENT_HISTORY": 2,
        "MODEL_METADATA_MISMATCH": 1,
        "NO_MODEL": 0,
    }
    top_status = max((card["status"] for card in cards), key=lambda value: status_rank[value]) if cards else "NO_BET"
    if top_status not in LIVE_CARD_STATUSES:
        top_status = "NO_BET"

    return {
        "ok": True,
        "status": top_status,
        "sport": sport,
        "market": market,
        "events_checked": len(events),
        "cards": sorted(cards, key=lambda item: item["ev_per_100"], reverse=True)[:50],
        "model_metadata": {
            "model_version": model_version,
            "training_rows": metadata.get("training_rows"),
            "qualified_bets": qualified_bets,
            "roi": historical_roi,
            "avg_clv_percent": avg_clv_value,
        },
        "note": "Live-card output is model research unless the status is CONFIRMED_BACKTESTED_EDGE.",
    }
