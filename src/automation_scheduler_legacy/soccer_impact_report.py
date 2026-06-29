from __future__ import annotations

from typing import Any

from .soccer_data_availability import evaluate_soccer_data_availability
from .soccer_goalkeeper_context import evaluate_soccer_goalkeeper_context
from .soccer_impact_calibration import evaluate_soccer_impact_calibration
from .soccer_impact_common import (
    ALLOWED_SOCCER_ACTIONS,
    FORBIDDEN_SOCCER_ACTIONS,
    PLAYER_PROP_MARKETS,
    TEAM_MARKETS,
    TOTAL_MARKETS,
    clamp,
    compact_list,
    finalize_soccer_response,
    normalize_soccer_market,
    normalize_soccer_sport,
    weighted_average,
)
from .soccer_impact_readiness import build_soccer_impact_readiness
from .soccer_impact_red_team import evaluate_soccer_impact_red_team
from .soccer_incentive_context import evaluate_soccer_incentive_context
from .soccer_lineup_availability_context import evaluate_soccer_lineup_availability_context
from .soccer_market_relevance import evaluate_soccer_market_relevance
from .soccer_matchup_context import evaluate_soccer_matchup_context
from .soccer_player_role_impact import evaluate_soccer_player_role_impact
from .soccer_possession_value_impact import evaluate_soccer_possession_value_impact
from .soccer_pressing_transition_context import evaluate_soccer_pressing_transition_context
from .soccer_referee_context import evaluate_soccer_referee_context
from .soccer_set_piece_context import evaluate_soccer_set_piece_context
from .soccer_tactical_context import evaluate_soccer_tactical_context


def _merge(*contexts: dict[str, Any] | None) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, dict):
            row.update(context)
    return row


def _combine_missing(*sections: dict[str, Any]) -> list[str]:
    values: list[Any] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        values.extend(section.get("missing_inputs") or [])
        values.extend(section.get("missing_player_inputs") or [])
        values.extend(section.get("missing_goalkeeper_inputs") or [])
    return compact_list(values, limit=90)


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
    if market_type in PLAYER_PROP_MARKETS and not player_level_allowed:
        return "DATA_INSUFFICIENT"
    if no_bet_reasons:
        return "NO_BET"
    if calibration_status == "calibration_ready" and selected_market_relevance >= 72:
        return "ACTIVE_REVIEW"
    if calibration_status == "insufficient_data":
        return "CALIBRATION_ONLY"
    if market_type in PLAYER_PROP_MARKETS:
        return "PLAYER_PROP_REVIEW_ONLY" if selected_market_relevance >= 50 else "CALIBRATION_ONLY"
    if market_type in TOTAL_MARKETS:
        return "TOTALS_REVIEW_ONLY" if selected_market_relevance >= 50 else "MARKET_REVIEW_ONLY"
    if market_type in TEAM_MARKETS:
        return "TEAM_MARKET_REVIEW_ONLY" if selected_market_relevance >= 50 else "MARKET_REVIEW_ONLY"
    return "WATCHLIST_REVIEW" if selected_market_relevance >= 60 else "MARKET_REVIEW_ONLY"


def build_soccer_impact_diagnostics(
    *,
    sport: str = "soccer",
    market_type: str = "three_way_moneyline",
    game_context: dict[str, Any] | None = None,
    team_context: dict[str, Any] | None = None,
    player_context: dict[str, Any] | None = None,
    lineup_context: dict[str, Any] | None = None,
    tactical_context: dict[str, Any] | None = None,
    possession_value_context: dict[str, Any] | None = None,
    shot_quality_context: dict[str, Any] | None = None,
    pressing_context: dict[str, Any] | None = None,
    transition_context: dict[str, Any] | None = None,
    set_piece_context: dict[str, Any] | None = None,
    goalkeeper_context: dict[str, Any] | None = None,
    referee_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration_context: dict[str, Any] | None = None,
    tracking_context: dict[str, Any] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    normalized_sport = normalize_soccer_sport(sport)
    market = normalize_soccer_market(market_type)
    source_payload = {
        "sport": sport,
        "market_type": market_type,
        "game_context": game_context or {},
        "team_context": team_context or {},
        "player_context": player_context or {},
        "lineup_context": lineup_context or {},
        "tactical_context": tactical_context or {},
        "possession_value_context": possession_value_context or {},
        "shot_quality_context": shot_quality_context or {},
        "pressing_context": pressing_context or {},
        "transition_context": transition_context or {},
        "set_piece_context": set_piece_context or {},
        "goalkeeper_context": goalkeeper_context or {},
        "referee_context": referee_context or {},
        "matchup_context": matchup_context or {},
        "availability_context": availability_context or {},
        "incentive_context": incentive_context or {},
        "calibration_context": calibration_context or {},
        "tracking_context": tracking_context or {},
        "dry_run": dry_run,
    }
    data = evaluate_soccer_data_availability(
        normalized_sport,
        market_type=market,
        game_context=game_context,
        team_context=team_context,
        player_context=player_context,
        lineup_context=lineup_context,
        tactical_context=tactical_context,
        possession_value_context=possession_value_context,
        shot_quality_context=shot_quality_context,
        pressing_context=pressing_context,
        transition_context=transition_context,
        set_piece_context=set_piece_context,
        goalkeeper_context=goalkeeper_context,
        referee_context=referee_context,
        matchup_context=matchup_context,
        availability_context=availability_context,
        incentive_context=incentive_context,
        calibration_context=calibration_context,
        tracking_context=tracking_context,
    )
    data_tier = int(data.get("data_tier", 0) or 0)
    possession = evaluate_soccer_possession_value_impact(_merge(team_context, possession_value_context, shot_quality_context, set_piece_context, transition_context), data_tier=data_tier, market_type=market)
    tactical = evaluate_soccer_tactical_context(tactical_context or {})
    pressing = evaluate_soccer_pressing_transition_context(_merge(pressing_context, transition_context, team_context))
    player = evaluate_soccer_player_role_impact(player_context or {}, player_level_allowed=bool(data.get("player_level_allowed")), data_tier=data_tier)
    lineup = evaluate_soccer_lineup_availability_context(_merge(lineup_context, availability_context, goalkeeper_context, incentive_context))
    set_piece = evaluate_soccer_set_piece_context(_merge(set_piece_context, referee_context, player_context))
    keeper = evaluate_soccer_goalkeeper_context(_merge(goalkeeper_context, lineup_context))
    referee = evaluate_soccer_referee_context(referee_context or {})
    matchup = evaluate_soccer_matchup_context(_merge(team_context, tactical_context, pressing_context, transition_context, set_piece_context, goalkeeper_context, referee_context, matchup_context, lineup_context), market_type=market)
    incentive = evaluate_soccer_incentive_context(incentive_context or {})
    market_relevance = evaluate_soccer_market_relevance(
        {"market_type": market, **(goalkeeper_context or {})},
        market_type=market,
        possession_value_impact=possession,
        tactical_context=tactical,
        pressing_transition_context=pressing,
        player_role_impact=player,
        lineup_availability_context=lineup,
        set_piece_context=set_piece,
        goalkeeper_context=keeper,
        referee_context=referee,
        matchup_context=matchup,
        incentive_context=incentive,
    )
    calibration = evaluate_soccer_impact_calibration(
        calibration_context or {},
        sport=normalized_sport,
        market_type=market,
        role=str(player.get("role") or "UNKNOWN"),
        data_tier=data_tier,
    )
    red_team = evaluate_soccer_impact_red_team(
        data_availability=data,
        possession_value_impact=possession,
        tactical_context=tactical,
        pressing_transition_context=pressing,
        player_role_impact=player,
        lineup_availability_context=lineup,
        set_piece_context=set_piece,
        goalkeeper_context=keeper,
        referee_context=referee,
        matchup_context=matchup,
        incentive_context=incentive,
        market_relevance=market_relevance,
        calibration=calibration,
        tracking_context=tracking_context or {},
    )
    no_bet_reasons = compact_list(
        [
            *(tactical.get("no_bet_reasons") or []),
            *(pressing.get("no_bet_reasons") or []),
            *(player.get("no_bet_reasons") or []),
            *(lineup.get("no_bet_reasons") or []),
            *(set_piece.get("no_bet_reasons") or []),
            *(keeper.get("no_bet_reasons") or []),
            *(referee.get("no_bet_reasons") or []),
            *(matchup.get("no_bet_reasons") or []),
            *(incentive.get("no_bet_reasons") or []),
            *(market_relevance.get("no_bet_market_reasons") or []),
            *(red_team.get("no_bet_reasons") or []),
        ],
        limit=40,
    )
    selected_relevance = float(market_relevance.get("selected_market_relevance_score", 0.0) or 0.0)
    action = _recommended_action(
        data_tier=data_tier,
        market_type=market,
        calibration_status=str(calibration.get("calibration_status") or "insufficient_data"),
        no_bet_reasons=no_bet_reasons,
        player_level_allowed=bool(data.get("player_level_allowed", False)),
        selected_market_relevance=selected_relevance,
    )
    red_adjustment = str(red_team.get("recommended_action_adjustment") or "NO_CHANGE")
    if red_adjustment == "NO_BET":
        action = "NO_BET"
    elif red_adjustment == "DATA_INSUFFICIENT" and action not in {"NO_BET", "DATA_INSUFFICIENT"}:
        action = "DATA_INSUFFICIENT"
    elif red_adjustment == "WATCHLIST_REVIEW" and action == "ACTIVE_REVIEW":
        action = "WATCHLIST_REVIEW"
    if action not in ALLOWED_SOCCER_ACTIONS:
        action = "CALIBRATION_ONLY"
    soccer_score = weighted_average(
        (
            (possession.get("possession_value_score"), 0.2),
            (possession.get("chance_quality_score"), 0.18),
            (tactical.get("tactical_fit_score"), 0.1),
            (pressing.get("market_relevance_modifier"), 0.08),
            (player.get("player_impact_score"), 0.08),
            (lineup.get("availability_score"), 0.1),
            (set_piece.get("set_piece_attack_score"), 0.06),
            (keeper.get("goalkeeper_impact_score"), 0.08),
            (referee.get("referee_environment_score"), 0.04),
            (matchup.get("matchup_advantage_score"), 0.08),
            (selected_relevance, 0.1),
        )
    ) or 0.0
    soccer_score = clamp(soccer_score - float(red_team.get("downgrade_score", 0.0) or 0.0) * 0.25)
    missing = _combine_missing(possession, tactical, pressing, player, lineup, set_piece, keeper, referee, matchup)
    missing = compact_list([*missing, *(red_team.get("missing_inputs") or [])], limit=90)
    next_data = compact_list([*(data.get("next_data_to_collect") or []), *(calibration.get("next_required_data") or []), *(red_team.get("missing_inputs") or [])], limit=45)
    result = {
        "ok": True,
        "status": "soccer_possession_value_impact_complete",
        "sport": normalized_sport,
        "market_type": market,
        "data_tier": data_tier,
        "tier_name": data.get("tier_name"),
        "team_level_allowed": bool(data.get("team_level_allowed", False)),
        "player_level_allowed": bool(data.get("player_level_allowed", False)),
        "tactical_level_allowed": bool(data.get("tactical_level_allowed", False)),
        "tracking_level_allowed": bool(data.get("tracking_level_allowed", False)),
        "data_availability": data,
        "possession_value_impact": possession,
        "tactical_context": tactical,
        "pressing_transition_context": pressing,
        "player_role_impact": player,
        "lineup_availability_context": lineup,
        "set_piece_context": set_piece,
        "goalkeeper_context": keeper,
        "referee_context": referee,
        "matchup_context": matchup,
        "incentive_context": incentive,
        "market_relevance": market_relevance,
        "calibration_status": calibration.get("calibration_status", "insufficient_data"),
        "calibration": calibration,
        "red_team": red_team,
        "soccer_impact_score": round(soccer_score, 2),
        "recommended_review_status": action,
        "recommended_action_adjustment": action,
        "markets_to_review": compact_list([] if action in {"NO_BET", "DATA_INSUFFICIENT"} else (market_relevance.get("strongest_market_links") or []), limit=12),
        "no_bet_reasons": no_bet_reasons,
        "missing_inputs": missing,
        "next_data_to_collect": next_data,
        "allowed_recommendations": list(ALLOWED_SOCCER_ACTIONS),
        "forbidden_recommendations_rejected": list(FORBIDDEN_SOCCER_ACTIONS),
        "dry_run": True,
        "compact_response": True,
    }
    return finalize_soccer_response(result, source_payload=source_payload)
