from __future__ import annotations

from typing import Any

from .golf_impact_common import (
    DATA_TIER_REQUIREMENTS,
    OUTRIGHT_MARKETS,
    PLAYER_PROP_MARKETS,
    compact_list,
    finalize_golf_response,
    normalize_golf_market,
    normalize_golf_sport,
    present_fields,
)


FIELD_GROUPS: dict[str, tuple[str, ...]] = {
    "basic_tournament_context": ("tournament_name", "course_name", "field_size", "event_name"),
    "player_identity_context": ("player_id", "player_name", "golfer_id", "golfer_name"),
    "ranking_context": ("world_ranking", "owgr", "ranking_proxy", "fedex_rank"),
    "recent_form_context": ("recent_finish_proxy", "recent_sg_total", "recent_results", "basic_round_score_history", "basic_cut_history"),
    "strokes_gained_total_context": ("sg_total", "recent_sg_total", "long_term_sg_total"),
    "strokes_gained_split_context": ("sg_tee_to_green", "sg_off_the_tee", "sg_approach", "sg_around_the_green", "sg_putting"),
    "off_tee_context": ("driving_distance", "driving_accuracy", "driving_dispersion", "fairways_hit_rate", "sg_off_the_tee"),
    "approach_context": ("sg_approach", "greens_in_regulation_rate", "proximity_total", "long_iron_skill", "wedge_skill"),
    "approach_distance_bucket_context": ("proximity_50_125", "proximity_125_150", "proximity_150_175", "proximity_175_200", "proximity_200_plus", "course_approach_distance_distribution"),
    "around_green_context": ("sg_around_the_green", "scrambling_rate", "sand_save_rate", "bunker_proximity"),
    "putting_context": ("sg_putting", "putts_per_round", "three_putt_avoidance", "make_rate_inside_5", "putting_volatility"),
    "scoring_context": ("scoring_average", "round_1_scoring", "weekend_scoring", "par_3_scoring", "par_4_scoring", "par_5_scoring"),
    "birdie_bogey_context": ("birdie_or_better_rate", "bogey_avoidance_rate", "double_bogey_rate"),
    "course_architecture_context": ("course_length", "par", "fairway_width", "rough_difficulty", "green_size", "green_speed", "wind_exposure"),
    "grass_surface_context": ("grass_type", "grass_type_fit", "bermuda_putting_fit", "bentgrass_putting_fit", "poa_putting_fit", "paspalum_putting_fit"),
    "course_history_context": ("course_history_results", "course_history_starts", "course_history_sg"),
    "comparable_course_context": ("comparable_course_results", "comparable_course_starts", "comp_course_fit_score"),
    "weather_context": ("wind_speed", "wind_gust", "rain_probability", "temperature", "weather_bucket"),
    "wind_context": ("wind_speed", "wind_gust", "wind_direction", "wind_skill", "wind_adjusted_approach_skill", "wind_adjusted_driving_skill"),
    "tee_time_wave_context": ("tee_time", "tee_wave", "morning_wave_conditions", "afternoon_wave_conditions", "weather_edge_by_wave"),
    "field_strength_context": ("field_strength", "world_ranking_field_strength_proxy", "top_20_field_count"),
    "cut_rule_context": ("cut_rule", "cut_line_projection", "no_cut_event", "limited_field_event"),
    "matchup_context": ("opponent_sg_total", "matchup_opponent", "relative_sg_total", "relative_course_fit"),
    "injury_context": ("injury_status", "withdrawal_risk", "recent_withdrawal", "illness_context"),
    "travel_fatigue_context": ("travel_distance", "time_zone_change", "consecutive_weeks_played", "previous_week_finish"),
    "betting_market_context": ("odds", "price", "market_implied_probability", "line_move"),
    "calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),
    "simulation_context": ("monte_carlo_inputs", "hole_level_scoring_distribution", "player_volatility_distribution", "field_pairwise_matchup_matrix"),
    "tracking_context": ("shot_level_dispersion", "lie_adjusted_proximity", "strokes_gained_by_hole_type", "shot_shape_tendencies", "wind_adjusted_shot_performance"),
}


def _merge(*contexts: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, dict):
            merged.update(context)
    return merged


def evaluate_golf_data_availability(
    sport: Any = "golf",
    *,
    market_type: Any = "top_20",
    tournament_context: dict[str, Any] | None = None,
    player_context: dict[str, Any] | None = None,
    strokes_gained_context: dict[str, Any] | None = None,
    off_tee_context: dict[str, Any] | None = None,
    approach_context: dict[str, Any] | None = None,
    around_green_context: dict[str, Any] | None = None,
    putting_context: dict[str, Any] | None = None,
    course_context: dict[str, Any] | None = None,
    weather_context: dict[str, Any] | None = None,
    wave_context: dict[str, Any] | None = None,
    field_context: dict[str, Any] | None = None,
    form_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration_context: dict[str, Any] | None = None,
    simulation_context: dict[str, Any] | None = None,
    tracking_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_sport = normalize_golf_sport(sport)
    market = normalize_golf_market(market_type)
    row = _merge(
        tournament_context,
        player_context,
        strokes_gained_context,
        off_tee_context,
        approach_context,
        around_green_context,
        putting_context,
        course_context,
        weather_context,
        wave_context,
        field_context,
        form_context,
        availability_context,
        incentive_context,
        calibration_context,
        simulation_context,
        tracking_context,
    )
    available = [group for group, fields in FIELD_GROUPS.items() if present_fields(row, fields)]
    missing = [group for group in FIELD_GROUPS if group not in available]
    has_player = "player_identity_context" in available
    has_tournament = "basic_tournament_context" in available
    if not has_player:
        tier = 0
    elif any(group in available for group in ("simulation_context", "tracking_context")):
        tier = 4
    elif any(group in available for group in ("course_architecture_context", "grass_surface_context", "course_history_context", "comparable_course_context", "weather_context", "wind_context", "tee_time_wave_context", "field_strength_context", "approach_distance_bucket_context")):
        tier = 3
    elif any(group in available for group in ("strokes_gained_total_context", "strokes_gained_split_context", "off_tee_context", "approach_context", "around_green_context", "putting_context", "scoring_context", "birdie_bogey_context")):
        tier = 2
    elif has_player and (has_tournament or any(group in available for group in ("ranking_context", "recent_form_context", "cut_rule_context", "betting_market_context"))):
        tier = 1
    else:
        tier = 0
    course_fit_allowed = tier >= 3 and "course_architecture_context" in available
    weather_wave_allowed = tier >= 3 and "tee_time_wave_context" in available and ("weather_context" in available or "wind_context" in available)
    simulation_allowed = tier >= 4 and "simulation_context" in available
    calibration_allowed = "calibration_outcomes" in available
    confidence_cap = {0: 0.0, 1: 42.0, 2: 60.0, 3: 78.0, 4: 88.0}[tier]
    cap_reasons: list[str] = []
    if not has_player:
        cap_reasons.append("player_identity_missing")
    if tier == 1:
        cap_reasons.append("strokes_gained_missing_basic_proxy_only")
    if market in OUTRIGHT_MARKETS and "field_strength_context" not in available:
        cap_reasons.append("field_strength_missing_caps_outright_confidence")
        confidence_cap = min(confidence_cap, 45.0)
    if market in PLAYER_PROP_MARKETS and tier < 2:
        cap_reasons.append("player_skill_context_missing_for_player_prop")
        confidence_cap = min(confidence_cap, 35.0)
    if "course_architecture_context" not in available:
        cap_reasons.append("course_architecture_missing_caps_course_fit")
    if "tee_time_wave_context" not in available:
        cap_reasons.append("tee_time_wave_missing_no_wave_edge")
    if not calibration_allowed:
        cap_reasons.append("calibration_outcomes_missing")
    next_data: list[str] = []
    if tier == 0:
        next_data.extend(["player_identity_context", "basic_tournament_context"])
    if tier < 2:
        next_data.extend(["sg_total", "sg_tee_to_green", "sg_approach", "sg_putting", "cut_rate"])
    if tier < 3:
        next_data.extend(["course_architecture", "approach_distance_buckets", "field_strength", "weather_and_tee_wave"])
    if tier < 4:
        next_data.extend(["shot_level_dispersion_optional", "simulation_inputs_optional"])
    if not calibration_allowed:
        next_data.append("settled_outcomes_by_market_course_weather_bucket")
    return finalize_golf_response(
        {
            "status": "golf_data_availability",
            "sport": normalized_sport,
            "market_type": market,
            "data_tier": tier,
            "tier_name": DATA_TIER_REQUIREMENTS[tier]["tier_name"],
            "player_level_allowed": tier >= 1,
            "course_fit_allowed": course_fit_allowed,
            "weather_wave_allowed": weather_wave_allowed,
            "simulation_allowed": simulation_allowed,
            "calibration_allowed": calibration_allowed,
            "available_field_groups": available,
            "missing_field_groups": missing,
            "confidence_cap": confidence_cap,
            "confidence_cap_reason": compact_list(cap_reasons, limit=12),
            "no_fabrication": True,
            "next_data_to_collect": compact_list(next_data, limit=24),
            "recommended_review_status": "DATA_INSUFFICIENT" if tier == 0 else "CALIBRATION_ONLY",
        },
        source_payload=row,
    )
