from __future__ import annotations

from typing import Any

from .basketball_player_impact_common import (
    average_present,
    clamp,
    compact_list,
    finalize_safe_response,
    missing_fields,
    percent_score,
    present_fields,
    score_from_range,
    weighted_average,
)


TRACKING_INPUTS = (
    "touches",
    "frontcourt_touches",
    "time_of_possession",
    "average_seconds_per_touch",
    "drives",
    "drive_points",
    "drive_assists",
    "paint_touches",
    "elbow_touches",
    "post_touches",
    "catch_and_shoot_attempts",
    "pull_up_attempts",
    "potential_assists",
    "secondary_assists",
    "passes_made",
    "passes_received",
    "rebound_chances",
    "contested_rebound_chances",
    "box_outs",
    "screen_assists",
    "distance_traveled",
    "average_speed",
    "rim_pressure_score",
    "spacing_gravity_score",
    "screen_gravity_score",
    "roll_gravity_score",
    "shot_contest_quality",
    "defensive_matchup_difficulty",
    "help_defense_impact",
    "opponent_field_goal_impact",
    "deflections",
    "loose_balls_recovered",
    "charges_drawn",
)


def evaluate_tracking_opportunity(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    present = present_fields(source, TRACKING_INPUTS)
    missing = missing_fields(source, TRACKING_INPUTS)
    if not present:
        return finalize_safe_response(
            {
                "tracking_opportunity_score": 0.0,
                "touch_opportunity_score": 0.0,
                "creation_opportunity_score": 0.0,
                "assist_opportunity_score": 0.0,
                "rebound_opportunity_score": 0.0,
                "shooting_opportunity_score": 0.0,
                "rim_pressure_score": 0.0,
                "spacing_gravity_score": 0.0,
                "defensive_tracking_score": 0.0,
                "matchup_difficulty_score": 0.0,
                "tracking_confidence": 0.0,
                "tracking_status": "missing",
                "tracking_missing_inputs": list(TRACKING_INPUTS),
            },
            source_payload=source,
        )

    touch_score = weighted_average(
        (
            (score_from_range(source.get("touches"), low=10.0, high=95.0), 1.0),
            (score_from_range(source.get("frontcourt_touches"), low=5.0, high=65.0), 1.0),
            (score_from_range(source.get("time_of_possession"), low=0.5, high=9.0), 0.8),
            (score_from_range(source.get("average_seconds_per_touch"), low=0.7, high=6.0), 0.3),
        )
    )
    creation_score = weighted_average(
        (
            (score_from_range(source.get("drives"), low=0.0, high=24.0), 1.0),
            (score_from_range(source.get("drive_points"), low=0.0, high=18.0), 0.6),
            (score_from_range(source.get("drive_assists"), low=0.0, high=8.0), 0.4),
            (score_from_range(source.get("paint_touches"), low=0.0, high=20.0), 0.7),
            (score_from_range(source.get("elbow_touches"), low=0.0, high=12.0), 0.4),
            (score_from_range(source.get("post_touches"), low=0.0, high=12.0), 0.45),
            (percent_score(source.get("rim_pressure_score")), 0.8),
            (percent_score(source.get("screen_gravity_score")), 0.35),
            (percent_score(source.get("roll_gravity_score")), 0.35),
        )
    )
    assist_score = weighted_average(
        (
            (score_from_range(source.get("potential_assists"), low=0.0, high=18.0), 1.1),
            (score_from_range(source.get("secondary_assists"), low=0.0, high=5.0), 0.4),
            (score_from_range(source.get("passes_made"), low=5.0, high=85.0), 0.6),
            (score_from_range(source.get("passes_received"), low=5.0, high=85.0), 0.45),
            (touch_score, 0.6),
        )
    )
    rebound_score = weighted_average(
        (
            (score_from_range(source.get("rebound_chances"), low=0.0, high=22.0), 1.0),
            (score_from_range(source.get("contested_rebound_chances"), low=0.0, high=12.0), 0.7),
            (score_from_range(source.get("box_outs"), low=0.0, high=10.0), 0.4),
        )
    )
    shooting_score = weighted_average(
        (
            (score_from_range(source.get("catch_and_shoot_attempts"), low=0.0, high=12.0), 0.9),
            (score_from_range(source.get("pull_up_attempts"), low=0.0, high=12.0), 0.8),
            (touch_score, 0.35),
            (percent_score(source.get("spacing_gravity_score")), 0.6),
        )
    )
    defensive_score = weighted_average(
        (
            (percent_score(source.get("shot_contest_quality")), 0.7),
            (percent_score(source.get("help_defense_impact")), 0.7),
            (percent_score(source.get("opponent_field_goal_impact")), 0.5),
            (score_from_range(source.get("deflections"), low=0.0, high=8.0), 0.5),
            (score_from_range(source.get("loose_balls_recovered"), low=0.0, high=5.0), 0.35),
            (score_from_range(source.get("charges_drawn"), low=0.0, high=2.0), 0.25),
        )
    )
    matchup_difficulty = percent_score(source.get("defensive_matchup_difficulty"))
    total = weighted_average(
        (
            (touch_score, 1.0),
            (creation_score, 1.0),
            (assist_score, 0.8),
            (rebound_score, 0.65),
            (shooting_score, 0.75),
            (defensive_score, 0.75),
            (percent_score(source.get("rim_pressure_score")), 0.4),
            (percent_score(source.get("spacing_gravity_score")), 0.35),
        )
    )
    status = "ok" if len(present) >= 14 else "partial"
    confidence = clamp(20.0 + min(len(present) / len(TRACKING_INPUTS), 1.0) * 75.0)

    return finalize_safe_response(
        {
            "tracking_opportunity_score": round(clamp(total or 0.0), 2),
            "touch_opportunity_score": round(clamp(touch_score or 0.0), 2),
            "creation_opportunity_score": round(clamp(creation_score or 0.0), 2),
            "assist_opportunity_score": round(clamp(assist_score or 0.0), 2),
            "rebound_opportunity_score": round(clamp(rebound_score or 0.0), 2),
            "shooting_opportunity_score": round(clamp(shooting_score or 0.0), 2),
            "rim_pressure_score": round(clamp(percent_score(source.get("rim_pressure_score")) or 0.0), 2),
            "spacing_gravity_score": round(clamp(percent_score(source.get("spacing_gravity_score")) or 0.0), 2),
            "defensive_tracking_score": round(clamp(defensive_score or 0.0), 2),
            "matchup_difficulty_score": round(clamp(matchup_difficulty or 0.0), 2),
            "tracking_confidence": round(confidence, 2),
            "tracking_status": status,
            "tracking_missing_inputs": compact_list(missing, limit=35),
        },
        source_payload=source,
    )
