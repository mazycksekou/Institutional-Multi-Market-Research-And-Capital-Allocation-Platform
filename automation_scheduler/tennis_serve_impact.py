from __future__ import annotations

from typing import Any

from .tennis_impact_common import avg_prefixed, clamp, compact_list, finalize_tennis_response, missing_fields, percent_score, score_from_range, weighted_average


SERVE_INPUTS = (
    "hold_percentage",
    "service_games_won_rate",
    "first_serve_percentage",
    "first_serve_points_won",
    "second_serve_points_won",
    "ace_rate",
    "double_fault_rate",
    "service_points_won",
    "service_points_won_surface",
    "serve_rating_proxy",
    "first_serve_in_pressure",
    "second_serve_points_won_pressure",
    "break_points_saved",
    "break_points_faced_rate",
    "service_game_volatility",
    "first_set_hold_rate",
    "tiebreak_service_points_won",
    "serve_speed_average",
    "serve_speed_first",
    "serve_speed_second",
    "serve_placement_wide_rate",
    "serve_placement_body_rate",
    "serve_placement_t_rate",
    "serve_plus_one_success",
    "surface_adjusted_hold_rate",
    "indoor_hold_rate",
    "outdoor_hold_rate",
    "sample_size",
)


def _score_rate(row: dict[str, Any], base: str, *, low: float, high: float, inverse: bool = False) -> float | None:
    return score_from_range(avg_prefixed(row, base), low=low, high=high, inverse=inverse)


def evaluate_tennis_serve_impact(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    hold = _score_rate(source, "hold_percentage", low=0.62, high=0.88) or _score_rate(source, "hold_probability", low=0.62, high=0.88)
    service_games = _score_rate(source, "service_games_won_rate", low=0.62, high=0.88)
    first_pct = _score_rate(source, "first_serve_percentage", low=0.52, high=0.70)
    first_won = _score_rate(source, "first_serve_points_won", low=0.62, high=0.80)
    second_won = _score_rate(source, "second_serve_points_won", low=0.43, high=0.58)
    ace = _score_rate(source, "ace_rate", low=0.025, high=0.14)
    double_fault = _score_rate(source, "double_fault_rate", low=0.015, high=0.08)
    service_points = _score_rate(source, "service_points_won", low=0.56, high=0.70)
    surface = _score_rate(source, "service_points_won_surface", low=0.56, high=0.70) or _score_rate(source, "surface_adjusted_hold_rate", low=0.62, high=0.88)
    pressure_first = _score_rate(source, "first_serve_in_pressure", low=0.50, high=0.70)
    pressure_second = _score_rate(source, "second_serve_points_won_pressure", low=0.40, high=0.58)
    bp_save = _score_rate(source, "break_points_saved", low=0.50, high=0.72)
    bp_faced_risk = _score_rate(source, "break_points_faced_rate", low=0.40, high=0.12)
    volatility = _score_rate(source, "service_game_volatility", low=0.0, high=1.0) or 100.0 - (bp_faced_risk if bp_faced_risk is not None else 50.0)
    first_set_hold = _score_rate(source, "first_set_hold_rate", low=0.62, high=0.88)
    tb_service = _score_rate(source, "tiebreak_service_points_won", low=0.55, high=0.75)
    speed = weighted_average(
        (
            (_score_rate(source, "serve_speed_average", low=95.0, high=130.0), 0.35),
            (_score_rate(source, "serve_speed_first", low=105.0, high=138.0), 0.35),
            (_score_rate(source, "serve_speed_second", low=78.0, high=105.0), 0.2),
        )
    )
    placement = weighted_average(
        (
            (percent_score(avg_prefixed(source, "serve_placement_wide_rate")), 0.2),
            (percent_score(avg_prefixed(source, "serve_placement_body_rate")), 0.2),
            (percent_score(avg_prefixed(source, "serve_placement_t_rate")), 0.2),
        )
    )
    plus_one = percent_score(avg_prefixed(source, "serve_plus_one_success"))
    sample = avg_prefixed(source, "sample_size") or 0.0
    limited_proxy = hold is not None and not any(value is not None for value in (first_pct, first_won, second_won, ace, double_fault, service_points, surface))
    insufficient = sample < 20
    hold_stability = weighted_average(((hold, 0.55), (service_games, 0.35), (service_points, 0.35), (100.0 - (volatility or 50.0), 0.2), (first_set_hold, 0.15)))
    first_score = weighted_average(((first_pct, 0.35), (first_won, 0.55), (pressure_first, 0.2), (speed, 0.15), (placement, 0.1)))
    second_score = weighted_average(((second_won, 0.6), (pressure_second, 0.35), (100.0 - (double_fault or 50.0), 0.25)))
    ace_pressure = weighted_average(((ace, 0.55), (first_won, 0.25), (tb_service, 0.25), (speed, 0.2), (surface, 0.2)))
    surface_score = weighted_average(((surface, 0.6), (hold, 0.25), (first_won, 0.2), (plus_one, 0.2)))
    serve = weighted_average(((hold_stability, 0.45), (first_score, 0.35), (second_score, 0.3), (ace_pressure, 0.2), (surface_score, 0.2), (bp_save, 0.2)))
    no_bet: list[str] = []
    if double_fault is not None and double_fault >= 65:
        no_bet.append("double_fault_risk_increases_break_volatility")
    if bp_save is not None and sample < 30:
        no_bet.append("break_points_saved_sample_size_capped")
    confidence_cap = None
    if limited_proxy:
        confidence_cap = "hold_percentage_limited_proxy_confidence_capped"
    if insufficient:
        confidence_cap = "sample_too_small" if not confidence_cap else f"{confidence_cap};sample_too_small"
    return finalize_tennis_response(
        {
            "serve_impact_score": round(clamp(serve or 0.0), 2),
            "hold_stability_score": round(clamp(hold_stability or 0.0), 2),
            "first_serve_score": round(clamp(first_score or 0.0), 2),
            "second_serve_resilience_score": round(clamp(second_score or 0.0), 2),
            "ace_pressure_score": round(clamp(ace_pressure or 0.0), 2),
            "double_fault_risk_score": round(clamp(double_fault or 0.0), 2),
            "break_point_save_score": round(clamp(bp_save or 0.0), 2),
            "service_game_volatility_score": round(clamp(volatility or 0.0), 2),
            "surface_adjusted_serve_score": round(clamp(surface_score or 0.0), 2),
            "ace_prop_relevance": round(clamp(weighted_average(((ace, 0.6), (first_pct, 0.2), (surface, 0.25), (speed, 0.2))) or 0.0), 2),
            "double_fault_prop_relevance": round(clamp(weighted_average(((double_fault, 0.65), (100.0 - (second_score or 50.0), 0.25), (volatility, 0.2))) or 0.0), 2),
            "total_games_modifier": round(clamp(weighted_average(((hold_stability, 0.45), (ace_pressure, 0.25), (100.0 - (double_fault or 0.0), 0.15))) or 0.0), 2),
            "serve_placement_fabricated": False,
            "serve_speed_fabricated": False,
            "confidence_cap_reason": confidence_cap,
            "missing_inputs": compact_list(missing_fields(source, SERVE_INPUTS), limit=35),
            "no_bet_reasons": compact_list(no_bet, limit=10),
            "insufficient_sample": insufficient,
            "limited_proxy": limited_proxy,
        },
        source_payload=source,
    )
