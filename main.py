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
from fastapi.routing import APIRoute

from betting_providers import aliases as betting_aliases
from betting_providers.base import PREDICTION_MARKET
from betting_providers.provider_router import ProviderRouter
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
    AutomationPatternDetectRequest,
    AutomationRunOnceRequest,
    AutomationSettlementDiscoveryRequest,
    AutomationSmallAccountReviewRequest,
    AutomationSoccerImpactDiagnosticsRequest,
    AutomationTennisImpactDiagnosticsRequest,
    DataSourceVerifyRequest,
    InstitutionalDeepSeekReviewRequest,
    InstitutionalExecutionSimulationRequest,
    InstitutionalLabRunRequest,
    NcaafCfbdVerifyRequest,
)
from src.api.schemas.quant import BetAnalysisRequest, MarketPricingRequest, StockAnalysisRequest
from src.api.schemas.performance import PerformanceBacktestRequest
from src.services.action_betting_service import ActionBettingService
from src.services.bet_csv_service import BETS_FILE, append_bet, summarize_bets
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
    APIRoute_dep=APIRoute,
    API_BASE_URL_dep=API_BASE_URL,
    Optional_dep=Optional,
    automation_scheduler_dep=automation_scheduler,
    compact_performance_health_dep=compact_performance_health,
    compact_performance_report_dep=compact_performance_report,
    get_openapi_dep=get_openapi,
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
    Optional_dep=Optional,
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
