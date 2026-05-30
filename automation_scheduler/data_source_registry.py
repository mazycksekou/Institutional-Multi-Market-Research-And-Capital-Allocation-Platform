from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .scheduler_config import sanitize_filename
from .source_quality_scoring import FUTURE_ONLY_ACCESS_TYPES, score_lane, score_source


ACCESS_TYPES = {
    "open_public",
    "free_key",
    "free_tier",
    "open_dataset",
    "public_wrapper_with_terms_review",
    "manual_import",
    "paid_candidate",
    "partner_candidate",
    "institutional_vendor_candidate",
    "broker_data_candidate",
    "sportsbook_account_candidate",
    "internal_proprietary_candidate",
    "unknown",
}

MANDATORY_LANES: tuple[dict[str, str], ...] = (
    {"lane_id": "prediction_markets", "module": "prediction_markets", "sport_or_asset": "Prediction Markets", "category": "prediction_market"},
    {"lane_id": "kalshi", "module": "kalshi", "sport_or_asset": "Kalshi", "category": "prediction_market"},
    {"lane_id": "polymarket", "module": "polymarket", "sport_or_asset": "Polymarket", "category": "prediction_market"},
    {"lane_id": "stocks", "module": "stocks", "sport_or_asset": "Stocks", "category": "financial_market"},
    {"lane_id": "ETFs", "module": "ETFs", "sport_or_asset": "ETFs", "category": "financial_market"},
    {"lane_id": "bonds", "module": "bonds", "sport_or_asset": "Bonds", "category": "financial_market"},
    {"lane_id": "rates", "module": "rates", "sport_or_asset": "Rates", "category": "financial_market"},
    {"lane_id": "macro", "module": "macro", "sport_or_asset": "Macro", "category": "financial_market"},
    {"lane_id": "major_assets", "module": "major_assets", "sport_or_asset": "Major Assets", "category": "financial_market"},
    {"lane_id": "sportsbooks", "module": "sportsbooks", "sport_or_asset": "Sportsbooks", "category": "odds"},
    {"lane_id": "odds", "module": "odds", "sport_or_asset": "Odds", "category": "odds"},
    {"lane_id": "weather", "module": "weather", "sport_or_asset": "Weather", "category": "environment"},
    {"lane_id": "officials", "module": "officials", "sport_or_asset": "Officials", "category": "context"},
    {"lane_id": "injuries", "module": "injuries", "sport_or_asset": "Injuries", "category": "context"},
    {"lane_id": "lineups", "module": "lineups", "sport_or_asset": "Lineups", "category": "context"},
    {"lane_id": "schedules", "module": "schedules", "sport_or_asset": "Schedules", "category": "context"},
    {"lane_id": "news_context", "module": "news_context", "sport_or_asset": "News/Event Context", "category": "context"},
    {"lane_id": "basketball_nba", "module": "basketball_nba", "sport_or_asset": "NBA", "category": "sport"},
    {"lane_id": "basketball_wnba", "module": "basketball_wnba", "sport_or_asset": "WNBA", "category": "sport"},
    {"lane_id": "americanfootball_nfl", "module": "americanfootball_nfl", "sport_or_asset": "NFL", "category": "sport"},
    {"lane_id": "americanfootball_ncaaf", "module": "americanfootball_ncaaf", "sport_or_asset": "NCAAF", "category": "sport"},
    {"lane_id": "baseball_mlb", "module": "baseball_mlb", "sport_or_asset": "MLB", "category": "sport"},
    {"lane_id": "icehockey_nhl", "module": "icehockey_nhl", "sport_or_asset": "NHL", "category": "sport"},
    {"lane_id": "soccer", "module": "soccer", "sport_or_asset": "Soccer", "category": "sport"},
    {"lane_id": "tennis", "module": "tennis", "sport_or_asset": "Tennis", "category": "sport"},
    {"lane_id": "ufc_mma", "module": "ufc_mma", "sport_or_asset": "UFC/MMA", "category": "sport"},
    {"lane_id": "boxing", "module": "boxing", "sport_or_asset": "Boxing", "category": "sport"},
    {"lane_id": "golf", "module": "golf", "sport_or_asset": "Golf", "category": "sport"},
    {"lane_id": "basketball_ncaab", "module": "basketball_ncaab", "sport_or_asset": "NCAAB", "category": "sport"},
    {"lane_id": "basketball_ncaaw", "module": "basketball_ncaaw", "sport_or_asset": "NCAAW", "category": "sport"},
)

MODULE_ALIASES = {
    "nba": "basketball_nba",
    "wnba": "basketball_wnba",
    "nfl": "americanfootball_nfl",
    "ncaaf": "americanfootball_ncaaf",
    "mlb": "baseball_mlb",
    "nhl": "icehockey_nhl",
    "mma": "ufc_mma",
    "ufc": "ufc_mma",
    "ncaab": "basketball_ncaab",
    "ncaaw": "basketball_ncaaw",
    "etfs": "ETFs",
    "etf": "ETFs",
    "prediction_market": "prediction_markets",
    "prediction_markets": "prediction_markets",
}

SPORT_REQUIRED_INPUTS = [
    "schedule",
    "team_stats",
    "player_stats",
    "final_results",
    "stable_event_id",
]

ODDS_REQUIRED_INPUTS = [
    "event_id",
    "market_type",
    "selection",
    "odds",
    "line",
    "timestamp",
    "final_results",
]

FINANCIAL_REQUIRED_INPUTS = [
    "symbol",
    "price",
    "timestamp",
    "volume",
    "historical_prices",
    "final_price",
]

PREDICTION_REQUIRED_INPUTS = [
    "ticker",
    "market_status",
    "close_time",
    "bid_ask",
    "settlement_result",
]

CONTEXT_REQUIRED_INPUTS = ["event_id", "timestamp", "source_context", "stable_join_key"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _required_inputs_for(category: str, lane_id: str) -> list[str]:
    if category == "sport":
        return list(SPORT_REQUIRED_INPUTS)
    if category == "odds":
        return list(ODDS_REQUIRED_INPUTS)
    if category == "financial_market":
        return list(FINANCIAL_REQUIRED_INPUTS)
    if category == "prediction_market":
        return list(PREDICTION_REQUIRED_INPUTS)
    if lane_id == "weather":
        return ["event_id", "location", "timestamp", "temperature", "wind", "precipitation"]
    return list(CONTEXT_REQUIRED_INPUTS)


def _optional_inputs_for(category: str, lane_id: str) -> list[str]:
    if category == "sport":
        return ["injuries", "lineups", "officials", "weather", "travel", "rest", "news_context"]
    if category == "financial_market":
        return ["fundamentals", "macro", "rates", "sector", "benchmarks", "corporate_actions"]
    if category == "prediction_market":
        return ["volume", "open_interest", "settlement_rules", "category", "event_metadata"]
    if category == "odds":
        return ["book_count", "consensus_line", "closing_line", "limits", "injuries", "weather"]
    return ["manual_notes", "confidence", "source_timestamp"]


def _default_coverage(**overrides: bool) -> dict[str, bool]:
    coverage = {
        "historical": False,
        "live": False,
        "schedules": False,
        "box_scores": False,
        "play_by_play": False,
        "player_stats": False,
        "team_stats": False,
        "injuries": False,
        "lineups": False,
        "officials": False,
        "odds": False,
        "weather": False,
        "fundamentals": False,
        "macro": False,
        "rates": False,
        "settlements": False,
        "final_results": False,
    }
    for key, value in overrides.items():
        if key in coverage:
            coverage[key] = bool(value)
    return coverage


def _source(
    *,
    source_id: str,
    source_name: str,
    lane_id: str,
    module: str | None = None,
    source_access_type: str = "unknown",
    current_phase_allowed: bool = False,
    future_source_candidate: bool = False,
    requires_account: bool = False,
    requires_api_key: bool = False,
    requires_terms_review: bool = True,
    requires_paid_subscription: bool = False,
    requires_execution_account: bool = False,
    requires_brokerage_account: bool = False,
    requires_sportsbook_account: bool = False,
    trial_only: bool = False,
    credit_card_required: bool = False,
    approval_status: str | None = None,
    adapter_status: str = "planned",
    coverage: dict[str, bool] | None = None,
    cadence: str = "unknown",
    backfill_depth: str = "",
    rate_limit_known: bool = False,
    rate_limit_notes: str = "",
    license_name: str = "unknown",
    terms_url_known: bool = False,
    commercial_use_unclear: bool = True,
    model_inputs_supported: list[str] | None = None,
    missing_model_inputs: list[str] | None = None,
    join_keys: list[str] | None = None,
    outcome_fields_available: list[str] | None = None,
    historical_backfill_fields_available: list[str] | None = None,
    notes: list[str] | None = None,
    verified_at: str | None = None,
) -> dict[str, Any]:
    if source_access_type not in ACCESS_TYPES:
        source_access_type = "unknown"
    future_only = source_access_type in FUTURE_ONLY_ACCESS_TYPES or bool(future_source_candidate)
    requires_budget_approval = bool(future_only or requires_paid_subscription)
    if approval_status is None:
        if future_only:
            approval_status = "future_candidate"
        elif requires_terms_review:
            approval_status = "needs_terms_review"
        elif current_phase_allowed:
            approval_status = "approved_for_research"
        else:
            approval_status = "candidate"
    source = {
        "source_id": source_id,
        "source_name": source_name,
        "lane_id": lane_id,
        "module": module or lane_id,
        "source_access_type": source_access_type,
        "current_phase_allowed": bool(current_phase_allowed and not future_only and not requires_paid_subscription and not requires_execution_account and not requires_brokerage_account and not requires_sportsbook_account and not trial_only and not credit_card_required),
        "future_source_candidate": bool(future_only),
        "requires_budget_approval": requires_budget_approval,
        "requires_account": bool(requires_account),
        "requires_api_key": bool(requires_api_key),
        "requires_terms_review": bool(requires_terms_review),
        "requires_provider_write": False,
        "requires_execution_account": bool(requires_execution_account),
        "requires_brokerage_account": bool(requires_brokerage_account),
        "requires_sportsbook_account": bool(requires_sportsbook_account),
        "requires_paid_subscription": bool(requires_paid_subscription or future_only),
        "trial_only": bool(trial_only),
        "credit_card_required": bool(credit_card_required),
        "approval_status": approval_status,
        "enabled": False,
        "adapter_status": adapter_status if adapter_status in {"not_started", "planned", "implemented", "verified", "disabled"} else "planned",
        "coverage": dict(coverage or _default_coverage()),
        "freshness": {
            "expected_update_cadence": cadence,
            "latency_notes": "",
            "backfill_depth": backfill_depth,
        },
        "limits": {
            "rate_limit_known": bool(rate_limit_known),
            "rate_limit_notes": rate_limit_notes,
            "daily_limit": None,
            "monthly_limit": None,
            "throttle_required": True,
            "cache_required": True,
        },
        "legal_terms": {
            "license": license_name,
            "terms_url_known": bool(terms_url_known),
            "terms_caution": bool(requires_terms_review or commercial_use_unclear),
            "commercial_use_unclear": bool(commercial_use_unclear),
            "requires_manual_review": bool(requires_terms_review),
        },
        "model_mapping": {
            "supported_model_modules": [module or lane_id],
            "model_inputs_supported": list(model_inputs_supported or []),
            "missing_model_inputs": list(missing_model_inputs or []),
            "join_keys": list(join_keys or []),
            "outcome_fields_available": list(outcome_fields_available or []),
            "historical_backfill_fields_available": list(historical_backfill_fields_available or []),
        },
        "quality": {
            "source_reliability_score": None,
            "freshness_score": None,
            "coverage_score": None,
            "completeness_score": None,
            "join_quality_score": None,
            "model_input_fill_rate": None,
            "terms_risk_score": None,
            "rate_limit_risk_score": None,
            "historical_depth_score": None,
            "outcome_availability_score": None,
        },
        "notes": list(notes or []),
        "verified_at": verified_at,
        "verified_by": "codex",
    }
    source["quality"] = score_source(source)
    return source


def _seed_sources() -> dict[str, list[dict[str, Any]]]:
    c: dict[str, list[dict[str, Any]]] = {lane["lane_id"]: [] for lane in MANDATORY_LANES}
    add = lambda lane, **kwargs: c[lane].append(_source(lane_id=lane, module=_module_for_lane(lane), **kwargs))

    add("prediction_markets", source_id="manual_prediction_market_import", source_name="Manual prediction-market result imports", source_access_type="manual_import", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, settlements=True, final_results=True), cadence="daily", model_inputs_supported=["ticker", "settlement_result"], join_keys=["ticker"], outcome_fields_available=["result", "status"], historical_backfill_fields_available=["settled_at", "result"])
    add("kalshi", source_id="kalshi_public_market_data", source_name="Kalshi public market data", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, adapter_status="implemented", coverage=_default_coverage(live=True, historical=True, settlements=True, final_results=True), cadence="near_live", model_inputs_supported=["ticker", "market_status", "close_time", "bid_ask", "settlement_result"], join_keys=["ticker", "market_ticker", "event_ticker"], outcome_fields_available=["result", "status"], historical_backfill_fields_available=["close_time", "settled_at", "result"], notes=["Read-only market and settlement use only; no order path."])
    add("polymarket", source_id="polymarket_gamma_api", source_name="Polymarket Gamma API", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(live=True, historical=True, settlements=True, final_results=True), cadence="near_live", model_inputs_supported=["ticker", "market_status", "close_time", "bid_ask"], join_keys=["condition_id", "market_slug"], outcome_fields_available=["outcome"], historical_backfill_fields_available=["close_time", "outcome"])
    add("polymarket", source_id="polymarket_data_api", source_name="Polymarket Data API", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, settlements=True), cadence="near_live", model_inputs_supported=["ticker", "market_status", "close_time"], join_keys=["condition_id", "market_slug"], outcome_fields_available=["outcome"])

    for lane in ("stocks", "ETFs"):
        add(lane, source_id=f"{lane.lower()}_yfinance", source_name="yfinance", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, fundamentals=lane == "stocks", final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "timestamp", "volume", "historical_prices", "final_price"], join_keys=["symbol"], outcome_fields_available=["final_price"], historical_backfill_fields_available=["date", "close", "volume"])
        add(lane, source_id=f"{lane.lower()}_stooq", source_name="Stooq", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "historical_prices", "final_price"], join_keys=["symbol"], outcome_fields_available=["close"], historical_backfill_fields_available=["date", "close"])
        add(lane, source_id=f"{lane.lower()}_alpha_vantage", source_name="Alpha Vantage free-tier candidate", source_access_type="free_tier", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "timestamp", "volume", "historical_prices", "final_price"], join_keys=["symbol"], outcome_fields_available=["adjusted_close"])
    add("stocks", source_id="sec_edgar_companyfacts", source_name="SEC EDGAR companyfacts", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, fundamentals=True), cadence="daily", model_inputs_supported=["symbol", "fundamentals"], join_keys=["cik", "ticker"], historical_backfill_fields_available=["facts", "period_end"])
    add("stocks", source_id="sec_edgar_submissions", source_name="SEC EDGAR submissions", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, fundamentals=True), cadence="daily", model_inputs_supported=["symbol", "fundamentals"], join_keys=["cik", "ticker"], historical_backfill_fields_available=["filing_date", "form"])
    add("stocks", source_id="nasdaq_data_link_future", source_name="Nasdaq Data Link future candidate", source_access_type="paid_candidate", future_source_candidate=True, coverage=_default_coverage(historical=True, fundamentals=True, macro=True), model_inputs_supported=["symbol", "historical_prices", "fundamentals"], join_keys=["symbol"])
    add("stocks", source_id="finnhub_future", source_name="Finnhub future candidate", source_access_type="paid_candidate", future_source_candidate=True, coverage=_default_coverage(historical=True, live=True, fundamentals=True), model_inputs_supported=["symbol", "price", "fundamentals"], join_keys=["symbol"])

    for lane in ("bonds", "rates", "macro"):
        add(lane, source_id=f"{lane}_fred_api", source_name="FRED API", source_access_type="free_key", current_phase_allowed=True, requires_api_key=True, requires_terms_review=False, coverage=_default_coverage(historical=True, macro=True, rates=True), cadence="daily", model_inputs_supported=["symbol", "historical_prices", "macro", "rates"], join_keys=["series_id", "date"], historical_backfill_fields_available=["date", "value"])
        add(lane, source_id=f"{lane}_treasury_fiscal_data", source_name="U.S. Treasury Fiscal Data API", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, macro=True, rates=True), cadence="daily", model_inputs_supported=["symbol", "historical_prices", "macro", "rates"], join_keys=["series", "date"], historical_backfill_fields_available=["date", "value"])
        add(lane, source_id=f"{lane}_treasury_yield", source_name="Treasury yield data", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, rates=True, final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "historical_prices", "final_price", "rates"], join_keys=["maturity", "date"], outcome_fields_available=["yield"], historical_backfill_fields_available=["date", "yield"])
    for lane in ("major_assets", "rates"):
        add(lane, source_id=f"{lane}_stooq_rates_fx_indices", source_name="Stooq rates / FX / indices", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, macro=True, rates=True, final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "historical_prices", "final_price", "macro", "rates"], join_keys=["symbol", "date"], outcome_fields_available=["close"], historical_backfill_fields_available=["date", "close"])
    add("major_assets", source_id="major_assets_yfinance_proxies", source_name="yfinance ETFs / indices / FX proxies", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "timestamp", "historical_prices", "final_price"], join_keys=["symbol"], outcome_fields_available=["close"])
    add("major_assets", source_id="alpha_vantage_fx_commodities", source_name="Alpha Vantage FX / commodities candidate", source_access_type="free_tier", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, final_results=True), cadence="daily", model_inputs_supported=["symbol", "price", "historical_prices", "final_price"], join_keys=["symbol"])

    for lane in ("sportsbooks", "odds"):
        add(lane, source_id=f"{lane}_the_odds_api", source_name="The Odds API free-tier candidate", source_access_type="free_tier", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(live=True, odds=True), cadence="near_live", model_inputs_supported=["event_id", "market_type", "selection", "odds", "line", "timestamp"], join_keys=["event_id", "bookmaker_key"])
        add(lane, source_id=f"{lane}_sportsgameodds", source_name="SportsGameOdds free-tier candidate", source_access_type="free_tier", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(live=True, odds=True), cadence="near_live", model_inputs_supported=["event_id", "market_type", "selection", "odds", "line", "timestamp"], join_keys=["event_id"])
        add(lane, source_id=f"{lane}_odds_api_io", source_name="Odds-API.io free-tier candidate", source_access_type="free_tier", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(live=True, odds=True), cadence="near_live", model_inputs_supported=["event_id", "market_type", "selection", "odds", "line", "timestamp"], join_keys=["event_id"])
        add(lane, source_id=f"{lane}_sharp_adapter_existing", source_name="Existing Sharp sportsbook adapter source pending access confirmation", source_access_type="sportsbook_account_candidate", future_source_candidate=True, requires_account=True, requires_sportsbook_account=True, coverage=_default_coverage(live=True, odds=True), cadence="near_live", model_inputs_supported=["event_id", "market_type", "selection", "odds", "line", "timestamp"], join_keys=["event_id"], notes=["Not enabled by registry; requires future confirmation of account, terms, and no write path."])

    add("weather", source_id="open_meteo_forecast", source_name="Open-Meteo forecast", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(live=True, weather=True), cadence="near_live", model_inputs_supported=["event_id", "location", "timestamp", "temperature", "wind", "precipitation"], join_keys=["latitude", "longitude", "timestamp"])
    add("weather", source_id="open_meteo_historical", source_name="Open-Meteo historical weather", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, weather=True), cadence="daily", model_inputs_supported=["event_id", "location", "timestamp", "temperature", "wind", "precipitation"], join_keys=["latitude", "longitude", "date"], historical_backfill_fields_available=["temperature", "wind", "precipitation"])
    add("schedules", source_id="manual_schedule_import", source_name="Manual schedule import", source_access_type="manual_import", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, schedules=True), cadence="daily", model_inputs_supported=["event_id", "timestamp", "schedule"], join_keys=["event_id", "date"])

    add("basketball_nba", source_id="nba_api", source_name="nba_api", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, schedules=True, box_scores=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "player_stats", "final_results", "stable_event_id"], join_keys=["game_id"], outcome_fields_available=["final_score"], historical_backfill_fields_available=["game_id", "box_score"])
    add("basketball_nba", source_id="hoopr_nba", source_name="hoopR NBA", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"], historical_backfill_fields_available=["game_id", "box_score"])
    add("basketball_nba", source_id="espn_nba_public_wrapper", source_name="ESPN NBA public endpoints through wrapper", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, schedules=True, box_scores=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "final_results", "stable_event_id"], join_keys=["event_id"], outcome_fields_available=["final_score"])

    add("basketball_wnba", source_id="wehoop_wnba", source_name="wehoop WNBA", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("basketball_wnba", source_id="wnba_stats_wrapper", source_name="WNBA Stats through wrapper", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, historical=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True), cadence="near_live", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("basketball_wnba", source_id="espn_wnba_public_wrapper", source_name="ESPN WNBA through wrapper", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, schedules=True, box_scores=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "final_results", "stable_event_id"], join_keys=["event_id"], outcome_fields_available=["final_score"])

    add("americanfootball_nfl", source_id="nflverse", source_name="nflverse", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"], historical_backfill_fields_available=["game_id", "play_by_play"])
    add("americanfootball_nfl", source_id="nflfastr", source_name="nflfastR", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("americanfootball_nfl", source_id="nflreadr", source_name="nflreadr", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("americanfootball_nfl", source_id="espn_nfl_public_wrapper", source_name="ESPN public endpoints", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, schedules=True, box_scores=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "final_results", "stable_event_id"], join_keys=["event_id"], outcome_fields_available=["final_score"])

    add("americanfootball_ncaaf", source_id="collegefootballdata", source_name="CollegeFootballData free-key candidate", source_access_type="free_key", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, schedules=True, box_scores=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("americanfootball_ncaaf", source_id="sportsdataverse_cfb", source_name="SportsDataverse CFB packages", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, play_by_play=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("americanfootball_ncaaf", source_id="espn_cfb_public_wrapper", source_name="ESPN college football public endpoints", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, schedules=True, box_scores=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "final_results", "stable_event_id"], join_keys=["event_id"], outcome_fields_available=["final_score"])

    add("baseball_mlb", source_id="pybaseball", source_name="pybaseball", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_pk", "player_id"], outcome_fields_available=["final_score"])
    add("baseball_mlb", source_id="mlb_stats_api", source_name="MLB Stats API public endpoints candidate", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(live=True, historical=True, schedules=True, box_scores=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="near_live", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_pk"], outcome_fields_available=["final_score"])
    for src, name in (("baseball_savant_pybaseball", "Baseball Savant through pybaseball"), ("fangraphs_pybaseball", "FanGraphs through pybaseball"), ("baseball_reference_pybaseball", "Baseball Reference through pybaseball")):
        add("baseball_mlb", source_id=src, source_name=name, source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, player_stats=True, team_stats=True), cadence="daily", model_inputs_supported=["player_stats", "team_stats"], join_keys=["player_id", "date"], notes=["Terms caution; adapter disabled pending review."])

    add("icehockey_nhl", source_id="nhl_public_api", source_name="NHL public API references", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(live=True, historical=True, schedules=True, box_scores=True, play_by_play=True, player_stats=True, team_stats=True, final_results=True), cadence="near_live", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("icehockey_nhl", source_id="nhl_api_wrappers", source_name="NHL API wrappers if license/terms acceptable", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])

    add("soccer", source_id="football_data_org", source_name="football-data.org free-tier candidate", source_access_type="free_tier", current_phase_allowed=True, requires_account=True, requires_api_key=True, requires_terms_review=True, coverage=_default_coverage(live=True, historical=True, schedules=True, box_scores=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["match_id"], outcome_fields_available=["final_score"])
    add("soccer", source_id="openfootball", source_name="openfootball datasets", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, schedules=True, final_results=True), cadence="historical_only", model_inputs_supported=["schedule", "final_results", "stable_event_id"], join_keys=["date", "home_team", "away_team"], outcome_fields_available=["final_score"])
    add("soccer", source_id="worldfootballr", source_name="worldfootballR", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["match_id"], outcome_fields_available=["final_score"])
    for src, name in (("understat_wrapper", "Understat through wrapper"), ("fbref_wrapper", "FBref through wrapper"), ("fotmob_wrapper", "Fotmob through wrapper")):
        add("soccer", source_id=src, source_name=name, source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, live=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["match_id"], outcome_fields_available=["final_score"], notes=["Terms caution; adapter disabled pending review."])

    add("tennis", source_id="jeff_sackmann_atp", source_name="Jeff Sackmann ATP data", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, player_stats=True, final_results=True), cadence="historical_only", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["tourney_id", "match_num"], outcome_fields_available=["winner"], historical_backfill_fields_available=["match_date", "winner"])
    add("tennis", source_id="jeff_sackmann_wta", source_name="Jeff Sackmann WTA data", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=False, coverage=_default_coverage(historical=True, player_stats=True, final_results=True), cadence="historical_only", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["tourney_id", "match_num"], outcome_fields_available=["winner"], historical_backfill_fields_available=["match_date", "winner"])
    add("tennis", source_id="match_charting_project", source_name="Match Charting Project", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, play_by_play=True, player_stats=True, final_results=True), cadence="historical_only", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["match_id"], outcome_fields_available=["winner"])

    for src, name in (("ufcstats_scraper_candidate", "UFCStats scraper candidates"), ("scrape_ufc_stats", "scrape_ufc_stats candidate"), ("ufc_stats_crawler", "ufc-stats-crawler candidate"), ("ufcscraper", "UFCscraper candidate")):
        add("ufc_mma", source_id=src, source_name=name, source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, player_stats=True, final_results=True), cadence="daily", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["fight_id"], outcome_fields_available=["winner"], notes=["Adapter disabled pending manual terms review."])

    add("boxing", source_id="open_boxing_api_candidate", source_name="Open Boxing API candidate", source_access_type="unknown", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, player_stats=True, final_results=True), cadence="unknown", model_inputs_supported=["player_stats", "final_results"], join_keys=["fight_id"], outcome_fields_available=["winner"])
    add("boxing", source_id="boxing_historical_dataset_needed", source_name="Public historical boxing datasets if discovered", source_access_type="unknown", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, final_results=True), cadence="unknown", model_inputs_supported=["final_results"], join_keys=["fight_id"], outcome_fields_available=["winner"])
    add("boxing", source_id="boxing_future_vendor", source_name="Boxing future vendor candidate", source_access_type="institutional_vendor_candidate", future_source_candidate=True, coverage=_default_coverage(historical=True, live=True, player_stats=True, final_results=True), model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["fight_id"], outcome_fields_available=["winner"])

    add("golf", source_id="golfastr", source_name="golfastR", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, player_stats=True, final_results=True), cadence="daily", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["tournament_id", "player_id"], outcome_fields_available=["finish_position"])
    add("golf", source_id="opengolfapi", source_name="OpenGolfAPI", source_access_type="open_public", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(live=True, historical=True, player_stats=True, final_results=True), cadence="daily", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["tournament_id", "player_id"], outcome_fields_available=["finish_position"])
    add("golf", source_id="espn_golf_public_wrapper", source_name="ESPN golf through wrapper", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, player_stats=True, final_results=True), cadence="near_live", model_inputs_supported=["player_stats", "final_results", "stable_event_id"], join_keys=["event_id", "player_id"], outcome_fields_available=["finish_position"])
    add("golf", source_id="public_pga_owgr_dataset_candidate", source_name="Public PGA / OWGR datasets if license-safe", source_access_type="unknown", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(historical=True, player_stats=True), cadence="unknown", model_inputs_supported=["player_stats"], join_keys=["player_id"])
    add("golf", source_id="golf_strokes_gained_future_vendor", source_name="Golf future vendor candidate for strokes-gained depth", source_access_type="institutional_vendor_candidate", future_source_candidate=True, coverage=_default_coverage(historical=True, live=True, player_stats=True, final_results=True), model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["tournament_id", "player_id"], outcome_fields_available=["finish_position"])

    add("basketball_ncaab", source_id="hoopr_mens_college_basketball", source_name="hoopR men's college basketball", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("basketball_ncaab", source_id="sportsdataverse_mbb", source_name="SportsDataverse men's basketball sources", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("basketball_ncaab", source_id="espn_mbb_public_wrapper", source_name="ESPN MBB through wrapper", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, schedules=True, box_scores=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "final_results", "stable_event_id"], join_keys=["event_id"], outcome_fields_available=["final_score"])

    add("basketball_ncaaw", source_id="wehoop_womens_college_basketball", source_name="wehoop women's college basketball", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, player_stats=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("basketball_ncaaw", source_id="sportsdataverse_wbb", source_name="SportsDataverse women's basketball sources", source_access_type="open_dataset", current_phase_allowed=True, requires_terms_review=True, coverage=_default_coverage(historical=True, schedules=True, box_scores=True, team_stats=True, final_results=True), cadence="daily", model_inputs_supported=SPORT_REQUIRED_INPUTS, join_keys=["game_id"], outcome_fields_available=["final_score"])
    add("basketball_ncaaw", source_id="espn_wbb_public_wrapper", source_name="ESPN WBB through wrapper", source_access_type="public_wrapper_with_terms_review", current_phase_allowed=False, requires_terms_review=True, coverage=_default_coverage(live=True, schedules=True, box_scores=True, final_results=True), cadence="near_live", model_inputs_supported=["schedule", "team_stats", "final_results", "stable_event_id"], join_keys=["event_id"], outcome_fields_available=["final_score"])
    return c


def _module_for_lane(lane_id: str) -> str:
    for lane in MANDATORY_LANES:
        if lane["lane_id"] == lane_id:
            return lane["module"]
    return lane_id


def _lane_status(sources: list[dict[str, Any]], future_sources: list[dict[str, Any]], verified: list[dict[str, Any]]) -> str:
    if verified:
        return "verified_sources_available"
    if sources:
        return "candidate_sources_available"
    if future_sources:
        return "future_vendor_needed"
    return "needs_external_research"


def _lane_from_definition(defn: dict[str, str], sources: list[dict[str, Any]]) -> dict[str, Any]:
    current_sources = [s for s in sources if not bool(s.get("future_source_candidate", False))]
    future_sources = [s for s in sources if bool(s.get("future_source_candidate", False))]
    verified = [s for s in current_sources if s.get("verified_at") and s.get("approval_status") == "approved_for_research"]
    category = defn["category"]
    lane_id = defn["lane_id"]
    required = _required_inputs_for(category, lane_id)
    lane = {
        "lane_id": lane_id,
        "module": defn["module"],
        "sport_or_asset": defn["sport_or_asset"],
        "category": category,
        "lane_status": _lane_status(current_sources, future_sources, verified),
        "assigned_research_lane": True,
        "external_research_owner": None,
        "source_candidates": current_sources,
        "verified_sources": verified,
        "future_source_candidates": future_sources,
        "rejected_sources": [],
        "required_model_inputs": required,
        "optional_model_inputs": _optional_inputs_for(category, lane_id),
        "outcome_fields_required": ["final_result"] if category in {"sport", "odds"} else ["settlement_result"] if category == "prediction_market" else ["final_price"] if category == "financial_market" else [],
        "historical_backfill_fields_required": ["stable_id", "timestamp", "historical_value", "final_result"],
        "live_fields_desired": ["timestamp", "status", "current_value"],
        "context_fields_desired": _optional_inputs_for(category, lane_id),
        "adapter_status": "planned" if verified else "blocked_pending_source" if not current_sources else "planned",
        "coverage_score": 0,
        "freshness_score": 0,
        "outcome_availability_score": 0,
        "terms_risk_score": 0,
        "external_research_priority_score": 0,
        "notes_for_external_researcher": [
            "Keep provider writes disabled.",
            "Document stable join keys and final outcome fields before adapter work.",
            "Confirm terms and rate limits before enabling any adapter.",
        ],
    }
    scores = score_lane(lane)
    lane.update(scores)
    return lane


def build_registry(*, module: str | None = None) -> dict[str, Any]:
    seeded = _seed_sources()
    lanes = [_lane_from_definition(defn, seeded.get(defn["lane_id"], [])) for defn in MANDATORY_LANES]
    if module:
        needle = MODULE_ALIASES.get(str(module).strip().lower(), str(module).strip())
        lanes = [lane for lane in lanes if lane["module"] == needle or lane["lane_id"] == needle or lane["sport_or_asset"].lower() == needle.lower()]
    sources = [src for lane in lanes for src in lane["source_candidates"] + lane["future_source_candidates"] + lane["verified_sources"]]
    return {
        "ok": True,
        "status": "ok",
        "created_at": utc_now_iso(),
        "schema_version": "data_source_registry_v1",
        "module_filter": module,
        "total_lanes": len(lanes),
        "lanes": lanes,
        "sources": sources,
        "storage_health": get_storage_health(),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
    }


def summarize_registry(registry: dict[str, Any]) -> dict[str, Any]:
    lanes = list(registry.get("lanes") or [])
    sources = list(registry.get("sources") or [])
    modules_without_verified = [lane["module"] for lane in lanes if not lane.get("verified_sources")]
    return {
        "total_lanes": len(lanes),
        "lanes_with_verified_sources": sum(1 for lane in lanes if lane.get("verified_sources")),
        "lanes_with_candidate_sources": sum(1 for lane in lanes if lane.get("source_candidates")),
        "lanes_needing_external_research": sum(1 for lane in lanes if lane.get("lane_status") == "needs_external_research"),
        "lanes_blocked_pending_source": sum(1 for lane in lanes if lane.get("adapter_status") == "blocked_pending_source"),
        "lanes_future_vendor_needed": sum(1 for lane in lanes if lane.get("lane_status") == "future_vendor_needed"),
        "total_sources": len(sources),
        "current_phase_allowed_count": sum(1 for src in sources if src.get("current_phase_allowed")),
        "candidate_count": sum(1 for src in sources if src.get("approval_status") in {"candidate", "needs_terms_review"}),
        "needs_terms_review_count": sum(1 for src in sources if src.get("requires_terms_review") or src.get("approval_status") == "needs_terms_review"),
        "future_source_candidate_count": sum(1 for src in sources if src.get("future_source_candidate")),
        "rejected_count": sum(1 for src in sources if src.get("approval_status") == "rejected"),
        "modules_fully_covered": [lane["module"] for lane in lanes if lane.get("coverage_score", 0) >= 85 and lane.get("verified_sources")],
        "modules_partially_covered": [lane["module"] for lane in lanes if lane.get("source_candidates") and not lane.get("verified_sources")],
        "modules_without_verified_source": modules_without_verified,
        "top_missing_fields_by_module": _top_missing_fields(lanes),
        "safety_flags": _safety_flags(),
    }


def _top_missing_fields(lanes: list[dict[str, Any]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for lane in lanes:
        required = set(lane.get("required_model_inputs") or [])
        supported: set[str] = set()
        for src in lane.get("source_candidates") or []:
            supported.update((src.get("model_mapping") or {}).get("model_inputs_supported") or [])
        missing = sorted(required - supported)
        if missing:
            out[str(lane["module"])] = missing[:10]
    return out


def _safety_flags() -> dict[str, Any]:
    return {
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
    }


def build_registry_report(*, module: str | None = None) -> dict[str, Any]:
    from .data_source_research_lanes import build_research_tasks
    from .model_input_coverage import build_coverage_report

    registry = build_registry(module=module)
    coverage = build_coverage_report(registry=registry)
    research = build_research_tasks(registry["lanes"])
    summary = summarize_registry(registry)
    recommended = recommended_next_adapters(registry)
    return {
        **registry,
        **summary,
        "coverage": coverage,
        "research_lanes": research,
        "open_external_research_tasks": len(research.get("tasks", [])),
        "recommended_next_adapters": recommended,
    }


def recommended_next_adapters(registry: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lane in registry.get("lanes") or []:
        for src in lane.get("source_candidates") or []:
            q = src.get("quality") or {}
            rows.append(
                {
                    "lane_id": lane.get("lane_id"),
                    "module": lane.get("module"),
                    "source_id": src.get("source_id"),
                    "source_name": src.get("source_name"),
                    "current_phase_usability_score": int(q.get("current_phase_usability_score") or 0),
                    "coverage_score": int(q.get("coverage_score") or 0),
                    "historical_depth_score": int(q.get("historical_depth_score") or 0),
                    "outcome_availability_score": int(q.get("outcome_availability_score") or 0),
                    "model_input_fill_rate": int(q.get("model_input_fill_rate") or 0),
                    "terms_risk_score": int(q.get("terms_risk_score") or 0),
                    "adapter_status": src.get("adapter_status"),
                    "enabled": False,
                }
            )
    rows.sort(
        key=lambda row: (
            -row["current_phase_usability_score"],
            -row["coverage_score"],
            -row["historical_depth_score"],
            -row["outcome_availability_score"],
            -row["model_input_fill_rate"],
            row["terms_risk_score"],
            row["source_name"],
        )
    )
    return rows[: max(1, min(int(limit), 50))]


def _data_sources_root(base_data_dir: str | Path | None = None) -> Path:
    if base_data_dir is None:
        root = get_data_sources_dir()
    else:
        root = resolve_base_data_dir(base_data_dir) / "data_sources"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _rel(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def render_registry_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Data Source Registry Report",
        "",
        f"- created_at: {report.get('created_at')}",
        f"- total_lanes: {report.get('total_lanes')}",
        f"- total_sources: {report.get('total_sources')}",
        f"- current_phase_allowed_count: {report.get('current_phase_allowed_count')}",
        f"- needs_terms_review_count: {report.get('needs_terms_review_count')}",
        f"- future_source_candidate_count: {report.get('future_source_candidate_count')}",
        "- provider_write: false",
        "- execution_allowed: false",
        "- live_execution_enabled: false",
        "",
        "## Lanes",
    ]
    for lane in report.get("lanes") or []:
        lines.append(
            f"- {lane.get('lane_id')}: {lane.get('lane_status')}, candidates={len(lane.get('source_candidates') or [])}, future={len(lane.get('future_source_candidates') or [])}, coverage_score={lane.get('coverage_score')}"
        )
    return "\n".join(lines) + "\n"


def write_registry_artifacts(report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    root = _data_sources_root(base_data_dir)
    run_id = sanitize_filename(f"data_sources_{str(report.get('created_at') or utc_now_iso()).replace(':', '-')}")
    latest = root / "latest.json"
    item = root / "items" / f"{run_id}.json"
    report_md = root / "reports" / f"{run_id}.md"
    daily = root / "daily" / f"{utc_now_iso()[:10]}.json"
    research_latest = root / "research_lanes.latest.json"
    _atomic_write_json(latest, report)
    _atomic_write_json(item, report)
    _atomic_write_text(report_md, render_registry_markdown(report))
    _atomic_write_json(daily, report)
    _atomic_write_json(research_latest, report.get("research_lanes") or {})
    return {
        "latest_path": _rel(latest, base_data_dir),
        "item_path": _rel(item, base_data_dir),
        "report_path": _rel(report_md, base_data_dir),
        "daily_path": _rel(daily, base_data_dir),
        "research_lanes_latest_path": _rel(research_latest, base_data_dir),
    }


def verify_registry(*, module: str | None = None, persist_report: bool = True, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    report = build_registry_report(module=module)
    lanes = report.get("lanes") or []
    errors: list[str] = []
    lane_ids = {lane.get("lane_id") for lane in lanes}
    if module is None:
        for lane in MANDATORY_LANES:
            if lane["lane_id"] not in lane_ids:
                errors.append(f"missing_lane:{lane['lane_id']}")
    for src in report.get("sources") or []:
        if src.get("enabled") and not (src.get("approval_status") == "approved_for_research" and src.get("current_phase_allowed")):
            errors.append(f"unsafe_enabled_source:{src.get('source_id')}")
        if src.get("future_source_candidate") and src.get("enabled"):
            errors.append(f"future_source_enabled:{src.get('source_id')}")
        if src.get("requires_provider_write"):
            errors.append(f"provider_write_source:{src.get('source_id')}")
    report.update(
        {
            "status": "verified" if not errors else "verification_failed",
            "verification_errors": errors,
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "raw_payload_included": False,
        }
    )
    if persist_report:
        report.update(write_registry_artifacts(report, base_data_dir=base_data_dir))
    return report
