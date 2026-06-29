from __future__ import annotations

from typing import Any

from .hockey_impact_common import (
    clamp,
    compact_list,
    finalize_hockey_response,
    missing_fields,
    normalize_hockey_role,
    score_centered,
    score_from_range,
    weighted_average,
)


SKATER_FIELDS = (
    "individual_expected_goals",
    "individual_shot_attempts",
    "shots_on_goal_rate",
    "power_play_time_on_ice",
    "even_strength_time_on_ice",
    "line_xg_share",
)


def evaluate_hockey_skater_impact(
    row: dict[str, Any] | None = None,
    *,
    skater_level_allowed: bool = False,
    data_tier: int = 0,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    role = normalize_hockey_role(source.get("role") or source.get("skater_role") or source.get("position"))
    if role == "GOALIE":
        role = "UNKNOWN"
    if not source:
        return finalize_hockey_response(
            {
                "skater_level_allowed": False,
                "skater_role": "UNKNOWN",
                "skater_impact_score": 0.0,
                "skater_market_relevance": 0.0,
                "missing_skater_inputs": list(SKATER_FIELDS),
                "no_bet_reasons": ["missing_skater_context"],
                "confidence_cap_reason": "skater_context_missing",
                "individual_xg_fabricated": False,
                "line_role_fabricated": False,
            },
            source_payload=source,
        )

    shot_generation = weighted_average(
        (
            (score_from_range(source.get("individual_shot_attempts"), low=1, high=10), 0.55),
            (score_from_range(source.get("shots_on_goal_rate"), low=0.5, high=5.5), 0.75),
            (score_from_range(source.get("shot_attempt_rate"), low=3, high=13), 0.35),
            (score_from_range(source.get("high_danger_attempt_rate"), low=0.1, high=2.3), 0.45),
            (score_from_range(source.get("point_shot_rate"), low=0.3, high=5.0), 0.25 if role == "DEFENSEMAN" else 0.0),
        )
    )
    scoring_quality = weighted_average(
        (
            (score_from_range(source.get("individual_expected_goals"), low=0.05, high=0.75), 0.9),
            (score_from_range(source.get("scoring_chance_rate"), low=0.2, high=3.0), 0.45),
            (score_from_range(source.get("high_danger_attempt_rate"), low=0.1, high=2.3), 0.45),
            (score_centered(source.get("line_xg_share"), center=0.5, span=0.2), 0.35),
        )
    )
    playmaking = weighted_average(
        (
            (score_from_range(source.get("primary_shot_assist_rate"), low=0.1, high=3.0), 0.65),
            (score_from_range(source.get("primary_points_rate"), low=0.1, high=1.8), 0.45),
            (score_from_range(source.get("individual_assists_rate"), low=0.05, high=1.2), 0.5),
            (score_from_range(source.get("slot_pass_rate"), low=0.1, high=3.0), 0.35),
        )
    )
    special_teams = weighted_average(
        (
            (score_from_range(source.get("power_play_time_on_ice"), low=0, high=5.0), 0.75),
            (score_from_range(source.get("penalty_kill_time_on_ice"), low=0, high=4.0), 0.35),
            (score_from_range(source.get("special_teams_time_on_ice"), low=0, high=6.0), 0.4),
        )
    )
    transition = weighted_average(
        (
            (score_from_range(source.get("controlled_entry_rate"), low=0.1, high=0.75), 0.45),
            (score_from_range(source.get("zone_entry_success_rate"), low=0.25, high=0.85), 0.45),
            (score_from_range(source.get("zone_exit_success_rate"), low=0.25, high=0.85), 0.35),
            (score_from_range(source.get("rush_chance_creation"), low=0.1, high=2.5), 0.35),
        )
    )
    defensive = weighted_average(
        (
            (score_from_range(source.get("blocked_shots_rate"), low=0.2, high=4.0), 0.5),
            (score_from_range(source.get("defensive_pair_xg_share"), low=0.38, high=0.62), 0.45 if role == "DEFENSEMAN" else 0.15),
            (score_from_range(source.get("entry_denial_rate"), low=0.2, high=0.75), 0.4),
            (score_from_range(source.get("defensive_turnover_rate"), low=0.0, high=0.2, inverse=True), 0.25),
            (score_from_range(source.get("rush_chances_allowed_proxy"), low=0.0, high=3.0, inverse=True), 0.25),
        )
    )
    blocked_relevance = weighted_average(
        (
            (score_from_range(source.get("blocked_shots_rate"), low=0.2, high=4.0), 0.9),
            (score_from_range(source.get("defensive_zone_start_rate"), low=0.25, high=0.75), 0.45),
            (score_from_range(source.get("penalty_kill_time_on_ice"), low=0, high=4.0), 0.35),
            (100.0 if role == "DEFENSEMAN" else 35.0, 0.4),
        )
    )
    toi_score = weighted_average(
        (
            (score_from_range(source.get("even_strength_time_on_ice"), low=8, high=21), 0.5),
            (score_from_range(source.get("power_play_time_on_ice"), low=0, high=5), 0.3),
            (score_from_range(source.get("shot_volume_stability"), low=0.0, high=1.0), 0.4),
        )
    )
    skater_impact = weighted_average(
        (
            (shot_generation, 0.3),
            (scoring_quality, 0.28),
            (playmaking, 0.18),
            (special_teams, 0.12),
            (transition, 0.07),
            (defensive, 0.05),
        )
    )
    relevance = weighted_average(
        (
            (shot_generation, 0.35),
            (scoring_quality, 0.28),
            (special_teams, 0.18),
            (toi_score, 0.25),
            (blocked_relevance if role == "DEFENSEMAN" else 0.0, 0.08),
        )
    )

    missing = missing_fields(source, SKATER_FIELDS)
    no_bet = []
    if not skater_level_allowed:
        no_bet.append("skater_level_data_not_allowed_by_tier")
    if source.get("individual_expected_goals") in (None, ""):
        no_bet.append("individual_xg_missing_not_fabricated")
    if source.get("line_xg_share") in (None, "") and source.get("confirmed_lines") in (None, "", False):
        no_bet.append("line_role_unconfirmed_caps_player_props")
    shooting_regression_caution = False
    recent_pct = source.get("shooting_percentage_recent")
    career_pct = source.get("shooting_percentage_career_proxy")
    if recent_pct not in (None, "") and career_pct not in (None, ""):
        recent = float(recent_pct)
        career = float(career_pct)
        shooting_regression_caution = recent > career + 0.06
        if shooting_regression_caution:
            no_bet.append("shooting_percentage_regression_caution")
    injury = str(source.get("injury_status") or "").lower()
    if injury in {"questionable", "doubtful", "out", "injured"}:
        no_bet.append("skater_injury_uncertainty")

    return finalize_hockey_response(
        {
            "skater_level_allowed": bool(skater_level_allowed),
            "skater_role": role,
            "skater_impact_score": round(clamp(skater_impact or 0.0), 2),
            "shot_generation_score": round(clamp(shot_generation or 0.0), 2),
            "scoring_quality_score": round(clamp(scoring_quality or 0.0), 2),
            "playmaking_score": round(clamp(playmaking or 0.0), 2),
            "special_teams_role_score": round(clamp(special_teams or 0.0), 2),
            "transition_score": round(clamp(transition or 0.0), 2),
            "defensive_impact_score": round(clamp(defensive or 0.0), 2),
            "blocked_shot_relevance_score": round(clamp(blocked_relevance or 0.0), 2),
            "skater_market_relevance": round(clamp(relevance or 0.0), 2),
            "confidence_cap_reason": "line_or_individual_xg_missing" if no_bet else None,
            "shooting_percentage_regression_caution": shooting_regression_caution,
            "missing_skater_inputs": compact_list(missing, limit=25),
            "no_bet_reasons": compact_list(no_bet, limit=20),
            "individual_xg_fabricated": False,
            "line_role_fabricated": False,
            "power_play_unit_fabricated": False,
        },
        source_payload=source,
    )
