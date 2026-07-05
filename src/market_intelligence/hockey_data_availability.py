from __future__ import annotations

from typing import Any

from .hockey_impact_common import (
    DATA_TIER_REQUIREMENTS,
    compact_list,
    finalize_hockey_response,
    normalize_hockey_sport,
    present_fields,
)


FIELD_GROUPS: dict[str, tuple[str, ...]] = {
    "basic_game_context": (
        "team",
        "opponent",
        "home_team",
        "away_team",
        "home_away",
        "game_date",
        "season",
        "market_type",
    ),
    "team_box_score_context": (
        "goals_for_per_game",
        "goals_against_per_game",
        "shots_for_per_game",
        "shots_against_per_game",
        "power_play_percentage",
        "penalty_kill_percentage",
    ),
    "shot_volume_context": ("shots_for_per_game", "shots_against_per_game", "shots_on_goal", "first_period_shot_rate"),
    "shot_attempt_context": (
        "shot_attempts_for_per_game",
        "shot_attempts_against_per_game",
        "unblocked_attempts_for_per_game",
        "unblocked_attempts_against_per_game",
    ),
    "possession_context": ("shot_share", "xg_share", "corsi_for_percentage", "fenwick_for_percentage"),
    "expected_goal_context": (
        "expected_goals_for_per_game",
        "expected_goals_against_per_game",
        "xg_share",
        "individual_expected_goals",
        "line_xg_share",
        "defensive_pair_xg_share",
    ),
    "scoring_chance_context": ("scoring_chances_for", "scoring_chances_against", "scoring_chance_rate"),
    "high_danger_context": (
        "high_danger_chances_for",
        "high_danger_chances_against",
        "high_danger_xg_for",
        "high_danger_xg_against",
        "high_danger_attempt_rate",
    ),
    "first_period_context": ("first_period_shot_rate", "first_period_xg_rate", "first_period_pace_proxy"),
    "skater_role_context": (
        "role",
        "skater_role",
        "individual_shot_attempts",
        "shots_on_goal_rate",
        "power_play_time_on_ice",
        "even_strength_time_on_ice",
    ),
    "goalie_context": (
        "goalie_status",
        "confirmed_starter",
        "projected_starter",
        "save_percentage",
        "recent_save_percentage",
        "goals_saved_above_expected_proxy",
    ),
    "confirmed_goalie_context": ("confirmed_starter", "confirmed_goalie", "confirmed_goalie_name"),
    "line_context": ("confirmed_lines", "projected_lines", "line_xg_share", "line_shot_share", "line_time_on_ice"),
    "defensive_pair_context": (
        "defensive_pair_xg_share",
        "defensive_pair_shot_share",
        "defensive_pair_time_on_ice",
        "defensive_pair_continuity",
    ),
    "special_teams_context": (
        "power_play_percentage",
        "penalty_kill_percentage",
        "power_play_xg_rate",
        "penalty_kill_xg_against_rate",
        "power_play_unit_role",
        "penalty_kill_unit_role",
    ),
    "zone_entry_context": ("controlled_entry_rate", "controlled_entry_success_rate", "entry_denial_rate"),
    "zone_exit_context": ("controlled_exit_rate", "failed_exit_rate", "zone_exit_success_rate"),
    "transition_context": (
        "rush_chances_for",
        "rush_chances_against",
        "odd_man_rushes_for",
        "odd_man_rushes_against",
        "neutral_zone_turnover_rate",
    ),
    "rush_context": ("rush_chances_for", "rush_chance_creation", "odd_man_rushes_for"),
    "rebound_context": ("rebound_chances_for", "rebound_chances_against", "rebound_creation", "rebound_control_proxy"),
    "forecheck_context": ("forecheck_pressure_rate", "puck_retrieval_rate", "dump_in_retrieval_rate"),
    "slot_chance_context": ("slot_shots_for", "slot_shots_against", "slot_pass_rate"),
    "matchup_context": (
        "matchup_deployment",
        "opponent_top_line_context",
        "opponent_top_pair_context",
        "opponent_shot_suppression",
        "opponent_goalie_quality_proxy",
    ),
    "injury_context": (
        "skater_injury_status",
        "goalie_injury_status",
        "injury_status",
        "scratches_context",
        "top_line_absence",
        "defensive_pair_injury",
    ),
    "rest_travel_context": (
        "rest_days",
        "back_to_back",
        "three_in_four",
        "travel_distance",
        "time_zone_change",
        "overtime_recent",
        "shootout_recent",
    ),
    "betting_market_context": ("odds", "moneyline", "puckline", "total", "team_total", "market_type"),
    "calibration_outcomes": (
        "historical_predictions",
        "settled_outcomes",
        "matched_outcomes_count",
        "final_outcome",
        "outcome",
    ),
    "tracking_context": (
        "tracking_available",
        "controlled_entry_rate",
        "controlled_exit_rate",
        "shift_level_workload",
        "player_speed",
        "deployment_matching",
    ),
}


def _flatten_contexts(*contexts: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, dict):
            merged.update(context)
    return merged


def evaluate_hockey_data_availability(
    sport: Any = "icehockey_nhl",
    *,
    market_type: Any = None,
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
) -> dict[str, Any]:
    normalized_sport = normalize_hockey_sport(sport)
    row = _flatten_contexts(
        game_context,
        team_context,
        skater_context,
        goalie_context,
        line_context,
        pair_context,
        special_teams_context,
        transition_context,
        shot_quality_context,
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

    if "tracking_context" in available or any(group in available for group in ("zone_entry_context", "zone_exit_context", "transition_context", "rush_context", "forecheck_context", "slot_chance_context")):
        data_tier = 4
    elif any(group in available for group in ("expected_goal_context", "line_context", "defensive_pair_context", "goalie_context")):
        data_tier = 3
    elif any(group in available for group in ("shot_attempt_context", "shot_volume_context", "possession_context", "special_teams_context", "scoring_chance_context", "high_danger_context")):
        data_tier = 2
    elif any(group in available for group in ("basic_game_context", "team_box_score_context", "rest_travel_context", "injury_context")):
        data_tier = 1
    else:
        data_tier = 0

    calibration_allowed = "calibration_outcomes" in available
    team_level_allowed = data_tier >= 1
    skater_level_allowed = "skater_role_context" in available or data_tier >= 3 and bool(skater_context)
    goalie_level_allowed = "goalie_context" in available
    line_level_allowed = "line_context" in available or "defensive_pair_context" in available
    tracking_level_allowed = data_tier >= 4 and "tracking_context" in available
    confirmed_goalie = "confirmed_goalie_context" in available

    confidence_cap = 20.0
    confidence_reason = "tier_0_no_reliable_hockey_impact_data"
    if data_tier == 1:
        confidence_cap = 42.0
        confidence_reason = "tier_1_basic_team_game_proxy_only"
    elif data_tier == 2:
        confidence_cap = 60.0
        confidence_reason = "tier_2_shot_volume_possession_proxy"
    elif data_tier == 3:
        confidence_cap = 76.0
        confidence_reason = "tier_3_xg_line_goalie_context"
    elif data_tier >= 4:
        confidence_cap = 86.0
        confidence_reason = "tier_4_tracking_transition_optional"
    if goalie_context and not confirmed_goalie:
        confidence_cap = min(confidence_cap, 68.0)
        confidence_reason = "goalie_unconfirmed_caps_market_confidence"
    if line_context and "line_context" not in available:
        confidence_cap = min(confidence_cap, 64.0)
        confidence_reason = "line_context_missing_or_unconfirmed"
    if not calibration_allowed:
        confidence_cap = min(confidence_cap, 68.0)

    next_data = []
    if data_tier == 0:
        next_data.extend(["basic_game_context", "team_box_score_context"])
    if data_tier < 2:
        next_data.extend(["shot_attempts_for_against", "shot_share", "power_play_penalty_kill_context"])
    if data_tier < 3:
        next_data.extend(["expected_goals_for_against", "confirmed_goalie_status", "line_pair_context"])
    if data_tier < 4:
        next_data.extend(["optional_zone_entry_exit_transition_context"])
    if not calibration_allowed:
        next_data.append("settled_outcomes_by_market_context_bucket")

    result = {
        "status": "DATA_INSUFFICIENT" if data_tier == 0 else "hockey_data_available",
        "sport": normalized_sport,
        "data_tier": data_tier,
        "tier_name": DATA_TIER_REQUIREMENTS[data_tier]["tier_name"],
        "team_level_allowed": team_level_allowed,
        "skater_level_allowed": skater_level_allowed,
        "goalie_level_allowed": goalie_level_allowed,
        "line_level_allowed": line_level_allowed,
        "tracking_level_allowed": tracking_level_allowed,
        "calibration_allowed": calibration_allowed,
        "available_field_groups": available,
        "missing_field_groups": missing,
        "confidence_cap": confidence_cap,
        "confidence_cap_reason": confidence_reason,
        "no_fabrication": True,
        "tracking_not_required": True,
        "zone_entry_exit_not_assumed": "zone_entry_context" not in available and "zone_exit_context" not in available,
        "gsax_not_inferred_from_save_percentage": True,
        "confirmed_goalie_required_for_full_confidence": not confirmed_goalie,
        "line_pair_context_not_fabricated": "line_context" not in available and "defensive_pair_context" not in available,
        "next_data_to_collect": compact_list(next_data, limit=30),
        "data_tier_requirements": DATA_TIER_REQUIREMENTS,
        "recommended_action_adjustment": "DATA_INSUFFICIENT" if data_tier == 0 else "CALIBRATION_ONLY",
    }
    return finalize_hockey_response(result, source_payload=row)
