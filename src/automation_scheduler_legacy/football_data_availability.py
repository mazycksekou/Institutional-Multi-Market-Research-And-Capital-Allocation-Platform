from __future__ import annotations

from typing import Any

from .football_impact_schema import (
    DATA_TIER_REQUIREMENTS,
    compact_list,
    finalize_football_response,
    normalize_football_sport,
    present_fields,
)


FIELD_GROUPS: dict[str, tuple[str, ...]] = {
    "basic_game_context": (
        "team",
        "opponent",
        "home_away",
        "week",
        "season",
        "game_total",
        "spread",
        "moneyline",
        "implied_team_total",
        "points_per_game",
        "yards_per_game",
    ),
    "play_by_play": (
        "epa_per_play",
        "success_rate",
        "explosive_play_rate",
        "negative_play_rate",
        "early_down_success_rate",
        "third_down_success_rate",
        "fourth_down_success_rate",
        "yards_per_play",
        "plays_sample_size",
    ),
    "drive_context": (
        "drive_success_rate",
        "points_per_drive",
        "finishing_drives_points_per_trip",
        "red_zone_epa",
        "red_zone_td_rate",
        "field_position_value",
        "drives_sample_size",
    ),
    "player_participation": (
        "player_id",
        "player_name",
        "role",
        "position",
        "offensive_snap_count",
        "defensive_snap_count",
        "routes_run",
        "carries",
        "targets",
        "dropbacks",
    ),
    "snap_share": ("snap_share_recent", "snap_share", "offensive_snap_share", "defensive_snap_share"),
    "route_share": ("route_share_recent", "route_share", "route_participation"),
    "target_share": ("target_share_recent", "target_share", "first_read_target_proxy"),
    "carry_share": ("carry_share_recent", "carry_share", "rush_attempt_share"),
    "pressure_context": (
        "pressure_rate",
        "pressure_to_sack_rate",
        "pressure_allowed_proxy",
        "pass_rush_win_proxy",
        "qb_pressure_rate",
        "opponent_pressure_rate",
    ),
    "coverage_context": (
        "coverage_shell",
        "man_coverage_rate",
        "zone_coverage_rate",
        "two_high_rate",
        "single_high_rate",
        "separation_allowed_proxy",
        "coverage_target_rate",
    ),
    "offensive_line_context": (
        "offensive_line_continuity",
        "pressure_allowed_proxy",
        "sack_allowed_proxy",
        "run_block_success_proxy",
        "ol_injuries",
    ),
    "defensive_line_context": (
        "defensive_line_continuity",
        "defensive_line_pressure_rate",
        "dl_pressure_rate",
        "run_stop_rate",
        "havoc_rate",
    ),
    "weather_context": ("weather_risk", "wind_mph", "precipitation_risk", "temperature", "altitude"),
    "injury_context": ("injury_status", "practice_status", "starting_qb_status", "teammate_injuries"),
    "depth_chart_context": ("depth_chart_role", "backup_qb_quality_proxy", "starter_status", "depth_chart_status"),
    "betting_market_context": (
        "odds",
        "spread",
        "total",
        "team_total",
        "line_move",
        "implied_probability",
    ),
    "calibration_outcomes": (
        "historical_predictions",
        "settled_outcomes",
        "matched_outcomes_count",
        "final_outcome",
        "outcome",
    ),
    "tracking_context": (
        "separation_proxy",
        "expected_yac",
        "yac_over_expected_proxy",
        "rushing_yards_over_expected",
        "defenders_in_box",
        "time_to_throw",
        "coverage_shell_detail",
        "tracking_available",
    ),
}


def _flatten_contexts(*contexts: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, dict):
            merged.update(context)
    return merged


def evaluate_football_data_availability(
    sport: Any = "americanfootball_nfl",
    *,
    team_context: dict[str, Any] | None = None,
    player_context: dict[str, Any] | None = None,
    play_drive_context: dict[str, Any] | None = None,
    personnel_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration_context: dict[str, Any] | None = None,
    tracking_context: dict[str, Any] | None = None,
    market_type: Any = None,
) -> dict[str, Any]:
    normalized_sport = normalize_football_sport(sport)
    row = _flatten_contexts(
        team_context,
        player_context,
        play_drive_context,
        personnel_context,
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

    if "tracking_context" in available:
        data_tier = 4
    elif any(group in available for group in ("player_participation", "snap_share", "route_share", "target_share", "carry_share")):
        data_tier = 3
    elif any(group in available for group in ("play_by_play", "drive_context")):
        data_tier = 2
    elif any(group in available for group in ("basic_game_context", "betting_market_context", "weather_context", "injury_context", "depth_chart_context")):
        data_tier = 1
    else:
        data_tier = 0

    player_level_allowed = data_tier >= 3
    team_level_allowed = data_tier >= 1
    tracking_level_allowed = data_tier >= 4
    calibration_allowed = "calibration_outcomes" in available
    next_data = []
    if data_tier == 0:
        next_data.extend(["basic_game_context", "play_by_play_or_drive_context"])
    if data_tier < 2:
        next_data.extend(["epa_per_play", "success_rate", "points_per_drive", "red_zone_td_rate"])
    if data_tier < 3:
        next_data.extend(["snap_share_recent", "route_share_recent", "target_share_recent", "carry_share_recent"])
    if not calibration_allowed:
        next_data.append("settled_outcomes_by_sport_market_role_context")
    if normalized_sport == "americanfootball_nfl" and data_tier >= 3 and not tracking_level_allowed:
        next_data.append("optional_tracking_context_if_available")
    confidence_cap = 20.0
    confidence_reason = "tier_0_no_reliable_football_impact_data"
    if data_tier == 1:
        confidence_cap = 45.0
        confidence_reason = "tier_1_basic_team_game_proxy_only"
    elif data_tier == 2:
        confidence_cap = 62.0
        confidence_reason = "tier_2_play_drive_team_unit_context"
    elif data_tier == 3:
        confidence_cap = 75.0
        confidence_reason = "tier_3_player_participation_role_context"
    elif data_tier >= 4:
        confidence_cap = 85.0
        confidence_reason = "tier_4_tracking_context_optional"
    if not calibration_allowed:
        confidence_cap = min(confidence_cap, 68.0)

    result = {
        "status": "DATA_INSUFFICIENT" if data_tier == 0 else "football_data_available",
        "sport": normalized_sport,
        "data_tier": data_tier,
        "tier_name": DATA_TIER_REQUIREMENTS[data_tier]["tier_name"],
        "available_field_groups": available,
        "missing_field_groups": missing,
        "player_level_allowed": player_level_allowed,
        "team_level_allowed": team_level_allowed,
        "tracking_level_allowed": tracking_level_allowed,
        "calibration_allowed": calibration_allowed,
        "confidence_cap": confidence_cap,
        "confidence_cap_reason": confidence_reason,
        "no_fabrication": True,
        "next_data_to_collect": compact_list(next_data, limit=20),
        "ncaaf_tracking_not_assumed": normalized_sport == "americanfootball_ncaaf",
        "data_tier_requirements": DATA_TIER_REQUIREMENTS,
        "recommended_action_adjustment": "DATA_INSUFFICIENT" if data_tier == 0 else "CALIBRATION_ONLY",
    }
    return finalize_football_response(result, source_payload=row)
