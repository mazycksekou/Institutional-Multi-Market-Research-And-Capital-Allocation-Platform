from __future__ import annotations

from typing import Any

from .football_availability_context import evaluate_football_availability_context
from .football_data_availability import FIELD_GROUPS, evaluate_football_data_availability
from .football_impact_calibration import evaluate_football_impact_calibration
from .football_impact_schema import (
    ALLOWED_FOOTBALL_ACTIONS,
    DATA_TIER_REQUIREMENTS,
    FORBIDDEN_FOOTBALL_ACTIONS,
    SUPPORTED_FOOTBALL_MARKET_TYPES,
    SUPPORTED_FOOTBALL_ROLES,
    SUPPORTED_FOOTBALL_SPORTS,
    PLAYER_PROP_MARKETS,
    TEAM_MARKETS,
    compact_list,
    finalize_football_response,
    normalize_football_market,
    normalize_football_sport,
)
from .football_incentive_context import evaluate_football_incentive_context
from .football_market_relevance import evaluate_football_market_relevance
from .football_matchup_context import evaluate_football_matchup_context
from .football_personnel_context import evaluate_football_personnel_context
from .football_play_drive_impact import evaluate_football_play_drive_impact
from .football_role_impact import evaluate_football_role_impact


def _combine_missing(*sections: dict[str, Any]) -> list[str]:
    values: list[Any] = []
    for section in sections:
        if isinstance(section, dict):
            values.extend(section.get("missing_inputs") or section.get("missing_role_inputs") or [])
    return compact_list(values, limit=60)


def _recommended_action(
    *,
    data_tier: int,
    market_type: str,
    calibration_status: str,
    no_bet_reasons: list[str],
    player_level_allowed: bool,
    selected_market_relevance: float,
) -> str:
    if data_tier <= 0:
        return "DATA_INSUFFICIENT"
    if no_bet_reasons:
        return "NO_BET"
    if calibration_status == "insufficient_data":
        return "CALIBRATION_ONLY"
    if market_type in PLAYER_PROP_MARKETS:
        if not player_level_allowed:
            return "DATA_INSUFFICIENT"
        return "PLAYER_PROP_REVIEW_ONLY" if selected_market_relevance >= 50.0 else "CALIBRATION_ONLY"
    if market_type in TEAM_MARKETS:
        return "TEAM_MARKET_REVIEW_ONLY" if selected_market_relevance >= 50.0 else "MARKET_REVIEW_ONLY"
    return "WATCHLIST_REVIEW" if selected_market_relevance >= 60.0 else "MARKET_REVIEW_ONLY"


def build_football_impact_diagnostics(
    *,
    sport: str = "americanfootball_nfl",
    market_type: str = "spread",
    team_context: dict[str, Any] | None = None,
    player_context: dict[str, Any] | None = None,
    play_drive_context: dict[str, Any] | None = None,
    personnel_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration_context: dict[str, Any] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    normalized_sport = normalize_football_sport(sport)
    market = normalize_football_market(market_type)
    source_payload = {
        "sport": sport,
        "market_type": market_type,
        "team_context": team_context or {},
        "player_context": player_context or {},
        "play_drive_context": play_drive_context or {},
        "personnel_context": personnel_context or {},
        "matchup_context": matchup_context or {},
        "availability_context": availability_context or {},
        "incentive_context": incentive_context or {},
        "calibration_context": calibration_context or {},
        "dry_run": dry_run,
    }
    availability = evaluate_football_data_availability(
        normalized_sport,
        team_context=team_context,
        player_context=player_context,
        play_drive_context=play_drive_context,
        personnel_context=personnel_context,
        matchup_context=matchup_context,
        availability_context=availability_context,
        incentive_context=incentive_context,
        calibration_context=calibration_context,
        market_type=market,
    )
    data_tier = int(availability.get("data_tier", 0) or 0)
    play_drive = evaluate_football_play_drive_impact(play_drive_context or team_context or {}, data_tier=data_tier)
    role = evaluate_football_role_impact(
        player_context or {},
        player_level_allowed=bool(availability.get("player_level_allowed", False)),
        data_tier=data_tier,
    )
    personnel = evaluate_football_personnel_context(personnel_context or {})
    matchup_input: dict[str, Any] = {}
    if isinstance(matchup_context, dict):
        matchup_input.update(matchup_context)
    if isinstance(availability_context, dict):
        matchup_input.setdefault("wind_mph", availability_context.get("wind_mph"))
    matchup = evaluate_football_matchup_context(matchup_input, market_type=market)
    avail = evaluate_football_availability_context(availability_context or {})
    incentive = evaluate_football_incentive_context(incentive_context or {})
    market_relevance = evaluate_football_market_relevance(
        {"market_type": market},
        market_type=market,
        play_drive_impact=play_drive,
        role_impact=role,
        personnel_context=personnel,
        matchup_context=matchup,
        availability_context=avail,
        incentive_context=incentive,
    )
    calibration = evaluate_football_impact_calibration(
        calibration_context or {},
        sport=normalized_sport,
        market_type=market,
        role=str(role.get("role") or "unknown"),
        data_tier=data_tier,
    )
    no_bet_reasons = compact_list(
        [
            *(matchup.get("no_bet_reasons") or []),
            *(market_relevance.get("no_bet_market_reasons") or []),
            *(incentive.get("no_bet_reasons") or []),
            "player_level_data_required_for_player_prop" if market in PLAYER_PROP_MARKETS and not availability.get("player_level_allowed") else None,
        ],
        limit=25,
    )
    selected_relevance = float(market_relevance.get("selected_market_relevance_score", 0.0) or 0.0)
    action = _recommended_action(
        data_tier=data_tier,
        market_type=market,
        calibration_status=str(calibration.get("calibration_status") or "insufficient_data"),
        no_bet_reasons=no_bet_reasons,
        player_level_allowed=bool(availability.get("player_level_allowed", False)),
        selected_market_relevance=selected_relevance,
    )
    if action not in ALLOWED_FOOTBALL_ACTIONS:
        action = "CALIBRATION_ONLY"
    missing = _combine_missing(play_drive, role, personnel, matchup, avail, incentive)
    next_data = compact_list([*(availability.get("next_data_to_collect") or []), *(calibration.get("next_required_data") or [])], limit=30)
    result = {
        "ok": True,
        "status": "football_impact_diagnostics_complete",
        "sport": normalized_sport,
        "market_type": market,
        "data_tier": data_tier,
        "tier_name": availability.get("tier_name"),
        "player_level_allowed": bool(availability.get("player_level_allowed", False)),
        "tracking_level_allowed": bool(availability.get("tracking_level_allowed", False)),
        "data_availability": availability,
        "play_drive_impact": play_drive,
        "role_impact": role,
        "personnel_context": personnel,
        "matchup_context": matchup,
        "availability_context": avail,
        "incentive_context": incentive,
        "market_relevance": market_relevance,
        "calibration_status": calibration.get("calibration_status", "insufficient_data"),
        "calibration": calibration,
        "recommended_action_adjustment": action,
        "no_bet_reasons": no_bet_reasons,
        "missing_inputs": missing,
        "next_data_to_collect": next_data,
        "allowed_recommendations": list(ALLOWED_FOOTBALL_ACTIONS),
        "forbidden_recommendations_rejected": list(FORBIDDEN_FOOTBALL_ACTIONS),
        "dry_run": True,
        "compact_response": True,
    }
    return finalize_football_response(result, source_payload=source_payload)


def build_football_impact_readiness() -> dict[str, Any]:
    ncaaf_missing = [
        "player_participation_where_available",
        "snap_share_route_target_carry_share_where_publicly_available",
        "settled_outcome_calibration_buckets",
    ]
    readiness = {
        "ok": True,
        "status": "football_impact_readiness",
        "supported_sports": list(SUPPORTED_FOOTBALL_SPORTS),
        "supported_roles": list(SUPPORTED_FOOTBALL_ROLES),
        "supported_markets": list(SUPPORTED_FOOTBALL_MARKET_TYPES),
        "data_tier_requirements": DATA_TIER_REQUIREMENTS,
        "field_groups": {key: list(value) for key, value in FIELD_GROUPS.items()},
        "nfl_readiness": {
            "status": "foundation_ready",
            "minimum_useful_tier": 2,
            "player_level_tier": 3,
            "tracking_optional_tier": 4,
            "provider_write": False,
            "execution_allowed": False,
        },
        "ncaaf_readiness": {
            "status": "foundation_ready_limited_public_data_aware",
            "minimum_useful_tier": 1,
            "player_level_tier": "only_where_participation_data_exists",
            "tracking_optional_tier": "not_assumed",
            "provider_write": False,
            "execution_allowed": False,
        },
        "missing_data_by_sport": {
            "americanfootball_nfl": ["settled_outcome_calibration_buckets", "optional_tracking_context"],
            "americanfootball_ncaaf": ncaaf_missing,
        },
        "calibration_requirements": [
            "bucketed_by_sport_market_role_data_tier_context_weather_injury_liquidity",
            "real_settled_outcomes_required",
            "open_close_prices_required_for_clv_proxy",
            "real_return_records_required_for_roi_proxy",
        ],
        "no_spend_policy": {
            "paid_data_required": False,
            "new_provider_calls_added": False,
            "tracking_required": False,
            "heavy_ml_training_added": False,
        },
        "recommended_initial_use": [
            "NCAAF team_unit_drive_review_when_play_drive_data_exists",
            "NFL role_player_prop_review_when_snap_route_target_context_exists",
            "no_bet_downgrades_for_injury_weather_qb_uncertainty",
            "calibration_only_until_outcomes_accumulate",
        ],
    }
    return finalize_football_response(readiness, source_payload=readiness)
