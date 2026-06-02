from __future__ import annotations

from typing import Any

from .tennis_impact_common import (
    CORRECT_SCORE_MARKETS,
    DATA_TIER_REQUIREMENTS,
    PLAYER_PROP_MARKETS,
    TIEBREAK_MARKETS,
    compact_list,
    finalize_tennis_response,
    normalize_tennis_market,
    normalize_tennis_sport,
    present_fields,
)


FIELD_GROUPS: dict[str, tuple[str, ...]] = {
    "basic_match_context": ("tour", "tournament", "event_name", "round", "surface", "best_of"),
    "player_identity_context": ("player_a_name", "player_b_name", "player_a_id", "player_b_id", "player_name", "player_id"),
    "ranking_rating_context": ("ranking_proxy", "player_a_ranking_proxy", "player_b_ranking_proxy", "elo_rating", "rating_proxy"),
    "surface_context": ("surface", "player_a_surface_win_rate", "player_b_surface_win_rate", "surface_win_rate"),
    "best_of_context": ("best_of", "format", "sets_to_win"),
    "serve_summary_context": ("hold_percentage", "service_games_won_rate", "first_serve_percentage", "first_serve_points_won", "second_serve_points_won", "service_points_won", "player_a_hold_percentage", "player_b_hold_percentage"),
    "return_summary_context": ("break_percentage", "return_games_won_rate", "return_points_won", "first_serve_return_points_won", "second_serve_return_points_won", "player_a_break_percentage", "player_b_break_percentage"),
    "hold_break_context": ("hold_percentage", "break_percentage", "player_a_hold_probability", "player_b_hold_probability", "player_a_break_probability", "player_b_break_probability"),
    "ace_double_fault_context": ("ace_rate", "double_fault_rate", "player_a_ace_rate", "player_b_ace_rate", "player_a_double_fault_rate", "player_b_double_fault_rate"),
    "break_point_context": ("break_points_saved", "break_points_converted", "break_points_created_rate", "break_points_faced_rate"),
    "tiebreak_context": ("tiebreak_win_rate", "tiebreak_probability", "first_set_tiebreak_probability", "tiebreaks_played_rate", "player_a_tiebreak_win_rate"),
    "surface_specific_context": ("service_points_won_surface", "return_points_won_surface", "surface_adjusted_hold_rate", "surface_adjusted_break_rate", "player_a_surface_hold_rate", "player_b_surface_break_rate"),
    "point_by_point_context": ("point_by_point", "point_sequence", "points", "point_context"),
    "rally_length_context": ("rally_length_preference", "short_rally_win_rate", "medium_rally_win_rate", "long_rally_win_rate"),
    "pressure_point_context": ("pressure_points_won", "deciding_points_won", "break_points_saved", "pressure_double_fault_rate"),
    "first_set_context": ("first_set_win_rate", "first_set_hold_rate", "first_set_break_rate", "first_set_tiebreak_rate"),
    "deciding_set_context": ("deciding_set_win_rate", "deciding_set_return_points_won"),
    "handedness_context": ("player_a_handedness", "player_b_handedness", "lefty_vs_righty_context"),
    "shot_pattern_context": ("forehand_strength_proxy", "backhand_weakness_proxy", "serve_direction_preference", "rally_directionality", "slice_usage", "topspin_heavy_context"),
    "serve_placement_context": ("serve_placement_wide_rate", "serve_placement_body_rate", "serve_placement_t_rate"),
    "return_position_context": ("return_position", "return_depth_proxy"),
    "movement_fatigue_context": ("movement_load", "sprint_recovery_metrics", "recent_match_minutes", "recent_sets_played", "matches_last_7_days"),
    "injury_retirement_context": ("injury_status", "medical_timeout_recent", "retirement_history", "withdrawal_risk", "retire_or_walkover_risk"),
    "weather_conditions_context": ("temperature", "humidity", "wind_speed", "weather_bucket", "weather_conditions"),
    "indoor_outdoor_context": ("indoor", "outdoor", "roof_status"),
    "court_speed_context": ("court_speed_index", "tournament_surface_speed_proxy"),
    "ball_type_context": ("ball_type",),
    "betting_market_context": ("odds", "price", "market_implied_probability", "line_move"),
    "calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),
    "tracking_context": ("serve_speed_distribution", "serve_speed_average", "return_position", "movement_load", "spin_rates", "ball_striking_speed", "tracking_context"),
}


def _merge(*contexts: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, dict):
            merged.update(context)
    return merged


def evaluate_tennis_data_availability(
    sport: Any = "tennis",
    *,
    market_type: Any = "moneyline",
    match_context: dict[str, Any] | None = None,
    player_a_context: dict[str, Any] | None = None,
    player_b_context: dict[str, Any] | None = None,
    serve_context: dict[str, Any] | None = None,
    return_context: dict[str, Any] | None = None,
    surface_context: dict[str, Any] | None = None,
    format_context: dict[str, Any] | None = None,
    pressure_context: dict[str, Any] | None = None,
    tiebreak_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    conditions_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration_context: dict[str, Any] | None = None,
    point_context: dict[str, Any] | None = None,
    tracking_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_sport = normalize_tennis_sport(sport)
    market = normalize_tennis_market(market_type)
    row = _merge(
        match_context,
        player_a_context,
        player_b_context,
        serve_context,
        return_context,
        surface_context,
        format_context,
        pressure_context,
        tiebreak_context,
        matchup_context,
        conditions_context,
        availability_context,
        incentive_context,
        calibration_context,
        point_context,
        tracking_context,
    )
    available = [group for group, fields in FIELD_GROUPS.items() if present_fields(row, fields)]
    missing = [group for group in FIELD_GROUPS if group not in available]
    has_players = "player_identity_context" in available
    has_match = "basic_match_context" in available
    if not has_players or not has_match:
        tier = 0
    elif any(group in available for group in ("tracking_context", "serve_placement_context", "shot_pattern_context", "return_position_context", "court_speed_context", "ball_type_context")):
        tier = 4
    elif any(group in available for group in ("surface_specific_context", "point_by_point_context", "rally_length_context", "pressure_point_context", "first_set_context", "deciding_set_context", "movement_fatigue_context", "injury_retirement_context")):
        tier = 3
    elif any(group in available for group in ("serve_summary_context", "return_summary_context", "hold_break_context", "ace_double_fault_context", "break_point_context", "tiebreak_context")):
        tier = 2
    else:
        tier = 1
    serve_return_allowed = tier >= 2
    surface_matchup_allowed = tier >= 3 and "surface_context" in available
    point_level_allowed = "point_by_point_context" in available
    tracking_level_allowed = tier >= 4 and "tracking_context" in available
    calibration_allowed = "calibration_outcomes" in available
    confidence_cap = {0: 0.0, 1: 42.0, 2: 62.0, 3: 80.0, 4: 88.0}[tier]
    cap_reasons: list[str] = []
    if not has_players:
        cap_reasons.append("player_identity_missing")
    if not has_match:
        cap_reasons.append("basic_match_context_missing")
    if "surface_context" not in available:
        cap_reasons.append("surface_missing_caps_surface_matchup")
        confidence_cap = min(confidence_cap, 55.0 if tier else 0.0)
    if "best_of_context" not in available and market in CORRECT_SCORE_MARKETS | {"total_sets"}:
        cap_reasons.append("best_of_missing_caps_correct_score_total_sets")
        confidence_cap = min(confidence_cap, 45.0)
    if "injury_retirement_context" not in available:
        cap_reasons.append("injury_retirement_missing_no_health_claim")
    if market in TIEBREAK_MARKETS and "tiebreak_context" not in available:
        cap_reasons.append("tiebreak_context_missing_caps_tiebreak_market")
        confidence_cap = min(confidence_cap, 50.0)
    if market in PLAYER_PROP_MARKETS and tier < 2:
        cap_reasons.append("serve_return_context_missing_for_player_prop")
        confidence_cap = min(confidence_cap, 35.0)
    if not calibration_allowed:
        cap_reasons.append("calibration_outcomes_missing")
    next_data: list[str] = []
    if tier == 0:
        next_data.extend(["player_identity_context", "basic_match_context"])
    if tier < 2:
        next_data.extend(["hold_percentage", "break_percentage", "first_serve_points_won", "return_points_won"])
    if tier < 3:
        next_data.extend(["surface_specific_hold_break", "pressure_points", "first_set_context", "rally_length_context"])
    if tier < 4:
        next_data.extend(["serve_placement_optional", "serve_speed_optional", "shot_pattern_optional", "court_speed_optional"])
    if not calibration_allowed:
        next_data.append("settled_outcomes_by_tour_surface_market_bucket")
    return finalize_tennis_response(
        {
            "status": "tennis_data_availability",
            "sport": normalized_sport,
            "market_type": market,
            "data_tier": tier,
            "tier_name": DATA_TIER_REQUIREMENTS[tier]["tier_name"],
            "player_level_allowed": tier >= 1,
            "serve_return_allowed": serve_return_allowed,
            "surface_matchup_allowed": surface_matchup_allowed,
            "point_level_allowed": point_level_allowed,
            "tracking_level_allowed": tracking_level_allowed,
            "calibration_allowed": calibration_allowed,
            "available_field_groups": available,
            "missing_field_groups": missing,
            "confidence_cap": confidence_cap,
            "confidence_cap_reason": compact_list(cap_reasons, limit=14),
            "no_fabrication": True,
            "next_data_to_collect": compact_list(next_data, limit=24),
            "recommended_review_status": "DATA_INSUFFICIENT" if tier == 0 else "CALIBRATION_ONLY",
        },
        source_payload=row,
    )
