from __future__ import annotations

from typing import Any

from .golf_impact_common import categorical_score, clamp, compact_list, finalize_golf_response, missing_fields, percent_score, safe_float, score_from_range, weighted_average


COURSE_INPUTS = (
    "course_name",
    "course_length",
    "par",
    "par_3_count",
    "par_4_count",
    "par_5_count",
    "par_4_450_500_count",
    "par_5_reachable_rate",
    "fairway_width",
    "rough_difficulty",
    "green_size",
    "green_speed",
    "green_firmness",
    "grass_type",
    "bunker_density",
    "water_hazard_density",
    "out_of_bounds_risk",
    "elevation",
    "wind_exposure",
    "dogleg_frequency",
    "forced_layup_frequency",
    "approach_distance_distribution",
    "scoring_difficulty",
    "course_history_results",
    "comparable_course_results",
    "course_debut_flag",
)


def _cat(value: Any, mapping: dict[str, float]) -> float | None:
    return categorical_score(value, mapping)


def _history_score(value: Any) -> tuple[float | None, int]:
    if isinstance(value, list):
        starts = len(value)
        finishes = [safe_float(item.get("finish") if isinstance(item, dict) else item) for item in value]
        finishes = [x for x in finishes if x is not None]
        if not finishes:
            return None, starts
        avg = sum(finishes) / len(finishes)
        return score_from_range(avg, low=60.0, high=5.0), starts
    if isinstance(value, dict):
        return percent_score(value.get("score") or value.get("fit_score")), int(safe_float(value.get("starts"), 0) or 0)
    return percent_score(value), int(safe_float(value, 0) or 0)


def evaluate_golf_course_fit_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    length = score_from_range(source.get("course_length"), low=6800.0, high=7600.0)
    par5 = score_from_range(source.get("par_5_reachable_rate"), low=0.05, high=0.55)
    width = _cat(source.get("fairway_width"), {"very_narrow": 20.0, "narrow": 32.0, "medium": 55.0, "average": 55.0, "wide": 78.0, "very_wide": 90.0})
    rough = _cat(source.get("rough_difficulty"), {"low": 20.0, "below_average": 35.0, "average": 50.0, "medium": 50.0, "above_average": 68.0, "high": 82.0, "severe": 92.0, "very_penal": 94.0})
    green_size = _cat(source.get("green_size"), {"small": 30.0, "medium": 55.0, "average": 55.0, "large": 78.0})
    green_speed = _cat(source.get("green_speed"), {"slow": 25.0, "medium": 50.0, "average": 50.0, "fast": 72.0, "very_fast": 86.0})
    firmness = _cat(source.get("green_firmness"), {"soft": 25.0, "average": 50.0, "firm": 72.0, "very_firm": 88.0})
    grass = 60.0 if source.get("grass_type") not in (None, "") else None
    hazard = weighted_average(
        (
            (score_from_range(source.get("bunker_density"), low=0.0, high=100.0) or _cat(source.get("bunker_density"), {"low": 25.0, "below_average": 35.0, "average": 50.0, "moderate": 58.0, "high": 78.0, "severe": 90.0}), 0.35),
            (score_from_range(source.get("water_hazard_density"), low=0.0, high=100.0) or _cat(source.get("water_hazard_density"), {"low": 25.0, "below_average": 35.0, "average": 50.0, "moderate": 60.0, "high": 80.0, "severe": 92.0}), 0.45),
            (score_from_range(source.get("out_of_bounds_risk"), low=0.0, high=100.0) or _cat(source.get("out_of_bounds_risk"), {"low": 20.0, "below_average": 35.0, "average": 50.0, "moderate": 58.0, "high": 82.0, "severe": 94.0}), 0.55),
            (rough, 0.25),
        )
    )
    wind_exposure = _cat(source.get("wind_exposure"), {"low": 25.0, "below_average": 35.0, "moderate": 55.0, "medium": 55.0, "high": 78.0, "exposed": 88.0})
    architecture = weighted_average(((length, 0.25), (width, 0.25), (100.0 - rough if rough is not None else None, 0.2), (green_size, 0.2), (green_speed, 0.15), (100.0 - (hazard or 50.0), 0.25), (par5, 0.2), (wind_exposure, 0.15)))
    course_hist, course_starts = _history_score(source.get("course_history_results"))
    comp_hist, comp_starts = _history_score(source.get("comparable_course_results"))
    course_history_relevance = min(course_starts / 4.0, 1.0) * (course_hist or 0.0)
    comp_fit = min(comp_starts / 5.0, 1.0) * (comp_hist or 0.0)
    distance_bucket = percent_score(source.get("distance_bucket_fit_score"))
    if distance_bucket is None and isinstance(source.get("approach_distance_distribution"), dict):
        distance_bucket = 55.0
    if distance_bucket is None and par5 is not None:
        distance_bucket = par5
    course_fit = weighted_average(((architecture, 0.65), (distance_bucket, 0.35), (grass, 0.2), (course_history_relevance, 0.2), (comp_fit, 0.25)))
    no_bet: list[str] = []
    if source.get("course_name") in (None, ""):
        no_bet.append("course_name_missing_caps_course_fit")
    if architecture is None:
        no_bet.append("course_architecture_missing_caps_course_fit")
    if source.get("grass_type") in (None, ""):
        no_bet.append("grass_type_missing_no_grass_fit_claim")
    if course_starts and course_starts < 3:
        no_bet.append("course_history_small_sample_capped")
    if comp_starts and comp_starts < 4:
        no_bet.append("comparable_course_history_small_sample_capped")
    if source.get("course_debut_flag"):
        no_bet.append("course_debut_increases_uncertainty")
    return finalize_golf_response(
        {
            "course_fit_score": round(clamp(course_fit or 0.0), 2),
            "architecture_fit_score": round(clamp(architecture or 0.0), 2),
            "distance_bucket_fit_score": round(clamp(distance_bucket or 0.0), 2),
            "grass_surface_fit_score": round(clamp(grass or 0.0), 2),
            "hazard_risk_score": round(clamp(hazard or 0.0), 2),
            "comp_course_fit_score": round(clamp(comp_fit or 0.0), 2),
            "course_history_relevance": round(clamp(course_history_relevance), 2),
            "course_architecture_fabricated": False,
            "grass_fit_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, COURSE_INPUTS), limit=35),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )
