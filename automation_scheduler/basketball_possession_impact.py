from __future__ import annotations

from typing import Any

from .basketball_player_impact_common import (
    average_present,
    clamp,
    compact_list,
    confidence_from_sample,
    finalize_safe_response,
    missing_fields,
    percent_score,
    present_fields,
    safe_float,
    score_centered,
    score_from_range,
    weighted_average,
)


POSSESSION_INPUTS = (
    "possessions_played",
    "on_court_offensive_rating",
    "on_court_defensive_rating",
    "on_court_net_rating",
    "off_court_offensive_rating",
    "off_court_defensive_rating",
    "off_court_net_rating",
    "points_created_per_possession",
    "expected_points_added",
    "expected_points_allowed_impact",
    "shot_quality_created",
    "shot_quality_allowed",
    "turnover_creation_rate",
    "turnover_committed_rate",
    "foul_drawn_rate",
    "foul_committed_rate",
    "offensive_rebound_chance_impact",
    "defensive_rebound_chance_impact",
    "transition_creation_score",
    "half_court_creation_score",
    "clutch_possession_impact",
)


def _rating_diff_score(row: dict[str, Any], on_key: str, off_key: str, *, inverse: bool = False) -> float | None:
    on_value = safe_float(row.get(on_key))
    off_value = safe_float(row.get(off_key))
    if on_value is None or off_value is None:
        return None
    diff = (off_value - on_value) if inverse else (on_value - off_value)
    return score_centered(diff, center=0.0, span=18.0)


def _rate_edge_score(good_value: Any, bad_value: Any, *, span: float = 0.12) -> float | None:
    good = safe_float(good_value)
    bad = safe_float(bad_value)
    if good is None or bad is None:
        return None
    return score_centered(good - bad, center=0.0, span=span)


def evaluate_possession_impact(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    present = present_fields(source, POSSESSION_INPUTS)
    missing = missing_fields(source, POSSESSION_INPUTS)
    if not present:
        return finalize_safe_response(
            {
                "possession_impact_score": 0.0,
                "offensive_possession_impact": 0.0,
                "defensive_possession_impact": 0.0,
                "transition_impact_score": 0.0,
                "half_court_impact_score": 0.0,
                "foul_impact_score": 0.0,
                "turnover_impact_score": 0.0,
                "rebound_possession_impact": 0.0,
                "possession_impact_confidence": 0.0,
                "possession_impact_status": "missing",
                "possession_impact_missing_inputs": list(POSSESSION_INPUTS),
            },
            source_payload=source,
        )

    offensive_rating = _rating_diff_score(source, "on_court_offensive_rating", "off_court_offensive_rating")
    net_rating = _rating_diff_score(source, "on_court_net_rating", "off_court_net_rating")
    points_created = score_from_range(source.get("points_created_per_possession"), low=0.65, high=1.35)
    expected_points = score_centered(source.get("expected_points_added"), center=0.0, span=0.35)
    shot_quality_created = percent_score(source.get("shot_quality_created"))
    transition = percent_score(source.get("transition_creation_score"))
    half_court = percent_score(source.get("half_court_creation_score"))
    offensive = weighted_average(
        (
            (offensive_rating, 1.3),
            (net_rating, 0.8),
            (points_created, 1.3),
            (expected_points, 1.3),
            (shot_quality_created, 0.9),
            (transition, 0.5),
            (half_court, 0.7),
        )
    )

    defensive_rating = _rating_diff_score(source, "on_court_defensive_rating", "off_court_defensive_rating", inverse=True)
    points_allowed = score_centered(source.get("expected_points_allowed_impact"), center=0.0, span=0.30)
    shot_quality_allowed_raw = safe_float(source.get("shot_quality_allowed"))
    if shot_quality_allowed_raw is None:
        shot_quality_allowed = None
    elif 0.0 <= shot_quality_allowed_raw <= 1.0:
        shot_quality_allowed = clamp((1.0 - shot_quality_allowed_raw) * 100.0)
    else:
        shot_quality_allowed = clamp(100.0 - shot_quality_allowed_raw)
    turnover_creation = score_from_range(source.get("turnover_creation_rate"), low=0.0, high=0.12)
    defensive_rebound = score_centered(source.get("defensive_rebound_chance_impact"), center=0.0, span=0.12)
    defensive = weighted_average(
        (
            (defensive_rating, 1.2),
            (points_allowed, 1.1),
            (shot_quality_allowed, 1.0),
            (turnover_creation, 0.7),
            (defensive_rebound, 0.6),
        )
    )

    foul_impact = _rate_edge_score(source.get("foul_drawn_rate"), source.get("foul_committed_rate"), span=0.10)
    turnover_impact = _rate_edge_score(source.get("turnover_creation_rate"), source.get("turnover_committed_rate"), span=0.12)
    rebound_impact = average_present(
        [
            score_centered(source.get("offensive_rebound_chance_impact"), center=0.0, span=0.12),
            score_centered(source.get("defensive_rebound_chance_impact"), center=0.0, span=0.12),
        ]
    )
    clutch = percent_score(source.get("clutch_possession_impact"))
    sample_confidence = confidence_from_sample(source.get("possessions_played"), full_sample=650.0, floor=18.0, cap=94.0)
    minutes_confidence = percent_score(source.get("minutes_stability_score"))
    if minutes_confidence is not None:
        sample_confidence = clamp((sample_confidence * 0.75) + (minutes_confidence * 0.25))

    total = weighted_average(
        (
            (offensive, 1.3),
            (defensive, 1.1),
            (transition, 0.5),
            (half_court, 0.7),
            (foul_impact, 0.35),
            (turnover_impact, 0.45),
            (rebound_impact, 0.45),
            (clutch, 0.25),
        )
    )
    status = "ok" if len(present) >= 11 and source.get("possessions_played") not in (None, "") else "partial"
    if source.get("possessions_played") in (None, ""):
        missing = compact_list(["possessions_played", *missing])

    return finalize_safe_response(
        {
            "possession_impact_score": round(clamp(total or 0.0), 2),
            "offensive_possession_impact": round(clamp(offensive or 0.0), 2),
            "defensive_possession_impact": round(clamp(defensive or 0.0), 2),
            "transition_impact_score": round(clamp(transition or 0.0), 2),
            "half_court_impact_score": round(clamp(half_court or 0.0), 2),
            "foul_impact_score": round(clamp(foul_impact or 0.0), 2),
            "turnover_impact_score": round(clamp(turnover_impact or 0.0), 2),
            "rebound_possession_impact": round(clamp(rebound_impact or 0.0), 2),
            "possession_impact_confidence": round(clamp(sample_confidence), 2),
            "possession_impact_status": status,
            "possession_impact_missing_inputs": compact_list(missing, limit=30),
        },
        source_payload=source,
    )
