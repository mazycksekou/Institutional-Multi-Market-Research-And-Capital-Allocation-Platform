from __future__ import annotations

from typing import Any

from .basketball_player_impact_common import (
    boolish,
    clamp,
    compact_list,
    finalize_safe_response,
    missing_fields,
    percent_score,
    present_fields,
    safe_float,
    score_from_range,
    weighted_average,
)


ROLE_BUCKETS = (
    "primary_creator",
    "secondary_creator",
    "spot_up_shooter",
    "movement_shooter",
    "rim_running_big",
    "stretch_big",
    "post_scorer",
    "point_of_attack_defender",
    "help_defender",
    "switchable_wing",
    "rebounder",
    "bench_scorer",
    "low_usage_connector",
    "defensive_specialist",
    "hustle_energy_player",
)

ROLE_INPUTS = (
    "role_label",
    "role_confidence",
    "usage_rate",
    "true_shooting_percentage",
    "effective_field_goal_percentage",
    "assist_rate",
    "turnover_rate",
    "free_throw_rate",
    "shot_attempt_rate",
    "three_point_attempt_rate",
    "rim_attempt_rate",
    "midrange_attempt_rate",
    "points_per_touch",
    "points_per_shot_attempt",
    "assist_to_turnover_ratio",
    "defensive_role",
    "offensive_role",
    "recent_role_change",
    "teammate_absence_usage_shift",
)


def normalize_role(value: Any) -> str | None:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "primary_ball_handler": "primary_creator",
        "lead_guard": "primary_creator",
        "secondary_ball_handler": "secondary_creator",
        "shooter": "spot_up_shooter",
        "catch_and_shoot": "spot_up_shooter",
        "roll_man": "rim_running_big",
        "stretch_5": "stretch_big",
        "3_and_d": "switchable_wing",
        "poa_defender": "point_of_attack_defender",
        "connector": "low_usage_connector",
    }
    role = aliases.get(raw, raw)
    return role if role in ROLE_BUCKETS else None


def infer_player_role(row: dict[str, Any]) -> tuple[str, float]:
    explicit = normalize_role(row.get("role_label") or row.get("offensive_role") or row.get("player_role"))
    explicit_confidence = percent_score(row.get("role_confidence"))
    if explicit:
        return explicit, clamp(explicit_confidence if explicit_confidence is not None else 82.0)

    usage = safe_float(row.get("usage_rate"), 0.0) or 0.0
    assist = safe_float(row.get("assist_rate"), 0.0) or 0.0
    threes = safe_float(row.get("three_point_attempt_rate"), 0.0) or 0.0
    rim = safe_float(row.get("rim_attempt_rate"), 0.0) or 0.0
    rebounds = safe_float(row.get("rebound_chances"), safe_float(row.get("rebound_rate"), 0.0)) or 0.0
    defensive_role = normalize_role(row.get("defensive_role"))

    if usage >= 28 and assist >= 20:
        return "primary_creator", 68.0
    if usage >= 22 and assist >= 14:
        return "secondary_creator", 64.0
    if threes >= 0.42 or threes >= 42:
        return "movement_shooter" if safe_float(row.get("distance_traveled"), 0.0) and safe_float(row.get("distance_traveled"), 0.0) > 2.5 else "spot_up_shooter", 60.0
    if rim >= 0.42 or rim >= 42:
        return "rim_running_big", 60.0
    if rebounds >= 12:
        return "rebounder", 58.0
    if defensive_role:
        return defensive_role, 58.0
    if usage <= 14 and assist >= 8:
        return "low_usage_connector", 54.0
    return "low_usage_connector", 35.0


def evaluate_role_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    present = present_fields(source, ROLE_INPUTS)
    missing = missing_fields(source, ROLE_INPUTS)
    role, confidence = infer_player_role(source)

    usage = score_from_range(source.get("usage_rate"), low=8.0, high=34.0)
    ts = percent_score(source.get("true_shooting_percentage"))
    efg = percent_score(source.get("effective_field_goal_percentage"))
    assist = score_from_range(source.get("assist_rate"), low=0.0, high=42.0)
    turnover_inverse = score_from_range(source.get("turnover_rate"), low=6.0, high=24.0, inverse=True)
    ft = score_from_range(source.get("free_throw_rate"), low=0.0, high=0.55)
    shot_rate = score_from_range(source.get("shot_attempt_rate"), low=6.0, high=28.0)
    threes = score_from_range(source.get("three_point_attempt_rate"), low=0.0, high=0.65)
    rim = score_from_range(source.get("rim_attempt_rate"), low=0.0, high=0.65)
    points_touch = score_from_range(source.get("points_per_touch"), low=0.05, high=0.65)
    points_shot = score_from_range(source.get("points_per_shot_attempt"), low=0.65, high=1.65)
    ast_to = score_from_range(source.get("assist_to_turnover_ratio"), low=0.5, high=4.5)

    if role == "primary_creator":
        usage_efficiency = weighted_average(((usage, 1.0), (ts, 1.0), (assist, 0.9), (turnover_inverse, 0.8), (points_touch, 0.5)))
        role_fit = weighted_average(((usage, 1.0), (assist, 1.0), (shot_rate, 0.6), (ast_to, 0.5)))
    elif role == "secondary_creator":
        usage_efficiency = weighted_average(((usage, 0.8), (ts, 1.1), (assist, 0.8), (turnover_inverse, 0.7), (points_touch, 0.45)))
        role_fit = weighted_average(((usage, 0.7), (assist, 0.7), (threes, 0.35), (ast_to, 0.45)))
    elif role in {"spot_up_shooter", "movement_shooter"}:
        usage_efficiency = weighted_average(((efg, 1.1), (ts, 1.0), (threes, 0.9), (points_shot, 0.9), (turnover_inverse, 0.6)))
        role_fit = weighted_average(((threes, 1.0), (efg, 0.8), (shot_rate, 0.45), (points_shot, 0.5)))
    elif role in {"rim_running_big", "stretch_big", "post_scorer"}:
        big_spacing = threes if role == "stretch_big" else rim
        usage_efficiency = weighted_average(((ts, 1.2), (big_spacing, 0.9), (ft, 0.45), (turnover_inverse, 0.55), (points_shot, 0.8)))
        role_fit = weighted_average(((big_spacing, 1.0), (ts, 0.7), (score_from_range(source.get("rebound_chances"), low=0.0, high=18.0), 0.5)))
    elif role in {"point_of_attack_defender", "help_defender", "switchable_wing", "defensive_specialist"}:
        defensive = weighted_average(((percent_score(source.get("defensive_role_score")), 0.8), (percent_score(source.get("help_defense_impact")), 0.6), (turnover_inverse, 0.5)))
        usage_efficiency = weighted_average(((ts, 0.7), (efg, 0.6), (turnover_inverse, 0.6), (defensive, 1.0)))
        role_fit = weighted_average(((defensive, 1.0), (percent_score(source.get("shot_contest_quality")), 0.5), (percent_score(source.get("defensive_matchup_rating")), 0.5)))
    elif role == "rebounder":
        usage_efficiency = weighted_average(((ts, 0.6), (turnover_inverse, 0.5), (score_from_range(source.get("rebound_chances"), low=0.0, high=22.0), 1.0)))
        role_fit = weighted_average(((score_from_range(source.get("rebound_chances"), low=0.0, high=22.0), 1.0), (score_from_range(source.get("box_outs"), low=0.0, high=10.0), 0.5)))
    elif role == "bench_scorer":
        usage_efficiency = weighted_average(((usage, 0.8), (ts, 0.9), (points_shot, 0.8), (shot_rate, 0.7)))
        role_fit = weighted_average(((usage, 0.8), (shot_rate, 0.8), (points_touch, 0.5)))
    else:
        usage_efficiency = weighted_average(((ts, 1.0), (efg, 0.8), (turnover_inverse, 0.9), (ast_to, 0.7)))
        role_fit = weighted_average(((turnover_inverse, 0.8), (ast_to, 0.7), (ts, 0.7)))

    recent_change = boolish(source.get("recent_role_change")) or abs(safe_float(source.get("teammate_absence_usage_shift"), 0.0) or 0.0) >= 4.0
    role_stability = clamp((confidence * 0.75) + (25.0 if not recent_change else 5.0))
    offensive_score = weighted_average(((usage_efficiency, 1.0), (role_fit, 0.8), (usage, 0.35), (assist, 0.25)))
    defensive_score = weighted_average(
        (
            (percent_score(source.get("defensive_role_score")), 0.8),
            (percent_score(source.get("shot_contest_quality")), 0.5),
            (percent_score(source.get("help_defense_impact")), 0.4),
        )
    )

    if not present:
        missing = list(ROLE_INPUTS)
    return finalize_safe_response(
        {
            "player_role": role,
            "role_confidence": round(clamp(confidence), 2),
            "role_adjusted_efficiency_score": round(clamp(usage_efficiency or 0.0), 2),
            "usage_efficiency_score": round(clamp(usage_efficiency or 0.0), 2),
            "role_fit_score": round(clamp(role_fit or 0.0), 2),
            "role_stability_score": round(clamp(role_stability), 2),
            "offensive_role_score": round(clamp(offensive_score or 0.0), 2),
            "defensive_role_score": round(clamp(defensive_score or 0.0), 2),
            "role_change_detected": bool(recent_change),
            "role_missing_inputs": compact_list(missing, limit=25),
        },
        source_payload=source,
    )
