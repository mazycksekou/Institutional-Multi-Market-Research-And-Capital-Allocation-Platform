from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .derived_feature_planner import plan_derived_features
from .scheduler_config import sanitize_filename


DATA_AVAILABILITY_SCHEMA_VERSION = "data_availability_tiers_v1"

TIER_NAMES = {
    0: "TIER_0_OUTCOME_BACKFILL",
    1: "TIER_1_BASIC_FORM",
    2: "TIER_2_MARKET_AWARE",
    3: "TIER_3_ADVANCED_STATS",
    4: "TIER_4_CONTEXT",
}

GLOBAL_TIER_FIELDS = {
    0: ["schedule", "teams", "event_date", "home_away", "final_score", "final_result", "margin", "total"],
    1: ["rolling_wins_losses", "rolling_points_for", "rolling_points_against", "rolling_margin", "home_away_splits", "rest_days", "simple_opponent_strength", "simple_rating", "volatility", "sos_proxy"],
    2: ["odds", "spread", "total", "moneyline", "implied_probability", "prediction_market_price", "line_movement", "market_liquidity"],
    3: ["advanced_performance_metrics", "epa", "success_rate", "havoc", "xg", "run_value", "shot_quality", "serve_return", "strokes_gained", "striking_grappling", "onchain", "fundamentals"],
    4: ["injuries", "lineups", "weather", "officials", "travel", "news", "macro_context", "operational_security_context"],
}

BASE_CONFIDENCE_CAPS = {-1: 0.0, 0: 0.55, 1: 0.62, 2: 0.70, 3: 0.78, 4: 0.86}

RECOMMENDED_USE_BY_LEVEL = {
    -1: "blocked_until_tier_0_critical_fields_exist",
    0: "outcome_backfill_and_tier_0_calibration_only",
    1: "baseline_training_and_tier_1_calibration",
    2: "market_aware_review_and_tier_2_calibration",
    3: "advanced_stats_review_with_tier_3_calibration",
    4: "context_aware_review_with_tier_4_calibration",
}

FREE_NEXT_ACTION_BY_LEVEL = {
    -1: "no-call audit for schedule/results/outcome fields",
    0: "derive Tier 1 rolling form from existing schedule/results history",
    1: "no-call audit for existing market, odds, or prediction-market fields",
    2: "mocked adapter coverage or free/open advanced-stat verification",
    3: "no-call audit for existing context reports and mocked joins",
    4: "continue tier-separated calibration and backfill from existing data",
}

DEFAULT_DERIVED_FEATURES = [
    "final_margin",
    "total_points",
    "winner",
    "rolling_points_for",
    "rolling_points_against",
    "rolling_margin",
    "rolling_win_rate",
    "home_away_split",
    "rest_days",
    "simple_rating",
    "opponent_adjusted_margin",
    "volatility",
    "close_game_rate",
    "market_implied_probability",
    "prediction_market_outcome",
]


def _profile(
    *,
    module: str,
    display_name: str,
    tier0: list[str],
    tier1: list[str],
    tier2: list[str],
    tier3: list[str],
    tier4: list[str],
    critical: list[str] | None = None,
    derived: list[str] | None = None,
    never_fabricate: list[str] | None = None,
) -> dict[str, Any]:
    tiers = {0: tier0, 1: tier1, 2: tier2, 3: tier3, 4: tier4}
    return {
        "module": module,
        "display_name": display_name,
        "tiers": tiers,
        "critical_fields": list(critical or tier0),
        "confidence_cap_rules": {
            "missing_critical_tier_0_cap": 0.0,
            "tier_0_cap": BASE_CONFIDENCE_CAPS[0],
            "tier_1_cap": BASE_CONFIDENCE_CAPS[1],
            "tier_2_cap": BASE_CONFIDENCE_CAPS[2],
            "tier_3_cap": BASE_CONFIDENCE_CAPS[3],
            "tier_4_cap": BASE_CONFIDENCE_CAPS[4],
            "advanced_missing_cap": 0.70,
            "context_missing_cap": 0.78,
        },
        "calibration_buckets": {
            level: f"{module}.{TIER_NAMES[level].lower()}"
            for level in range(5)
        },
        "allowed_derived_features_from_free_data": list(derived or DEFAULT_DERIVED_FEATURES),
        "never_fabricate_fields": sorted(set(never_fabricate or []) | set(tier3) | set(tier4)),
    }


BASKETBALL_T0 = ["teams", "event_id", "event_date", "home_away", "final_score", "final_result"]
BASKETBALL_T1 = ["rolling_points_for", "rolling_points_against", "rolling_margin", "rolling_win_rate", "home_away_split", "rest_days", "simple_team_rating", "sos_proxy", "volatility"]
BASKETBALL_T2 = ["spread", "total", "moneyline", "implied_probability", "market_price", "line_movement", "market_liquidity"]
BASKETBALL_T3 = ["shot_quality", "possession_metrics", "pace", "rebound_rate", "turnover_rate", "player_efficiency", "advanced_team_rating"]
BASKETBALL_T4 = ["injuries", "lineups", "depth_chart", "officials", "travel", "rest_disadvantage", "news"]

FOOTBALL_T1 = ["rolling_points_for", "rolling_points_against", "rolling_margin", "rolling_win_rate", "rest_days", "simple_team_rating", "sos_proxy", "volatility"]
FOOTBALL_T2 = ["spread", "total", "moneyline", "implied_probability", "market_price", "line_movement", "market_liquidity"]
FOOTBALL_T3 = ["epa", "success_rate", "explosiveness", "havoc", "drive_metrics", "points_per_drive", "play_success_rate"]
FOOTBALL_T4 = ["qb_status", "injuries", "weather", "lineups", "depth_chart", "officials", "travel", "news"]

SPORT_PROFILES: dict[str, dict[str, Any]] = {
    "basketball_nba": _profile(module="basketball_nba", display_name="NBA", tier0=BASKETBALL_T0, tier1=BASKETBALL_T1, tier2=BASKETBALL_T2, tier3=BASKETBALL_T3, tier4=BASKETBALL_T4),
    "basketball_wnba": _profile(module="basketball_wnba", display_name="WNBA", tier0=BASKETBALL_T0, tier1=BASKETBALL_T1, tier2=BASKETBALL_T2, tier3=BASKETBALL_T3, tier4=BASKETBALL_T4),
    "basketball_ncaab": _profile(module="basketball_ncaab", display_name="NCAAB", tier0=BASKETBALL_T0, tier1=BASKETBALL_T1, tier2=BASKETBALL_T2, tier3=BASKETBALL_T3, tier4=BASKETBALL_T4),
    "basketball_ncaaw": _profile(module="basketball_ncaaw", display_name="NCAAW", tier0=BASKETBALL_T0, tier1=BASKETBALL_T1, tier2=BASKETBALL_T2, tier3=BASKETBALL_T3, tier4=BASKETBALL_T4),
    "americanfootball_nfl": _profile(module="americanfootball_nfl", display_name="NFL", tier0=["teams", "game_id", "season", "week", "home_away", "final_score", "final_result"], tier1=FOOTBALL_T1, tier2=FOOTBALL_T2, tier3=FOOTBALL_T3, tier4=FOOTBALL_T4),
    "americanfootball_ncaaf": _profile(module="americanfootball_ncaaf", display_name="NCAAF", tier0=["teams", "game_id", "season", "week", "home_away", "final_score", "final_result"], tier1=FOOTBALL_T1, tier2=FOOTBALL_T2, tier3=FOOTBALL_T3, tier4=FOOTBALL_T4, never_fabricate=["epa", "success_rate", "explosiveness", "havoc", "qb_status"]),
    "baseball_mlb": _profile(module="baseball_mlb", display_name="MLB", tier0=["teams", "game_id", "event_date", "starter", "final_score", "final_result"], tier1=["rolling_runs_for", "rolling_runs_against", "rolling_margin", "team_form", "bullpen_usage_proxy", "home_away_split", "park_factor", "rest_days"], tier2=["moneyline", "run_line", "total", "implied_probability", "market_price", "line_movement"], tier3=["pitch_values", "run_value", "xwoba", "barrel_rate", "advanced_pitcher_metrics", "advanced_batter_metrics"], tier4=["lineup_confirmation", "umpire", "weather", "injuries", "travel", "news"], critical=["teams", "game_id", "event_date", "final_score", "final_result"]),
    "icehockey_nhl": _profile(module="icehockey_nhl", display_name="NHL", tier0=["teams", "game_id", "event_date", "home_away", "final_score", "final_result"], tier1=["rolling_goals_for", "rolling_goals_against", "rolling_margin", "rolling_win_rate", "home_away_split", "rest_days", "simple_team_rating"], tier2=["moneyline", "puck_line", "total", "implied_probability", "market_price"], tier3=["xg", "xga", "shot_quality", "possession_metrics", "special_teams_metrics", "goalie_metrics"], tier4=["injuries", "goalie_confirmation", "lineups", "officials", "travel", "news"]),
    "soccer": _profile(module="soccer", display_name="Soccer", tier0=["teams", "match_id", "event_date", "home_away", "final_score", "final_result"], tier1=["rolling_goals_for", "rolling_goals_against", "form", "home_away_split", "rest_days", "simple_team_rating", "sos_proxy"], tier2=["three_way_odds", "asian_handicap", "total", "implied_probability", "market_price"], tier3=["xg", "xga", "shot_quality", "pressing_metrics", "possession_metrics"], tier4=["lineups", "injuries", "weather", "referee", "travel", "news"], critical=["teams", "match_id", "event_date", "final_score", "final_result"]),
    "tennis": _profile(module="tennis", display_name="Tennis", tier0=["players", "match_id", "event_date", "surface", "final_score", "final_result"], tier1=["rolling_sets_won", "rolling_games_won", "player_form", "surface_form", "rest_days", "simple_player_rating", "volatility"], tier2=["moneyline", "game_spread", "total_games", "implied_probability", "market_price"], tier3=["serve_metrics", "return_metrics", "hold_rate", "break_rate", "point_win_rate", "rally_metrics"], tier4=["injury_status", "travel", "draw_context", "weather", "news"], critical=["players", "match_id", "event_date", "final_result"]),
    "golf": _profile(module="golf", display_name="Golf", tier0=["players", "tournament_id", "event_date", "course", "finish_position", "final_result"], tier1=["recent_finishes", "scoring_average", "field_strength", "course_history", "simple_player_rating", "volatility"], tier2=["outright_odds", "placement_odds", "matchup_odds", "implied_probability", "market_price"], tier3=["strokes_gained", "approach_metrics", "putting_metrics", "driving_metrics", "around_green_metrics"], tier4=["weather", "tee_time", "injury_status", "travel", "news"], critical=["players", "tournament_id", "event_date", "finish_position"]),
    "combat_sports": _profile(module="combat_sports", display_name="Combat Sports", tier0=["fighters", "fight_id", "event_date", "weight_class", "final_result", "method"], tier1=["record", "recent_form", "finish_rate", "age", "reach", "layoff_days", "simple_fighter_rating"], tier2=["moneyline", "method_odds", "round_total", "implied_probability", "market_price"], tier3=["striking_metrics", "grappling_metrics", "takedown_metrics", "control_time", "pace_metrics"], tier4=["injury_status", "camp_context", "weigh_in", "travel", "news"], critical=["fighters", "fight_id", "event_date", "final_result"]),
    "prediction_market": _profile(module="prediction_market", display_name="Prediction Markets", tier0=["ticker", "market_id", "close_time", "settlement_result", "final_result"], tier1=["category_base_rate", "historical_market_price", "time_to_close", "volatility", "simple_market_rating"], tier2=["bid_ask", "market_price", "implied_probability", "volume", "open_interest", "market_liquidity"], tier3=["order_book_depth", "spread_quality", "liquidity_microstructure", "settlement_history"], tier4=["settlement_rules", "event_news", "market_context", "operational_context"], critical=["ticker", "settlement_result"]),
    "stock": _profile(module="stock", display_name="Stocks", tier0=["symbol", "date", "close_price", "return"], tier1=["rolling_return", "volatility", "drawdown", "volume", "trend"], tier2=["market_benchmark", "sector_benchmark", "rates_context", "macro_context"], tier3=["fundamentals", "filings", "earnings", "revisions", "valuation"], tier4=["news", "insider_context", "institutional_context", "macro_regime"], critical=["symbol", "date", "close_price"]),
    "crypto": _profile(module="crypto", display_name="Crypto", tier0=["symbol", "timestamp", "price", "return"], tier1=["rolling_return", "volatility", "volume", "drawdown", "trend"], tier2=["order_book", "spread", "liquidity", "funding", "open_interest"], tier3=["onchain", "dex_liquidity", "stablecoin_flows", "gas", "defi_context"], tier4=["news", "security_context", "regulatory_context", "macro_context"], critical=["symbol", "timestamp", "price"]),
    "sportsbook": _profile(module="sportsbook", display_name="Sportsbook", tier0=["event_id", "teams", "event_date", "market_type", "selection", "final_result"], tier1=["basic_form", "home_away_split", "rest_days", "simple_team_rating"], tier2=["odds", "line", "spread", "total", "moneyline", "implied_probability", "book_count"], tier3=["consensus_line", "closing_line", "line_movement", "limit_context", "market_liquidity"], tier4=["injuries", "weather", "lineups", "news"], critical=["event_id", "market_type", "selection"]),
    "context_module": _profile(module="context_module", display_name="Context Module", tier0=["timestamp", "source_context", "stable_join_key"], tier1=["coverage_history", "source_reliability", "cadence", "join_quality"], tier2=["entity_linkage", "market_linkage"], tier3=["normalized_context_metric"], tier4=["weather", "injury_status", "lineups", "officials", "news", "macro_context", "security_context", "travel"], critical=["timestamp"]),
}

MODULE_PROFILE_ALIASES = {
    "nba": "basketball_nba",
    "wnba": "basketball_wnba",
    "ncaab": "basketball_ncaab",
    "ncaaw": "basketball_ncaaw",
    "nfl": "americanfootball_nfl",
    "ncaaf": "americanfootball_ncaaf",
    "mlb": "baseball_mlb",
    "nhl": "icehockey_nhl",
    "ufc": "combat_sports",
    "mma": "combat_sports",
    "ufc_mma": "combat_sports",
    "boxing": "combat_sports",
    "prediction_markets": "prediction_market",
    "kalshi": "prediction_market",
    "polymarket": "prediction_market",
    "stocks": "stock",
    "ETFs": "stock",
    "institutional_stock_pro_analyst": "stock",
    "cryptocurrency_edge_lab": "crypto",
    "cryptocurrency": "crypto",
    "sportsbooks": "sportsbook",
    "odds": "sportsbook",
    "bonds": "stock",
    "rates": "stock",
    "macro": "stock",
    "major_assets": "stock",
    "fx_currencies": "stock",
    "weather": "context_module",
    "news_sentiment": "context_module",
    "government_open_data": "context_module",
    "transportation_logistics": "context_module",
    "health_public_context": "context_module",
    "security_ops": "context_module",
    "officials": "context_module",
    "injuries": "context_module",
    "lineups": "context_module",
    "schedules": "context_module",
    "news_context": "context_module",
}

FIELD_EXPANSIONS = {
    "schedule": {"schedule", "event_date", "event_time", "teams", "players", "fighters", "home_away", "season", "week"},
    "stable_event_id": {"stable_event_id", "event_id", "game_id", "match_id", "fight_id", "tournament_id", "market_id"},
    "final_results": {"final_results", "final_result", "result", "outcome", "final_score", "settlement_result", "finish_position"},
    "final_score": {"final_score", "final_result", "result", "points_for", "points_against"},
    "team_stats": {"team_stats", "teams", "basic_form"},
    "player_stats": {"player_stats", "players", "fighters", "participants"},
    "event_id": {"event_id", "stable_join_key"},
    "source": {"source", "source_context"},
    "source_id": {"source_id", "source_context"},
    "source_context": {"source_context"},
    "box_scores": {"box_scores", "final_score", "points_for", "points_against"},
    "historical_prices": {"historical_prices", "date", "close_price", "return", "rolling_return", "volatility", "drawdown", "trend"},
    "price": {"price", "close_price", "spot_price"},
    "asset_symbol": {"asset_symbol", "symbol"},
    "spot_price": {"spot_price", "price"},
    "timestamp": {"timestamp", "date", "event_date"},
    "date": {"date", "event_date"},
    "match_date": {"match_date", "event_date"},
    "final_price": {"final_price", "close_price", "return"},
    "close": {"close", "close_price", "return"},
    "settlement_result": {"settlement_result", "final_result", "outcome"},
    "bid_ask": {"bid_ask", "market_price", "implied_probability", "spread", "market_liquidity"},
    "odds": {"odds", "moneyline", "spread", "total", "implied_probability"},
    "line": {"line", "spread", "total"},
    "volume": {"volume", "market_liquidity"},
    "fundamentals": {"fundamentals", "valuation"},
    "sec_filings": {"sec_filings", "filings"},
    "ohlcv": {"ohlcv", "price", "volume", "return", "rolling_return", "volatility", "drawdown"},
    "exchange_volume": {"exchange_volume", "volume", "liquidity"},
    "order_book_depth": {"order_book_depth", "order_book", "liquidity", "spread"},
    "funding_rates": {"funding_rates", "funding"},
    "onchain_signals": {"onchain_signals", "onchain"},
    "dex_liquidity": {"dex_liquidity", "dex"},
    "macro": {"macro", "macro_context"},
    "rates": {"rates", "rates_context"},
}

COVERAGE_FIELD_EXPANSIONS = {
    "schedules": {"schedule", "event_date", "teams", "home_away"},
    "box_scores": {"final_score", "points_for", "points_against"},
    "final_results": {"final_result", "final_score", "settlement_result", "finish_position"},
    "settlements": {"settlement_result", "final_result"},
    "odds": {"odds", "moneyline", "spread", "total", "implied_probability"},
    "historical": {"date"},
    "live": {"timestamp"},
    "team_stats": {"team_stats", "teams"},
    "player_stats": {"player_stats", "players", "fighters"},
    "fundamentals": {"fundamentals", "valuation"},
    "filings": {"filings"},
    "earnings": {"earnings"},
    "macro": {"macro_context"},
    "rates": {"rates_context"},
    "order_book": {"order_book", "spread", "liquidity"},
    "funding": {"funding"},
    "open_interest": {"open_interest"},
    "onchain": {"onchain"},
    "dex": {"dex_liquidity"},
    "weather": {"weather"},
    "news": {"news"},
    "sentiment": {"news"},
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_profile_key(module: str | None) -> str:
    key = str(module or "").strip()
    return MODULE_PROFILE_ALIASES.get(key, MODULE_PROFILE_ALIASES.get(key.lower(), key))


def get_tier_profile(module: str | None) -> dict[str, Any]:
    key = resolve_profile_key(module)
    return SPORT_PROFILES.get(key) or SPORT_PROFILES["context_module"]


def _expand_fields(fields: list[str] | set[str] | tuple[str, ...]) -> set[str]:
    expanded: set[str] = set()
    for field in fields:
        key = str(field or "").strip()
        if not key:
            continue
        expanded.add(key)
        expanded.update(FIELD_EXPANSIONS.get(key, set()))
    return expanded


def fields_from_source(source: dict[str, Any]) -> set[str]:
    mapping = dict(source.get("model_mapping") or {})
    fields: set[str] = set()
    for key in ("model_inputs_supported", "outcome_fields_available", "historical_backfill_fields_available", "join_keys"):
        fields.update(str(item) for item in list(mapping.get(key) or []) if item)
    for coverage_key, present in dict(source.get("coverage") or {}).items():
        if bool(present):
            fields.update(COVERAGE_FIELD_EXPANSIONS.get(str(coverage_key), {str(coverage_key)}))
    return _expand_fields(fields)


def fields_from_lane(lane: dict[str, Any], *, include_future: bool = False) -> set[str]:
    fields: set[str] = set()
    sources = list(lane.get("verified_sources") or []) + list(lane.get("source_candidates") or [])
    if include_future:
        sources += list(lane.get("future_source_candidates") or [])
    for source in sources:
        if isinstance(source, dict):
            fields.update(fields_from_source(source))
    return fields


def _profile_all_fields(profile: dict[str, Any]) -> set[str]:
    fields: set[str] = set()
    for tier_fields in dict(profile.get("tiers") or {}).values():
        fields.update(tier_fields)
    return fields


def _has_tier_signal(level: int, profile: dict[str, Any], fields: set[str], derived_fields: set[str]) -> bool:
    tier_fields = set(profile["tiers"][level])
    if level == 0:
        return set(profile["critical_fields"]).issubset(fields | derived_fields)
    return bool(tier_fields & (fields | derived_fields))


def _current_level(profile: dict[str, Any], fields: set[str], derived_fields: set[str]) -> int:
    critical = set(profile["critical_fields"])
    if not critical.issubset(fields | derived_fields):
        return -1
    current = 0
    for level in range(1, 5):
        if _has_tier_signal(level, profile, fields, derived_fields):
            current = level
    return current


def _confidence_for(level: int, profile: dict[str, Any], fields: set[str], derived_fields: set[str]) -> tuple[float, str]:
    rules = dict(profile.get("confidence_cap_rules") or {})
    critical_missing = sorted(set(profile["critical_fields"]) - (fields | derived_fields))
    if critical_missing:
        return 0.0, "missing_critical_tier_0_fields"
    cap = float(rules.get(f"tier_{level}_cap", BASE_CONFIDENCE_CAPS.get(level, 0.0)))
    missing_advanced = sorted(set(profile["tiers"][3]) - (fields | derived_fields))
    missing_context = sorted(set(profile["tiers"][4]) - (fields | derived_fields))
    reason = f"{TIER_NAMES[level].lower()}_cap"
    if missing_advanced and level < 3:
        cap = min(cap, float(rules.get("advanced_missing_cap", cap)))
        reason = "missing_advanced_stats_cap"
    if missing_context and level < 4:
        cap = min(cap, float(rules.get("context_missing_cap", cap)))
        if reason == f"{TIER_NAMES[level].lower()}_cap":
            reason = "missing_context_cap"
    return round(cap, 4), reason


def assess_tier(
    *,
    module: str,
    tier_level: int,
    available_fields: list[str] | set[str],
    derived_fields: list[str] | set[str] | None = None,
) -> dict[str, Any]:
    profile = get_tier_profile(module)
    fields = _expand_fields(set(available_fields or []))
    derived = _expand_fields(set(derived_fields or []))
    tier_fields = set(profile["tiers"][tier_level])
    present = sorted(tier_fields & (fields | derived))
    missing = sorted(tier_fields - (fields | derived))
    current_level = _current_level(profile, fields, derived)
    cap, cap_reason = _confidence_for(min(max(current_level, 0), 4), profile, fields, derived) if current_level >= 0 else (0.0, "missing_critical_tier_0_fields")
    return {
        "tier_name": TIER_NAMES[tier_level],
        "tier_level": tier_level,
        "available_fields": present,
        "missing_fields": missing,
        "derived_fields": sorted(tier_fields & derived),
        "unavailable_not_fabricated_fields": sorted(set(profile["never_fabricate_fields"]) & set(missing)),
        "calibration_bucket": profile["calibration_buckets"][tier_level],
        "confidence_penalty": round(1.0 - cap, 4),
        "confidence_cap": cap,
        "confidence_cap_reason": cap_reason,
        "can_backtest": current_level >= 0,
        "can_train_baseline": current_level >= 0,
        "can_support_review": current_level >= min(tier_level, 1),
        "can_support_confirmed_bet": bool(current_level >= 4 and tier_level >= 4),
        "recommended_use": RECOMMENDED_USE_BY_LEVEL[tier_level],
        "recommended_next_free_layer": FREE_NEXT_ACTION_BY_LEVEL.get(min(tier_level, 4)),
        "budget_required_for_next_layer": False,
        "requires_budget_approval": False,
    }


def evaluate_data_availability(
    *,
    module: str,
    available_fields: list[str] | set[str],
    derived_fields: list[str] | set[str] | None = None,
) -> dict[str, Any]:
    profile = get_tier_profile(module)
    fields = _expand_fields(set(available_fields or []))
    derived = _expand_fields(set(derived_fields or []))
    current = _current_level(profile, fields, derived)
    all_fields = _profile_all_fields(profile)
    missing_critical = sorted(set(profile["critical_fields"]) - (fields | derived))
    missing_advanced = sorted(set(profile["tiers"][3]) - (fields | derived))
    missing_context = sorted(set(profile["tiers"][4]) - (fields | derived))
    cap, cap_reason = _confidence_for(current, profile, fields, derived) if current >= 0 else (0.0, "missing_critical_tier_0_fields")
    tier_name = TIER_NAMES.get(current, "INSUFFICIENT_TIER_0")
    supported = [TIER_NAMES[level] for level in range(0, current + 1)] if current >= 0 else []
    unsupported = [TIER_NAMES[level] for level in range(max(current + 1, 0), 5)]
    if current < 0:
        reliability = "blocked_missing_tier_0"
    elif current == 0:
        reliability = "low_tier_0_only"
    elif current == 1:
        reliability = "moderate_basic_form"
    elif current == 2:
        reliability = "market_aware_partial"
    elif current == 3:
        reliability = "advanced_partial"
    else:
        reliability = "context_aware_partial"
    return {
        "module": profile["module"],
        "profile_module_requested": module,
        "data_availability_tier": tier_name,
        "current_best_tier": tier_name,
        "tier_level": current,
        "supported_tiers": supported,
        "unsupported_tiers": unsupported,
        "fields_available": sorted(all_fields & (fields | derived)),
        "fields_missing": sorted(all_fields - (fields | derived)),
        "derived_fields": sorted(derived),
        "tier_assessments": [
            assess_tier(module=module, tier_level=level, available_fields=fields, derived_fields=derived)
            for level in range(5)
        ],
        "calibration_bucket": profile["calibration_buckets"].get(current, f"{profile['module']}.insufficient_tier0"),
        "calibration_buckets_available": [profile["calibration_buckets"][level] for level in range(0, current + 1)] if current >= 0 else [],
        "missing_critical_inputs": missing_critical,
        "missing_advanced_inputs": missing_advanced,
        "missing_context_inputs": missing_context,
        "confidence_penalty_applied": round(1.0 - cap, 4),
        "confidence_cap": cap,
        "confidence_cap_reason": cap_reason,
        "expected_calibration_reliability": reliability,
        "recommended_next_data_layer": FREE_NEXT_ACTION_BY_LEVEL.get(current, FREE_NEXT_ACTION_BY_LEVEL[-1]),
        "recommended_next_free_layer": FREE_NEXT_ACTION_BY_LEVEL.get(current, FREE_NEXT_ACTION_BY_LEVEL[-1]),
        "data_not_available_warning": "missing fields are reported and not fabricated" if missing_advanced or missing_context or missing_critical else None,
        "can_backtest": current >= 0,
        "can_train_baseline": current >= 0,
        "can_support_review": current >= 0,
        "can_support_confirmed_bet": current >= 4,
        "recommended_use": RECOMMENDED_USE_BY_LEVEL.get(current, RECOMMENDED_USE_BY_LEVEL[-1]),
        "budget_required_for_next_layer": False,
        "requires_budget_approval": False,
    }


def build_prediction_calibration_metadata(
    *,
    module: str,
    available_fields: list[str] | set[str],
    derived_fields: list[str] | set[str] | None = None,
) -> dict[str, Any]:
    availability = evaluate_data_availability(module=module, available_fields=available_fields, derived_fields=derived_fields)
    return {
        "data_availability_tier": availability["data_availability_tier"],
        "calibration_bucket": availability["calibration_bucket"],
        "missing_critical_inputs": availability["missing_critical_inputs"],
        "missing_advanced_inputs": availability["missing_advanced_inputs"],
        "confidence_penalty_applied": availability["confidence_penalty_applied"],
        "confidence_cap": availability["confidence_cap"],
        "confidence_cap_reason": availability["confidence_cap_reason"],
        "expected_calibration_reliability": availability["expected_calibration_reliability"],
        "recommended_next_data_layer": availability["recommended_next_data_layer"],
        "data_not_available_warning": availability["data_not_available_warning"],
    }


def _module_row(lane: dict[str, Any]) -> dict[str, Any]:
    module = str(lane.get("module") or lane.get("lane_id") or "unknown")
    fields = fields_from_lane(lane)
    availability = evaluate_data_availability(module=module, available_fields=fields)
    profile = get_tier_profile(module)
    planner = plan_derived_features(
        available_fields=fields,
        requested_features=list(profile.get("allowed_derived_features_from_free_data") or DEFAULT_DERIVED_FEATURES),
        module=module,
    )
    return {
        "module": module,
        "current_best_tier": availability["current_best_tier"],
        "supported_tiers": availability["supported_tiers"],
        "unsupported_tiers": availability["unsupported_tiers"],
        "fields_available": availability["fields_available"],
        "fields_missing": availability["fields_missing"],
        "derived_features_available": planner["derived_features_available"],
        "derived_features_blocked": planner["derived_features_blocked"][:20],
        "calibration_buckets_available": availability["calibration_buckets_available"],
        "calibration_bucket": availability["calibration_bucket"],
        "missing_critical_inputs": availability["missing_critical_inputs"],
        "missing_advanced_inputs": availability["missing_advanced_inputs"],
        "confidence_cap": availability["confidence_cap"],
        "confidence_cap_reason": availability["confidence_cap_reason"],
        "budget_required_for_next_layer": False,
        "requires_budget_approval": False,
        "next_free_action": availability["recommended_next_free_layer"],
        "paid_action_blocked": True,
        "recommended_no_spend_next_step": availability["recommended_next_free_layer"],
        "data_not_available_warning": availability["data_not_available_warning"],
    }


def build_data_availability_report(*, registry: dict[str, Any], module: str | None = None) -> dict[str, Any]:
    lanes = list(registry.get("lanes") or [])
    if module:
        needle = str(module)
        lanes = [
            lane for lane in lanes
            if str(lane.get("module")) == needle
            or str(lane.get("lane_id")) == needle
            or resolve_profile_key(str(lane.get("module"))) == resolve_profile_key(needle)
        ]
    modules = [_module_row(lane) for lane in lanes]
    enabled_sources = [
        source for source in list(registry.get("sources") or [])
        if bool(source.get("enabled", False))
    ]
    paid_enabled = [
        source for source in enabled_sources
        if bool(source.get("requires_budget_approval", False)) or bool(source.get("paid_upgrade_allowed", False))
    ]
    return {
        "ok": True,
        "status": "ok",
        "schema_version": DATA_AVAILABILITY_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "module_filter": module,
        "total_modules": len(modules),
        "modules": modules,
        "enabled_source_count": len(enabled_sources),
        "paid_source_enabled_count": len(paid_enabled),
        "paid_action_blocked": True,
        "recommended_no_spend_next_step": "no-call audit of existing source reports",
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "storage_health": get_storage_health(),
    }


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    path = base / "data_availability"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _rel(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


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


def render_data_availability_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Data Availability Tiers",
        "",
        f"- created_at: {report.get('created_at')}",
        f"- total_modules: {report.get('total_modules')}",
        f"- enabled_source_count: {report.get('enabled_source_count')}",
        f"- paid_source_enabled_count: {report.get('paid_source_enabled_count')}",
        "- provider_write: false",
        "- execution_allowed: false",
        "- raw_payload_included: false",
        "- secrets_included: false",
        "",
        "## Modules",
    ]
    for row in list(report.get("modules") or []):
        lines.append(
            f"- {row.get('module')}: {row.get('current_best_tier')}, cap={row.get('confidence_cap')}, next={row.get('recommended_no_spend_next_step')}"
        )
    return "\n".join(lines) + "\n"


def write_data_availability_report(report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    root = _root(base_data_dir)
    created = str(report.get("created_at") or utc_now_iso())
    day = created[:10]
    run_id = sanitize_filename(f"data_availability_{created.replace(':', '-')}_{uuid4().hex[:8]}")
    latest = root / "latest.json"
    item = root / "items" / f"{run_id}.json"
    daily_json = root / "daily" / f"{day}.json"
    daily_md = root / "daily" / f"{day}.md"
    payload = {**report, "raw_payload_included": False, "secrets_included": False}
    _atomic_write_json(latest, payload)
    _atomic_write_json(item, payload)
    _atomic_write_json(daily_json, payload)
    _atomic_write_text(daily_md, render_data_availability_markdown(payload))
    return {
        "latest_path": _rel(latest, base_data_dir),
        "item_path": _rel(item, base_data_dir),
        "daily_json_path": _rel(daily_json, base_data_dir),
        "daily_markdown_path": _rel(daily_md, base_data_dir),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=None)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    from .data_source_registry import build_registry

    report = build_data_availability_report(registry=build_registry(module=args.module), module=args.module)
    if args.persist:
        report.update(write_data_availability_report(report))
    print(json.dumps({
        "ok": report["ok"],
        "status": report["status"],
        "total_modules": report["total_modules"],
        "latest_path": report.get("latest_path"),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
