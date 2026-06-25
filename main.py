import csv
import os
import secrets
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from betting_providers import aliases as betting_aliases
from src.providers.compat import PREDICTION_MARKET
from src.providers.provider_router import ProviderRouter
from src.api.model_card_service import ModelCardService
from src.api.system_routes import register_system_routes
from src.api.provider_status_routes import register_provider_status_routes
from src.api.debug_routes import register_debug_routes
from src.api.betting_metadata_routes import register_betting_metadata_routes
from src.api.market_metadata_routes import register_market_metadata_routes
from src.api.bet_csv_routes import register_bet_csv_routes
from src.api.stock_analysis_routes import register_stock_analysis_routes
from src.api.quant_routes import register_quant_routes
from src.api.governance_routes import register_governance_routes
from src.api.performance_routes import register_performance_routes
from src.api.market_utility_routes import register_market_utility_routes
from src.api.model_backtest_routes import register_model_backtest_routes
from src.api.betting_action_routes import register_betting_action_routes
from src.api.automation_core_routes import register_automation_core_routes
from src.api.automation_sport_impact_routes import register_automation_sport_impact_routes
from src.api.automation_review_outcomes_routes import register_automation_review_outcomes_routes
from src.api.automation_deepseek_routes import register_automation_deepseek_routes
from src.api.automation_manifold_routes import register_automation_manifold_routes
from src.api.automation_small_account_routes import register_automation_small_account_routes
from src.api.automation_data_source_routes import register_automation_data_source_routes
from src.api.automation_institutional_lab_routes import register_automation_institutional_lab_routes
from src.api.automation_run_once_routes import register_automation_run_once_routes
from src.api.schemas.bet_csv import BetLogRequest
from src.api.schemas.automation import (
    AutomationAdvancedShapeDiagnosticsRequest,
    AutomationBaseballImpactDiagnosticsRequest,
    AutomationBasketballPlayerImpactRequest,
    AutomationCalibrationCollectorRunRequest,
    AutomationCalibrationCollectorScheduledRunRequest,
    AutomationCombatImpactDiagnosticsRequest,
    AutomationCrossAssetManifoldReviewRequest,
    AutomationDeepSeekRedTeamRequest,
    AutomationDeepSeekReviewRequest,
    AutomationExtremeSignalDiagnosticsRequest,
    AutomationFootballImpactDiagnosticsRequest,
    AutomationGolfImpactDiagnosticsRequest,
    AutomationHockeyImpactDiagnosticsRequest,
    AutomationManifoldMapRequest,
    AutomationOutcomeIngestRequest,
    AutomationOutcomeLocalSettlementImportRequest,
    AutomationSettlementDiscoveryRequest,
    AutomationSoccerImpactDiagnosticsRequest,
    AutomationTennisImpactDiagnosticsRequest,
)
from src.api.schemas.quant import BetAnalysisRequest, MarketPricingRequest, StockAnalysisRequest
from src.api.schemas.performance import PerformanceBacktestRequest
from src.services.action_betting_service import ActionBettingService
from src.services.bet_csv_service import BETS_FILE, append_bet, summarize_bets
import src.services.automation_scheduler_facade as automation_scheduler
import bet_log
import bet_decision_engine
import market_pricing
import multi_sport_model_registry
import model_probability
import screenshot_intake
from src.services.automation_scheduler_facade import get_runtime_data_path, get_automation_data_dir
from src.services.automation_scheduler_facade import (
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
from model_governance import (
    build_model_validation_report,
    generate_governance_report,
    get_governance_health,
)
from model_governance.model_inventory import get_model_inventory
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
DEFAULT_BOOKMAKERS = os.getenv(
    "DEFAULT_BOOKMAKERS",
    "draftkings,fanduel,betmgm,caesars,espnbet,bet365",
)
DEFAULT_REGIONS = os.getenv("DEFAULT_REGIONS", "us")
DEFAULT_MARKETS = "h2h,spreads,totals"
DATA_DIR = get_automation_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)

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

PROVIDER_ROUTER = ProviderRouter()
MODEL_CARD_SERVICE = ModelCardService(PROVIDER_ROUTER)
ACTION_BETTING_SERVICE = ActionBettingService(
    PROVIDER_ROUTER,
    default_markets=DEFAULT_MARKETS,
    default_bookmakers=DEFAULT_BOOKMAKERS,
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

register_system_routes(app)
register_provider_status_routes(app)
register_debug_routes(
    app,
    require_action_key=require_action_key,
    get_configured_action_key=get_configured_action_key,
)
register_betting_metadata_routes(
    app,
    require_action_key=require_action_key,
    provider_router=PROVIDER_ROUTER,
)
register_market_metadata_routes(
    app,
    require_action_key=require_action_key,
    provider_router=PROVIDER_ROUTER,
)
register_bet_csv_routes(
    app,
    require_action_key=require_action_key,
)
register_stock_analysis_routes(
    app,
    require_action_key=require_action_key,
    provider_router=PROVIDER_ROUTER,
    stock_data_fn=stock_data,
    no_data_response_fn=no_data_response,
)
register_quant_routes(
    app,
    require_action_key=require_action_key,
    american_to_decimal_fn=american_to_decimal,
    american_to_implied_probability_fn=american_to_implied_probability,
    build_market_pricing_row_fn=build_market_pricing_row,
    capm_required_return_fn=capm_required_return,
    classify_bet_fn=classify_bet,
    classify_edge_fn=classify_edge,
    classify_stock_fn=classify_stock,
    expected_value_dollars_fn=expected_value_dollars,
    expected_value_per_unit_fn=expected_value_per_unit,
    exposure_check_fn=exposure_check,
    implied_probability_from_american_fn=implied_probability_from_american,
    kelly_fraction_fn=kelly_fraction,
    probability_to_fair_american_fn=probability_to_fair_american,
    stock_alpha_fn=stock_alpha,
    suggested_bet_size_fn=suggested_bet_size,
    suggested_stake_fn=suggested_stake,
)
register_governance_routes(
    app,
    build_model_validation_report_dep=build_model_validation_report,
    compact_governance_inventory_dep=compact_governance_inventory,
    compact_governance_report_dep=compact_governance_report,
    compact_health_response_dep=compact_health_response,
    compact_validation_response_dep=compact_validation_response,
    generate_governance_report_dep=generate_governance_report,
    get_governance_health_dep=get_governance_health,
    get_model_inventory_dep=get_model_inventory,
    redact_and_limit_payload_dep=redact_and_limit_payload,
)
register_performance_routes(
    app,
    API_BASE_URL_dep=API_BASE_URL,
    automation_scheduler_dep=automation_scheduler,
    compact_performance_health_dep=compact_performance_health,
    compact_performance_report_dep=compact_performance_report,
    redact_and_limit_payload_dep=redact_and_limit_payload,
)
register_market_utility_routes(
    app,
    provider_router=PROVIDER_ROUTER,
    model_card_service=MODEL_CARD_SERVICE,
    repo_root=Path(__file__).resolve().parent,
)
register_model_backtest_routes(app)
register_betting_action_routes(
    app,
    require_action_key=require_action_key,
    provider_router=PROVIDER_ROUTER,
    action_betting_service=ACTION_BETTING_SERVICE,
    bet_log_dep=bet_log,
    bet_decision_engine_dep=bet_decision_engine,
    market_pricing_dep=market_pricing,
    model_probability_dep=model_probability,
    multi_sport_model_registry_dep=multi_sport_model_registry,
    screenshot_intake_dep=screenshot_intake,
    default_markets=DEFAULT_MARKETS,
    default_bookmakers=DEFAULT_BOOKMAKERS,
    utc_now_fn=utc_now,
)
register_automation_core_routes(
    app,
    automation_scheduler_dep=automation_scheduler,
    compact_health_response_dep=compact_health_response,
    compact_intelligence_readiness_response_dep=compact_intelligence_readiness_response,
    compact_strategy_readiness_response_dep=compact_strategy_readiness_response,
    redact_and_limit_payload_dep=redact_and_limit_payload,
)
register_automation_sport_impact_routes(
    app,
    automation_scheduler_dep=automation_scheduler,
    compact_advanced_red_team_response_dep=compact_advanced_red_team_response,
    compact_baseball_impact_diagnostics_response_dep=compact_baseball_impact_diagnostics_response,
    compact_baseball_impact_readiness_response_dep=compact_baseball_impact_readiness_response,
    compact_basketball_player_impact_readiness_response_dep=compact_basketball_player_impact_readiness_response,
    compact_basketball_player_impact_response_dep=compact_basketball_player_impact_response,
    compact_combat_impact_diagnostics_response_dep=compact_combat_impact_diagnostics_response,
    compact_combat_impact_readiness_response_dep=compact_combat_impact_readiness_response,
    compact_extreme_randomness_diagnostics_response_dep=compact_extreme_randomness_diagnostics_response,
    compact_extreme_randomness_report_response_dep=compact_extreme_randomness_report_response,
    compact_football_impact_diagnostics_response_dep=compact_football_impact_diagnostics_response,
    compact_football_impact_readiness_response_dep=compact_football_impact_readiness_response,
    compact_golf_impact_diagnostics_response_dep=compact_golf_impact_diagnostics_response,
    compact_golf_impact_readiness_response_dep=compact_golf_impact_readiness_response,
    compact_hockey_impact_diagnostics_response_dep=compact_hockey_impact_diagnostics_response,
    compact_hockey_impact_readiness_response_dep=compact_hockey_impact_readiness_response,
    compact_soccer_impact_diagnostics_response_dep=compact_soccer_impact_diagnostics_response,
    compact_soccer_impact_readiness_response_dep=compact_soccer_impact_readiness_response,
    compact_tennis_impact_diagnostics_response_dep=compact_tennis_impact_diagnostics_response,
    compact_tennis_impact_readiness_response_dep=compact_tennis_impact_readiness_response,
    redact_and_limit_payload_dep=redact_and_limit_payload,
)
register_automation_review_outcomes_routes(
    app,
    automation_scheduler_dep=automation_scheduler,
    compact_calibration_collector_response_dep=compact_calibration_collector_response,
    compact_calibration_response_dep=compact_calibration_response,
    compact_outcome_import_response_dep=compact_outcome_import_response,
    compact_outcome_ingest_response_dep=compact_outcome_ingest_response,
    compact_outcomes_response_dep=compact_outcomes_response,
    compact_review_queue_response_dep=compact_review_queue_response,
    compact_settlement_discovery_response_dep=compact_settlement_discovery_response,
    redact_and_limit_payload_dep=redact_and_limit_payload,
)
register_automation_deepseek_routes(
    app,
    automation_scheduler_dep=automation_scheduler,
    compact_deepseek_review_response_dep=compact_deepseek_review_response,
    redact_and_limit_payload_dep=redact_and_limit_payload,
)
register_automation_manifold_routes(
    app,
    automation_scheduler_dep=automation_scheduler,
    compact_manifold_map_response_dep=compact_manifold_map_response,
    compact_manifold_review_response_dep=compact_manifold_review_response,
    redact_and_limit_payload_dep=redact_and_limit_payload,
)
register_automation_small_account_routes(
    app,
    automation_scheduler_dep=automation_scheduler,
    compact_balance_sheet_risk_response_dep=compact_balance_sheet_risk_response,
    compact_broker_quality_response_dep=compact_broker_quality_response,
    compact_micro_outcome_calibration_response_dep=compact_micro_outcome_calibration_response,
    compact_pattern_calibration_response_dep=compact_pattern_calibration_response,
    compact_pattern_detection_response_dep=compact_pattern_detection_response,
    compact_pattern_review_queue_response_dep=compact_pattern_review_queue_response,
    compact_small_account_review_response_dep=compact_small_account_review_response,
    redact_and_limit_payload_dep=redact_and_limit_payload,
)
register_automation_data_source_routes(
    app,
    automation_scheduler_dep=automation_scheduler,
    compact_cfbd_adapter_verification_response_dep=compact_cfbd_adapter_verification_response,
    compact_data_availability_tiers_response_dep=compact_data_availability_tiers_response,
    compact_data_source_coverage_response_dep=compact_data_source_coverage_response,
    compact_data_source_env_vars_response_dep=compact_data_source_env_vars_response,
    compact_data_source_health_response_dep=compact_data_source_health_response,
    compact_data_source_priorities_response_dep=compact_data_source_priorities_response,
    compact_data_source_registry_response_dep=compact_data_source_registry_response,
    compact_data_source_research_lanes_response_dep=compact_data_source_research_lanes_response,
    compact_public_apis_expansion_report_response_dep=compact_public_apis_expansion_report_response,
    redact_and_limit_payload_dep=redact_and_limit_payload,
)
register_automation_institutional_lab_routes(
    app,
    automation_scheduler_dep=automation_scheduler,
    compact_deepseek_review_response_dep=compact_deepseek_review_response,
    compact_institutional_execution_response_dep=compact_institutional_execution_response,
    compact_institutional_lab_health_response_dep=compact_institutional_lab_health_response,
    compact_institutional_lab_run_response_dep=compact_institutional_lab_run_response,
    compact_institutional_report_response_dep=compact_institutional_report_response,
    redact_and_limit_payload_dep=redact_and_limit_payload,
)
register_automation_run_once_routes(
    app,
    automation_scheduler_dep=automation_scheduler,
    compact_run_once_response_dep=compact_run_once_response,
    redact_and_limit_payload_dep=redact_and_limit_payload,
)
