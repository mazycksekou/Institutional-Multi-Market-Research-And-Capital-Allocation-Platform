from __future__ import annotations

from typing import Any

from .baseball_impact_common import (
    DATA_TIER_REQUIREMENTS,
    PLAYER_PROP_MARKETS,
    TEAM_MARKETS,
    compact_list,
    finalize_baseball_response,
    normalize_baseball_market,
    normalize_baseball_sport,
    present_fields,
)


FIELD_GROUPS: dict[str, tuple[str, ...]] = {
    "basic_game_context": ("team", "opponent", "home_team", "away_team", "park", "game_date", "runs_scored_per_game", "runs_allowed_per_game"),
    "probable_pitcher_context": ("probable_pitcher", "probable_pitcher_name", "confirmed_starter", "starter_status"),
    "batting_order_context": ("confirmed_lineup", "projected_lineup", "batting_order", "lineup_slot"),
    "handedness_context": ("pitcher_handedness", "batter_handedness", "handedness"),
    "platoon_context": ("platoon_split_woba", "platoon_split_xwoba", "team_platoon_woba", "pitcher_platoon_split"),
    "team_box_score_context": ("runs_scored_per_game", "runs_allowed_per_game", "team_woba", "team_iso", "team_k_rate", "team_bb_rate"),
    "pitcher_box_score_context": ("starter_era_proxy", "starter_fip_proxy", "k_rate", "bb_rate", "hr_per_9_proxy", "innings_per_start"),
    "hitter_box_score_context": ("k_rate", "bb_rate", "iso", "xba", "xslg", "lineup_slot", "plate_appearances_projection"),
    "splits_context": ("platoon_split_woba", "platoon_split_xwoba", "pitcher_split_woba_allowed", "hitter_splits"),
    "pitch_mix_context": ("pitch_mix", "pitch_type_run_values", "pitcher_pitch_type_matchup", "breaking_ball_usage"),
    "pitch_level_context": ("pitch_run_value", "whiff_rate", "chase_rate", "zone_rate", "called_strike_plus_whiff_proxy"),
    "plate_appearance_context": ("plate_appearance_run_value", "base_out_run_expectancy_delta", "expected_runs_created"),
    "batted_ball_context": ("ground_ball_rate", "fly_ball_rate", "pull_rate", "launch_angle"),
    "contact_quality_context": ("exit_velocity", "average_exit_velocity", "barrel_rate", "hard_hit_rate", "xwoba", "xba", "xslg"),
    "bat_tracking_context": ("bat_speed", "swing_length", "squared_up_rate", "blast_rate", "attack_angle"),
    "pitch_tracking_context": ("pitch_movement_proxy", "spin_rate_proxy", "extension_proxy", "release_point_stability"),
    "catcher_context": ("catcher_framing_proxy", "catcher_pop_time_proxy", "catcher_throwing_score", "catcher_status"),
    "defense_context": ("outs_above_average_proxy", "defensive_runs_saved_proxy", "arm_strength_proxy", "range_score_proxy"),
    "baserunning_context": ("sprint_speed", "stolen_base_attempt_rate", "stolen_base_success_rate", "extra_base_taken_rate"),
    "bullpen_context": ("bullpen_era_proxy", "bullpen_fip_proxy", "bullpen_recent_pitch_count", "closer_available", "unavailable_relievers"),
    "park_context": ("park_factor", "home_run_factor", "run_factor", "handedness_park_factor", "altitude"),
    "weather_context": ("wind_speed", "wind_direction", "temperature", "humidity", "precipitation_risk", "air_density_proxy"),
    "roof_context": ("roof_status",),
    "umpire_context": ("umpire_zone_size_proxy", "umpire_k_rate_proxy", "umpire_walk_rate_proxy", "umpire_over_under_tendency_proxy"),
    "betting_market_context": ("odds", "total", "runline", "team_total", "line_move"),
    "calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),
}


def _merge(*contexts: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, dict):
            merged.update(context)
    return merged


def evaluate_baseball_data_availability(
    sport: Any = "baseball_mlb",
    *,
    market_type: Any = "moneyline",
    game_context: dict[str, Any] | None = None,
    team_context: dict[str, Any] | None = None,
    pitcher_context: dict[str, Any] | None = None,
    batter_context: dict[str, Any] | None = None,
    lineup_context: dict[str, Any] | None = None,
    bullpen_context: dict[str, Any] | None = None,
    catcher_context: dict[str, Any] | None = None,
    defense_context: dict[str, Any] | None = None,
    baserunning_context: dict[str, Any] | None = None,
    park_weather_context: dict[str, Any] | None = None,
    umpire_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration_context: dict[str, Any] | None = None,
    tracking_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_sport = normalize_baseball_sport(sport)
    market = normalize_baseball_market(market_type)
    row = _merge(
        game_context,
        team_context,
        pitcher_context,
        batter_context,
        lineup_context,
        bullpen_context,
        catcher_context,
        defense_context,
        baserunning_context,
        park_weather_context,
        umpire_context,
        incentive_context,
        calibration_context,
        tracking_context,
    )
    available = [group for group, fields in FIELD_GROUPS.items() if present_fields(row, fields)]
    missing = [group for group in FIELD_GROUPS if group not in available]
    if any(group in available for group in ("bat_tracking_context", "pitch_tracking_context", "catcher_context", "defense_context", "baserunning_context", "umpire_context")):
        tier = 4
    elif any(group in available for group in ("pitch_mix_context", "pitch_level_context", "plate_appearance_context", "batted_ball_context", "contact_quality_context")):
        tier = 3
    elif any(group in available for group in ("pitcher_box_score_context", "hitter_box_score_context", "splits_context", "platoon_context", "bullpen_context", "handedness_context")):
        tier = 2
    elif any(group in available for group in ("basic_game_context", "probable_pitcher_context", "batting_order_context", "team_box_score_context", "park_context", "weather_context", "roof_context", "betting_market_context")):
        tier = 1
    else:
        tier = 0
    pitcher_row = _merge(game_context, pitcher_context)
    batter_row = _merge(game_context, batter_context, lineup_context)
    team_allowed = tier >= 1
    pitcher_allowed = tier >= 2 and any(
        present_fields(pitcher_row, FIELD_GROUPS[group])
        for group in ("probable_pitcher_context", "pitcher_box_score_context", "pitch_level_context", "pitch_mix_context", "pitch_tracking_context")
    )
    batter_allowed = tier >= 2 and any(
        present_fields(batter_row, FIELD_GROUPS[group])
        for group in ("batting_order_context", "hitter_box_score_context", "splits_context", "platoon_context", "batted_ball_context", "contact_quality_context", "bat_tracking_context")
    )
    tracking_allowed = tier >= 4
    calibration_allowed = "calibration_outcomes" in available
    confidence_cap = {0: 0.0, 1: 42.0, 2: 58.0, 3: 76.0, 4: 88.0}[tier]
    cap_reasons = []
    if tier == 0:
        cap_reasons.append("missing_basic_game_context")
    if market in PLAYER_PROP_MARKETS and not (pitcher_allowed or batter_allowed):
        cap_reasons.append("player_context_missing_for_player_prop")
        confidence_cap = min(confidence_cap, 35.0)
    if market in {"total", "team_total", "first_five_total"} and not any(group in available for group in ("park_context", "weather_context", "roof_context", "umpire_context")):
        cap_reasons.append("park_weather_umpire_missing_caps_total_confidence")
        confidence_cap = min(confidence_cap, 52.0)
    if not calibration_allowed:
        cap_reasons.append("calibration_outcomes_missing")
    next_data = []
    if tier == 0:
        next_data.extend(["basic_game_context", "probable_pitcher_context"])
    if tier < 2:
        next_data.extend(["handedness_context", "pitcher_hitter_splits", "bullpen_usage"])
    if tier < 3:
        next_data.extend(["pitch_mix", "whiff_chase_contact_quality", "plate_appearance_run_value"])
    if market in {"total", "team_total", "first_five_total"} and not any(group in available for group in ("park_context", "weather_context", "umpire_context")):
        next_data.extend(["park_factor", "weather_context", "umpire_zone_tendency_if_available"])
    if not calibration_allowed:
        next_data.append("settled_outcomes_by_market_role_context")
    return finalize_baseball_response(
        {
            "status": "baseball_data_availability",
            "sport": normalized_sport,
            "market_type": market,
            "data_tier": tier,
            "tier_name": DATA_TIER_REQUIREMENTS[tier]["tier_name"],
            "team_level_allowed": team_allowed,
            "pitcher_level_allowed": pitcher_allowed,
            "batter_level_allowed": batter_allowed,
            "tracking_level_allowed": tracking_allowed,
            "calibration_allowed": calibration_allowed,
            "available_field_groups": available,
            "missing_field_groups": missing,
            "confidence_cap": confidence_cap,
            "confidence_cap_reason": compact_list(cap_reasons, limit=10),
            "no_fabrication": True,
            "next_data_to_collect": compact_list(next_data, limit=20),
            "recommended_review_status": "DATA_INSUFFICIENT" if tier == 0 else "CALIBRATION_ONLY",
        },
        source_payload=row,
    )
