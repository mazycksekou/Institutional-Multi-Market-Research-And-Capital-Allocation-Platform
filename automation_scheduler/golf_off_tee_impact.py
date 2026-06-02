from __future__ import annotations

from typing import Any

from .golf_impact_common import categorical_score, clamp, compact_list, finalize_golf_response, missing_fields, score_centered, score_from_range, weighted_average


OFF_TEE_INPUTS = (
    "sg_off_the_tee",
    "driving_distance",
    "driving_accuracy",
    "driving_dispersion",
    "fairways_hit_rate",
    "good_drive_rate",
    "left_miss_rate",
    "right_miss_rate",
    "penalty_off_tee_rate",
    "rough_proximity_penalty",
    "carry_distance",
    "ball_speed_proxy",
    "wind_adjusted_driving_skill",
    "course_fairway_width",
    "rough_difficulty",
    "forced_layup_context",
    "dogleg_fit",
    "driver_usage_rate",
)


def _width_score(value: Any) -> float | None:
    return categorical_score(value, {"very_narrow": 20.0, "narrow": 32.0, "medium": 55.0, "average": 55.0, "wide": 78.0, "very_wide": 90.0})


def _difficulty_score(value: Any) -> float | None:
    return categorical_score(value, {"low": 20.0, "below_average": 35.0, "average": 50.0, "medium": 50.0, "above_average": 68.0, "high": 82.0, "severe": 92.0, "very_penal": 94.0})


def evaluate_golf_off_tee_impact(row: dict[str, Any] | None = None, *, course_fit_allowed: bool = False) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    sg_ott = score_centered(source.get("sg_off_the_tee"), center=0.0, span=0.8)
    distance = weighted_average(
        (
            (score_from_range(source.get("driving_distance"), low=280.0, high=325.0), 0.55),
            (score_from_range(source.get("carry_distance"), low=260.0, high=310.0), 0.35),
            (score_from_range(source.get("ball_speed_proxy"), low=158.0, high=185.0), 0.25),
        )
    )
    accuracy = weighted_average(
        (
            (score_from_range(source.get("driving_accuracy"), low=0.48, high=0.72), 0.45),
            (score_from_range(source.get("fairways_hit_rate"), low=0.48, high=0.72), 0.5),
            (score_from_range(source.get("good_drive_rate"), low=0.62, high=0.82), 0.35),
        )
    )
    dispersion = weighted_average(
        (
            (score_from_range(source.get("driving_dispersion"), low=85.0, high=35.0), 0.65),
            (score_from_range(source.get("left_miss_rate"), low=0.22, high=0.06), 0.25),
            (score_from_range(source.get("right_miss_rate"), low=0.22, high=0.06), 0.25),
        )
    )
    penalty_avoidance = weighted_average(
        (
            (score_from_range(source.get("penalty_off_tee_rate"), low=0.075, high=0.015), 0.75),
            (score_from_range(source.get("rough_proximity_penalty"), low=1.0, high=-0.25), 0.35),
        )
    )
    fairway_width = _width_score(source.get("course_fairway_width") or source.get("fairway_width"))
    rough = _difficulty_score(source.get("rough_difficulty"))
    dogleg = score_from_range(source.get("dogleg_fit"), low=0.0, high=100.0)
    wind_drive = score_from_range(source.get("wind_adjusted_driving_skill"), low=0.0, high=100.0)
    course_fit = weighted_average(
        (
            (distance, 0.35 if fairway_width is None or fairway_width >= 50 else 0.18),
            (accuracy, 0.35 if rough is None or rough < 65 else 0.55),
            (dispersion, 0.45 if fairway_width is None or fairway_width < 60 else 0.25),
            (penalty_avoidance, 0.45 if rough is None or rough >= 55 else 0.25),
            (dogleg, 0.2),
            (wind_drive, 0.25),
        )
    )
    if course_fit is not None and distance is not None and distance >= 70 and rough is not None and rough >= 70:
        course_fit = max(0.0, course_fit - min((rough - 65.0) * 0.35, 12.0))
    off_tee = weighted_average(((sg_ott, 0.7), (distance, 0.35), (accuracy, 0.35), (dispersion, 0.35), (penalty_avoidance, 0.35), (course_fit, 0.25)))
    no_bet: list[str] = []
    if not course_fit_allowed or fairway_width is None or rough is None:
        no_bet.append("course_architecture_missing_caps_off_tee_course_fit")
    if distance and distance >= 70 and fairway_width is not None and fairway_width < 40:
        no_bet.append("narrow_course_reduces_pure_distance_confidence")
    if distance and distance >= 70 and rough is not None and rough >= 70:
        no_bet.append("rough_penalty_reduces_distance_edge_confidence")
    if source.get("driving_dispersion") in (None, "", []):
        no_bet.append("dispersion_not_inferred_from_accuracy")
    return finalize_golf_response(
        {
            "off_tee_score": round(clamp(off_tee or 0.0), 2),
            "distance_advantage_score": round(clamp(distance or 0.0), 2),
            "accuracy_score": round(clamp(accuracy or 0.0), 2),
            "dispersion_risk_score": round(clamp(100.0 - (dispersion or 50.0)), 2),
            "penalty_avoidance_score": round(clamp(penalty_avoidance or 0.0), 2),
            "course_off_tee_fit_score": round(clamp(course_fit or 0.0), 2),
            "driving_prop_relevance": round(clamp(weighted_average(((distance, 0.55), (accuracy, 0.35), (course_fit, 0.25))) or 0.0), 2),
            "course_fit_confidence_capped": not course_fit_allowed or fairway_width is None or rough is None,
            "dispersion_inferred": False,
            "missing_inputs": compact_list(missing_fields(source, OFF_TEE_INPUTS), limit=30),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )
