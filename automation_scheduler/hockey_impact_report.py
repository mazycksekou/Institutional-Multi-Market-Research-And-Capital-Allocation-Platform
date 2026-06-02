from __future__ import annotations

from typing import Any

from .hockey_availability_context import evaluate_hockey_availability_context
from .hockey_data_availability import evaluate_hockey_data_availability
from .hockey_goalie_impact import evaluate_hockey_goalie_impact
from .hockey_impact_calibration import evaluate_hockey_impact_calibration
from .hockey_impact_common import (
    ALLOWED_HOCKEY_ACTIONS,
    FORBIDDEN_HOCKEY_ACTIONS,
    GOALIE_PROP_MARKETS,
    SKATER_PROP_MARKETS,
    TEAM_MARKETS,
    clamp,
    compact_list,
    finalize_hockey_response,
    normalize_hockey_market,
    normalize_hockey_sport,
    weighted_average,
)
from .hockey_impact_readiness import build_hockey_impact_readiness
from .hockey_impact_red_team import evaluate_hockey_impact_red_team
from .hockey_incentive_context import evaluate_hockey_incentive_context
from .hockey_line_pair_context import evaluate_hockey_line_pair_context
from .hockey_market_relevance import evaluate_hockey_market_relevance
from .hockey_matchup_context import evaluate_hockey_matchup_context
from .hockey_possession_impact import evaluate_hockey_possession_impact
from .hockey_skater_impact import evaluate_hockey_skater_impact
from .hockey_special_teams_context import evaluate_hockey_special_teams_context
from .hockey_transition_context import evaluate_hockey_transition_context


def _combine_missing(*sections: dict[str, Any]) -> list[str]:
    values: list[Any] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        values.extend(section.get("missing_inputs") or [])
        values.extend(section.get("missing_skater_inputs") or [])
        values.extend(section.get("missing_goalie_inputs") or [])
    return compact_list(values, limit=80)


def _recommended_action(
    *,
    data_tier: int,
    market_type: str,
    calibration_status: str,
    no_bet_reasons: list[str],
    skater_level_allowed: bool,
    goalie_level_allowed: bool,
    selected_market_relevance: float,
) -> str:
    if data_tier <= 0:
        return "DATA_INSUFFICIENT"
    if market_type in SKATER_PROP_MARKETS and not skater_level_allowed:
        return "DATA_INSUFFICIENT"
    if market_type in GOALIE_PROP_MARKETS and not goalie_level_allowed:
        return "DATA_INSUFFICIENT"
    if no_bet_reasons:
        return "NO_BET"
    if calibration_status == "calibration_ready" and selected_market_relevance >= 72.0:
        return "ACTIVE_REVIEW"
    if calibration_status == "insufficient_data":
        return "CALIBRATION_ONLY"
    if market_type in SKATER_PROP_MARKETS:
        return "PLAYER_PROP_REVIEW_ONLY" if selected_market_relevance >= 50.0 else "CALIBRATION_ONLY"
    if market_type in GOALIE_PROP_MARKETS:
        return "GOALIE_PROP_REVIEW_ONLY" if selected_market_relevance >= 50.0 else "CALIBRATION_ONLY"
    if market_type in TEAM_MARKETS:
        return "TEAM_MARKET_REVIEW_ONLY" if selected_market_relevance >= 50.0 else "MARKET_REVIEW_ONLY"
    return "WATCHLIST_REVIEW" if selected_market_relevance >= 60.0 else "MARKET_REVIEW_ONLY"


def _merge(*contexts: dict[str, Any] | None) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, dict):
            row.update(context)
    return row


def build_hockey_impact_diagnostics(
    *,
    sport: str = "icehockey_nhl",
    market_type: str = "moneyline",
    game_context: dict[str, Any] | None = None,
    team_context: dict[str, Any] | None = None,
    skater_context: dict[str, Any] | None = None,
    goalie_context: dict[str, Any] | None = None,
    line_context: dict[str, Any] | None = None,
    pair_context: dict[str, Any] | None = None,
    special_teams_context: dict[str, Any] | None = None,
    transition_context: dict[str, Any] | None = None,
    shot_quality_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration_context: dict[str, Any] | None = None,
    tracking_context: dict[str, Any] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    normalized_sport = normalize_hockey_sport(sport)
    market = normalize_hockey_market(market_type)
    source_payload = {
        "sport": sport,
        "market_type": market_type,
        "game_context": game_context or {},
        "team_context": team_context or {},
        "skater_context": skater_context or {},
        "goalie_context": goalie_context or {},
        "line_context": line_context or {},
        "pair_context": pair_context or {},
        "special_teams_context": special_teams_context or {},
        "transition_context": transition_context or {},
        "shot_quality_context": shot_quality_context or {},
        "matchup_context": matchup_context or {},
        "availability_context": availability_context or {},
        "incentive_context": incentive_context or {},
        "calibration_context": calibration_context or {},
        "tracking_context": tracking_context or {},
        "dry_run": dry_run,
    }
    data = evaluate_hockey_data_availability(
        normalized_sport,
        market_type=market,
        game_context=game_context,
        team_context=team_context,
        skater_context=skater_context,
        goalie_context=goalie_context,
        line_context=line_context,
        pair_context=pair_context,
        special_teams_context=special_teams_context,
        transition_context=transition_context,
        shot_quality_context=shot_quality_context,
        matchup_context=matchup_context,
        availability_context=availability_context,
        incentive_context=incentive_context,
        calibration_context=calibration_context,
        tracking_context=tracking_context,
    )
    data_tier = int(data.get("data_tier", 0) or 0)
    possession = evaluate_hockey_possession_impact(_merge(team_context, shot_quality_context), data_tier=data_tier, market_type=market)
    skater = evaluate_hockey_skater_impact(_merge(skater_context, line_context, special_teams_context), skater_level_allowed=bool(data.get("skater_level_allowed")), data_tier=data_tier)
    goalie = evaluate_hockey_goalie_impact(_merge(goalie_context, availability_context), goalie_level_allowed=bool(data.get("goalie_level_allowed")))
    line_pair = evaluate_hockey_line_pair_context(_merge(line_context, pair_context))
    special = evaluate_hockey_special_teams_context(special_teams_context or {})
    transition = evaluate_hockey_transition_context(_merge(transition_context, tracking_context))
    avail = evaluate_hockey_availability_context(_merge(availability_context, goalie_context, line_context, pair_context))
    incentive = evaluate_hockey_incentive_context(incentive_context or {})
    matchup = evaluate_hockey_matchup_context(
        _merge(team_context, shot_quality_context, line_context, pair_context, goalie_context, special_teams_context, transition_context, matchup_context, availability_context),
        market_type=market,
    )
    market_relevance = evaluate_hockey_market_relevance(
        {"market_type": market},
        market_type=market,
        possession_impact=possession,
        skater_impact=skater,
        goalie_impact=goalie,
        line_pair_context=line_pair,
        special_teams_context=special,
        transition_context=transition,
        matchup_context=matchup,
        availability_context=avail,
        incentive_context=incentive,
    )
    calibration = evaluate_hockey_impact_calibration(
        calibration_context or {},
        sport=normalized_sport,
        market_type=market,
        role=str(skater.get("skater_role") or "UNKNOWN"),
        data_tier=data_tier,
    )
    red_team = evaluate_hockey_impact_red_team(
        data_availability=data,
        possession_impact=possession,
        skater_impact=skater,
        goalie_impact=goalie,
        line_pair_context=line_pair,
        special_teams_context=special,
        transition_context=transition,
        matchup_context=matchup,
        availability_context=avail,
        incentive_context=incentive,
        market_relevance=market_relevance,
        calibration=calibration,
        tracking_context=tracking_context or {},
    )
    no_bet_reasons = compact_list(
        [
            *(possession.get("no_bet_reasons") or []),
            *(skater.get("no_bet_reasons") or []),
            *(goalie.get("no_bet_reasons") or []),
            *(line_pair.get("no_bet_reasons") or []),
            *(special.get("no_bet_reasons") or []),
            *(transition.get("no_bet_reasons") or []),
            *(matchup.get("no_bet_reasons") or []),
            *(avail.get("no_bet_reasons") or []),
            *(incentive.get("no_bet_reasons") or []),
            *(market_relevance.get("no_bet_market_reasons") or []),
            *(red_team.get("no_bet_reasons") or []),
        ],
        limit=35,
    )
    selected_relevance = float(market_relevance.get("selected_market_relevance_score", 0.0) or 0.0)
    action = _recommended_action(
        data_tier=data_tier,
        market_type=market,
        calibration_status=str(calibration.get("calibration_status") or "insufficient_data"),
        no_bet_reasons=no_bet_reasons,
        skater_level_allowed=bool(data.get("skater_level_allowed", False)),
        goalie_level_allowed=bool(data.get("goalie_level_allowed", False)),
        selected_market_relevance=selected_relevance,
    )
    red_team_adjustment = str(red_team.get("recommended_action_adjustment") or "NO_CHANGE")
    if red_team_adjustment == "NO_BET":
        action = "NO_BET"
    elif red_team_adjustment == "DATA_INSUFFICIENT" and action not in {"NO_BET", "DATA_INSUFFICIENT"}:
        action = "DATA_INSUFFICIENT"
    elif red_team_adjustment == "WATCHLIST_REVIEW" and action == "ACTIVE_REVIEW":
        action = "WATCHLIST_REVIEW"
    if action not in ALLOWED_HOCKEY_ACTIONS:
        action = "CALIBRATION_ONLY"

    hockey_score = weighted_average(
        (
            (possession.get("possession_score"), 0.22),
            (skater.get("skater_impact_score"), 0.14),
            (goalie.get("goalie_impact_score"), 0.16),
            (line_pair.get("team_market_modifier"), 0.1),
            (special.get("special_teams_edge_score"), 0.1),
            (transition.get("transition_score"), 0.08),
            (matchup.get("matchup_advantage_score"), 0.1),
            (avail.get("availability_score"), 0.1),
            (selected_relevance, 0.1),
        )
    ) or 0.0
    hockey_score = clamp(hockey_score - float(red_team.get("downgrade_score", 0.0) or 0.0) * 0.25)
    markets_to_review = []
    if action not in {"NO_BET", "DATA_INSUFFICIENT"}:
        markets_to_review = market_relevance.get("strongest_market_links") or []
    missing = _combine_missing(possession, skater, goalie, line_pair, special, transition, matchup, avail)
    missing = compact_list([*missing, *(red_team.get("missing_inputs") or [])], limit=80)
    next_data = compact_list([*(data.get("next_data_to_collect") or []), *(calibration.get("next_required_data") or []), *(red_team.get("missing_inputs") or [])], limit=40)
    result = {
        "ok": True,
        "status": "hockey_player_impact_complete",
        "sport": normalized_sport,
        "market_type": market,
        "data_tier": data_tier,
        "tier_name": data.get("tier_name"),
        "team_level_allowed": bool(data.get("team_level_allowed", False)),
        "skater_level_allowed": bool(data.get("skater_level_allowed", False)),
        "goalie_level_allowed": bool(data.get("goalie_level_allowed", False)),
        "line_level_allowed": bool(data.get("line_level_allowed", False)),
        "tracking_level_allowed": bool(data.get("tracking_level_allowed", False)),
        "data_availability": data,
        "possession_impact": possession,
        "skater_impact": skater,
        "goalie_impact": goalie,
        "line_pair_context": line_pair,
        "special_teams_context": special,
        "transition_context": transition,
        "matchup_context": matchup,
        "availability_context": avail,
        "incentive_context": incentive,
        "market_relevance": market_relevance,
        "calibration_status": calibration.get("calibration_status", "insufficient_data"),
        "calibration": calibration,
        "red_team": red_team,
        "hockey_impact_score": round(hockey_score, 2),
        "recommended_review_status": action,
        "recommended_action_adjustment": action,
        "markets_to_review": compact_list(markets_to_review, limit=12),
        "no_bet_reasons": no_bet_reasons,
        "missing_inputs": missing,
        "next_data_to_collect": next_data,
        "allowed_recommendations": list(ALLOWED_HOCKEY_ACTIONS),
        "forbidden_recommendations_rejected": list(FORBIDDEN_HOCKEY_ACTIONS),
        "dry_run": True,
        "compact_response": True,
    }
    return finalize_hockey_response(result, source_payload=source_payload)
