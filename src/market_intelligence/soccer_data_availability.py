from __future__ import annotations

from typing import Any

from .soccer_impact_common import DATA_TIER_REQUIREMENTS, compact_list, finalize_soccer_response, normalize_soccer_sport, present_fields


FIELD_GROUPS: dict[str, tuple[str, ...]] = {
    "basic_game_context": ("team", "opponent", "home_team", "away_team", "home_away", "league", "competition", "season"),
    "team_box_score_context": ("goals_for_per_game", "goals_against_per_game", "shots_for_per_game", "shots_against_per_game", "possession_share"),
    "shot_context": ("shots_for_per_game", "shots_against_per_game", "shots_on_target_for", "shots_on_target_against", "shots"),
    "xg_context": ("xg_for", "xg_against", "expected_goals_for", "expected_goals_against", "xg_per_shot"),
    "non_penalty_xg_context": ("non_penalty_xg_for", "non_penalty_xg_against", "npxg_for", "npxg_against"),
    "big_chance_context": ("big_chances_for", "big_chances_against", "box_entries_for", "box_entries_against", "penalty_area_touches_for"),
    "possession_context": ("possession_share", "field_tilt", "final_third_entries", "passes_into_final_third"),
    "field_tilt_context": ("field_tilt", "territorial_share", "final_third_entries"),
    "progressive_action_context": ("progressive_passes", "progressive_carries", "passes_into_penalty_area", "carries_into_box"),
    "possession_value_context": ("possession_value_for", "possession_value_against", "obv_for", "vaep_for"),
    "expected_threat_context": ("expected_threat_for", "expected_threat_against", "xT_created", "xT_received"),
    "obv_vaep_context": ("obv_for", "obv_against", "vaep_for", "vaep_against", "possession_value_added"),
    "pressing_context": ("pressures", "successful_pressures", "pressures_final_third", "high_press_rate", "ppda_proxy"),
    "counter_pressing_context": ("counterpress_regains", "counter_pressing_rate", "pressure_regain_time"),
    "transition_context": ("counterattack_xg", "direct_attacks", "transition_xg_for", "transition_xg_against", "transition_shots_for"),
    "set_piece_context": ("set_piece_xg_for", "set_piece_xg_against", "corner_rate_for", "penalty_rate_for", "set_piece_taker_status"),
    "goalkeeper_context": ("confirmed_starter", "projected_starter", "goalkeeper_status", "save_percentage", "post_shot_xg_allowed", "goals_prevented_proxy"),
    "post_shot_xg_context": ("post_shot_xg_allowed", "goals_prevented_proxy", "psxg_allowed"),
    "lineup_context": ("confirmed_lineup", "projected_lineup", "starting_xi_stability", "key_attacker_absent", "key_defender_absent"),
    "formation_context": ("formation", "attacking_shape", "defensive_shape", "build_up_style", "manager_style_context"),
    "player_role_context": ("role", "player_role", "minutes_projection", "shots", "non_penalty_xg", "progressive_passes", "tackles"),
    "referee_context": ("referee_name", "card_rate", "yellow_card_rate", "foul_rate", "penalty_rate"),
    "card_penalty_context": ("card_rate", "yellow_card_rate", "red_card_rate", "penalty_rate", "player_card_risk"),
    "rest_travel_context": ("days_rest", "rest_days", "travel_distance", "time_zone_change", "fixture_congestion", "midweek_match"),
    "competition_context": ("competition", "fixture_priority", "cup_rotation_context", "league", "derby_or_rivalry_context"),
    "betting_market_context": ("odds", "market_type", "asian_handicap", "total", "team_total", "moneyline"),
    "calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),
    "tracking_context": ("tracking_available", "pitch_control", "off_ball_runs", "defensive_line_height", "compactness", "formation_phase_shape"),
}


def _flatten_contexts(*contexts: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, dict):
            merged.update(context)
    return merged


def evaluate_soccer_data_availability(
    sport: Any = "soccer",
    *,
    market_type: Any = None,
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
) -> dict[str, Any]:
    normalized_sport = normalize_soccer_sport(sport)
    row = _flatten_contexts(
        game_context,
        team_context,
        player_context,
        lineup_context,
        tactical_context,
        possession_value_context,
        shot_quality_context,
        pressing_context,
        transition_context,
        set_piece_context,
        goalkeeper_context,
        referee_context,
        matchup_context,
        availability_context,
        incentive_context,
        calibration_context,
        tracking_context,
        {"market_type": market_type} if market_type else {},
    )
    available = []
    missing = []
    for group, fields in FIELD_GROUPS.items():
        if present_fields(row, fields):
            available.append(group)
        else:
            missing.append(group)
    player_role_available = isinstance(player_context, dict) and bool(present_fields(player_context, FIELD_GROUPS["player_role_context"]))
    tracking_available = isinstance(tracking_context, dict) and bool(present_fields(tracking_context, FIELD_GROUPS["tracking_context"]))
    if not tracking_available and "tracking_context" in available:
        available.remove("tracking_context")
        if "tracking_context" not in missing:
            missing.append("tracking_context")

    if tracking_available:
        data_tier = 4
    elif any(group in available for group in ("possession_value_context", "expected_threat_context", "obv_vaep_context", "pressing_context", "transition_context", "formation_context")) or player_role_available:
        data_tier = 3
    elif any(group in available for group in ("xg_context", "shot_context", "set_piece_context", "referee_context", "big_chance_context", "non_penalty_xg_context")):
        data_tier = 2
    elif any(group in available for group in ("basic_game_context", "team_box_score_context", "lineup_context", "rest_travel_context", "competition_context")):
        data_tier = 1
    else:
        data_tier = 0

    calibration_allowed = "calibration_outcomes" in available
    team_level_allowed = data_tier >= 1
    player_level_allowed = player_role_available
    tactical_level_allowed = any(group in available for group in ("formation_context", "pressing_context", "transition_context", "possession_value_context", "expected_threat_context"))
    tracking_level_allowed = tracking_available
    confirmed_lineup = bool(row.get("confirmed_lineup") is True or str(row.get("confirmed_lineup")).lower() == "true")
    confirmed_keeper = bool(row.get("confirmed_starter") is True or str(row.get("confirmed_starter")).lower() == "true")

    confidence_cap = 20.0
    confidence_reason = "tier_0_no_reliable_soccer_impact_data"
    if data_tier == 1:
        confidence_cap = 42.0
        confidence_reason = "tier_1_basic_team_game_proxy_only"
    elif data_tier == 2:
        confidence_cap = 62.0
        confidence_reason = "tier_2_shot_xg_set_piece_referee_context"
    elif data_tier == 3:
        confidence_cap = 78.0
        confidence_reason = "tier_3_event_possession_value_player_role_context"
    elif data_tier >= 4:
        confidence_cap = 88.0
        confidence_reason = "tier_4_tracking_360_optional"
    if lineup_context is not None and not confirmed_lineup:
        confidence_cap = min(confidence_cap, 66.0)
        confidence_reason = "confirmed_lineup_missing_caps_player_tactical_confidence"
    if goalkeeper_context is not None and not confirmed_keeper:
        confidence_cap = min(confidence_cap, 68.0)
        confidence_reason = "goalkeeper_confirmation_missing_caps_team_total_confidence"
    if not calibration_allowed:
        confidence_cap = min(confidence_cap, 68.0)

    next_data = []
    if data_tier == 0:
        next_data.extend(["basic_game_context", "team_shot_or_xg_context"])
    if data_tier < 2:
        next_data.extend(["xg_for_against", "shots_for_against", "set_piece_context"])
    if data_tier < 3:
        next_data.extend(["expected_threat_or_possession_value", "player_role_context", "formation_or_pressing_context"])
    if data_tier < 4:
        next_data.append("optional_tracking_360_tactical_micro_events")
    if not calibration_allowed:
        next_data.append("settled_outcomes_by_soccer_market_context")

    return finalize_soccer_response(
        {
            "status": "DATA_INSUFFICIENT" if data_tier == 0 else "soccer_data_available",
            "sport": normalized_sport,
            "data_tier": data_tier,
            "tier_name": DATA_TIER_REQUIREMENTS[data_tier]["tier_name"],
            "team_level_allowed": team_level_allowed,
            "player_level_allowed": player_level_allowed,
            "tactical_level_allowed": tactical_level_allowed,
            "tracking_level_allowed": tracking_level_allowed,
            "calibration_allowed": calibration_allowed,
            "available_field_groups": available,
            "missing_field_groups": missing,
            "confidence_cap": confidence_cap,
            "confidence_cap_reason": confidence_reason,
            "no_fabrication": True,
            "xt_not_fabricated": "expected_threat_context" not in available,
            "obv_vaep_not_fabricated": "obv_vaep_context" not in available,
            "tracking_not_required": True,
            "formation_not_fabricated": "formation_context" not in available,
            "confirmed_lineup_required_for_full_confidence": not confirmed_lineup,
            "confirmed_goalkeeper_required_for_full_confidence": not confirmed_keeper,
            "referee_tendency_not_fabricated": "referee_context" not in available,
            "next_data_to_collect": compact_list(next_data, limit=35),
            "data_tier_requirements": DATA_TIER_REQUIREMENTS,
            "recommended_action_adjustment": "DATA_INSUFFICIENT" if data_tier == 0 else "CALIBRATION_ONLY",
        },
        source_payload=row,
    )
