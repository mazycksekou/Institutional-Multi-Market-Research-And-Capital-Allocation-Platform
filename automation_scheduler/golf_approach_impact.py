from __future__ import annotations

from typing import Any

from .golf_impact_common import categorical_score, clamp, compact_list, finalize_golf_response, missing_fields, percent_score, score_centered, score_from_range, weighted_average


APPROACH_INPUTS = (
    "sg_approach",
    "greens_in_regulation_rate",
    "proximity_total",
    "proximity_50_125",
    "proximity_125_150",
    "proximity_150_175",
    "proximity_175_200",
    "proximity_200_plus",
    "long_iron_skill",
    "wedge_skill",
    "approach_from_rough_skill",
    "approach_from_fairway_skill",
    "par_3_approach_skill",
    "par_4_approach_skill",
    "par_5_layup_or_go_for_green_context",
    "course_approach_distance_distribution",
    "green_size",
    "green_firmness",
    "wind_adjusted_approach_skill",
)


def _green_size_score(value: Any) -> float | None:
    return categorical_score(value, {"small": 30.0, "below_average": 38.0, "medium": 55.0, "average": 55.0, "large": 78.0, "very_large": 88.0})


def _firmness_score(value: Any) -> float | None:
    return categorical_score(value, {"soft": 25.0, "average": 50.0, "medium": 50.0, "firm": 72.0, "very_firm": 88.0})


def _bucket_fit(source: dict[str, Any]) -> tuple[float | None, bool]:
    buckets = {
        "50_125": score_from_range(source.get("proximity_50_125"), low=24.0, high=12.0),
        "125_150": score_from_range(source.get("proximity_125_150"), low=33.0, high=20.0),
        "150_175": score_from_range(source.get("proximity_150_175"), low=42.0, high=27.0),
        "175_200": score_from_range(source.get("proximity_175_200"), low=52.0, high=34.0),
        "200_plus": score_from_range(source.get("proximity_200_plus"), low=66.0, high=44.0),
    }
    long_iron = percent_score(source.get("long_iron_skill"))
    wedge = percent_score(source.get("wedge_skill"))
    if buckets["50_125"] is None:
        buckets["50_125"] = wedge
    if buckets["175_200"] is None:
        buckets["175_200"] = long_iron
    if buckets["200_plus"] is None:
        buckets["200_plus"] = long_iron
    distribution = source.get("course_approach_distance_distribution")
    if not isinstance(distribution, dict):
        return None, False
    parts = []
    for bucket, score in buckets.items():
        if score is not None:
            parts.append((score, float(distribution.get(bucket, distribution.get(bucket.replace("_", "-"), 0.0)) or 0.0)))
    return weighted_average(parts), bool(parts)


def evaluate_golf_approach_impact(row: dict[str, Any] | None = None, *, course_fit_allowed: bool = False) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    sg_app = score_centered(source.get("sg_approach"), center=0.0, span=1.0)
    gir = score_from_range(source.get("greens_in_regulation_rate"), low=0.58, high=0.74)
    prox = score_from_range(source.get("proximity_total"), low=42.0, high=28.0)
    bucket_fit, bucket_supported = _bucket_fit(source)
    long_iron = percent_score(source.get("long_iron_skill"))
    wedge = percent_score(source.get("wedge_skill"))
    rough = percent_score(source.get("approach_from_rough_skill"))
    fairway = percent_score(source.get("approach_from_fairway_skill"))
    green_size = _green_size_score(source.get("green_size"))
    firmness = _firmness_score(source.get("green_firmness"))
    wind = percent_score(source.get("wind_adjusted_approach_skill"))
    approach = weighted_average(((sg_app, 0.85), (prox, 0.45), (gir, 0.25), (bucket_fit, 0.45), (long_iron, 0.25), (wedge, 0.25), (rough, 0.2), (fairway, 0.2), (wind, 0.2)))
    course_fit = weighted_average(((bucket_fit, 0.55), (long_iron, 0.25), (wedge, 0.25), (rough, 0.25), (green_size, 0.2), (100.0 - firmness if firmness is not None else None, 0.1), (wind, 0.25)))
    scoring = weighted_average(((approach, 0.55), (bucket_fit, 0.35), (gir, 0.35), (wedge, 0.25), (long_iron, 0.2)))
    no_bet: list[str] = []
    if sg_app is None and gir is not None:
        no_bet.append("gir_alone_does_not_fabricate_sg_approach")
    if not bucket_supported:
        no_bet.append("approach_distance_bucket_fit_requires_player_and_course_buckets")
    if not course_fit_allowed:
        no_bet.append("course_architecture_missing_caps_approach_fit")
    if firmness is not None and wind is None:
        no_bet.append("firm_green_or_wind_context_caps_approach_confidence")
    return finalize_golf_response(
        {
            "approach_score": round(clamp(approach or 0.0), 2),
            "distance_bucket_fit_score": round(clamp(bucket_fit or 0.0), 2),
            "proximity_score": round(clamp(prox or 0.0), 2),
            "gir_relevance_score": round(clamp(gir or 0.0), 2),
            "scoring_opportunity_score": round(clamp(scoring or 0.0), 2),
            "course_approach_fit_score": round(clamp(course_fit or 0.0), 2),
            "approach_prop_relevance": round(clamp(weighted_average(((approach, 0.55), (gir, 0.35), (course_fit, 0.25))) or 0.0), 2),
            "sg_approach_fabricated": False,
            "distance_bucket_fit_supported": bucket_supported,
            "missing_inputs": compact_list(missing_fields(source, APPROACH_INPUTS), limit=30),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )
