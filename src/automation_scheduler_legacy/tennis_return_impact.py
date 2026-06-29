from __future__ import annotations

from typing import Any

from .tennis_impact_common import avg_prefixed, clamp, compact_list, finalize_tennis_response, missing_fields, percent_score, score_from_range, weighted_average


RETURN_INPUTS = (
    "break_percentage",
    "return_games_won_rate",
    "return_points_won",
    "first_serve_return_points_won",
    "second_serve_return_points_won",
    "break_points_created_rate",
    "break_points_converted",
    "return_depth_proxy",
    "return_winner_rate",
    "return_error_rate",
    "opponent_second_serve_attack_rate",
    "return_points_won_surface",
    "surface_adjusted_break_rate",
    "first_set_break_rate",
    "deciding_set_return_points_won",
    "pressure_return_points_won",
    "tiebreak_return_points_won",
    "sample_size",
)


def _score_rate(row: dict[str, Any], base: str, *, low: float, high: float, inverse: bool = False) -> float | None:
    return score_from_range(avg_prefixed(row, base), low=low, high=high, inverse=inverse)


def evaluate_tennis_return_impact(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    break_pct = _score_rate(source, "break_percentage", low=0.12, high=0.35) or _score_rate(source, "break_probability", low=0.12, high=0.35)
    return_games = _score_rate(source, "return_games_won_rate", low=0.12, high=0.35)
    return_points = _score_rate(source, "return_points_won", low=0.34, high=0.45)
    first_return = _score_rate(source, "first_serve_return_points_won", low=0.24, high=0.38)
    second_attack = _score_rate(source, "second_serve_return_points_won", low=0.46, high=0.60)
    bp_created = _score_rate(source, "break_points_created_rate", low=0.10, high=0.32)
    bp_converted = _score_rate(source, "break_points_converted", low=0.32, high=0.50)
    depth = percent_score(avg_prefixed(source, "return_depth_proxy"))
    winners = _score_rate(source, "return_winner_rate", low=0.02, high=0.09)
    errors = _score_rate(source, "return_error_rate", low=0.24, high=0.10)
    second_attack_proxy = _score_rate(source, "opponent_second_serve_attack_rate", low=0.0, high=1.0)
    surface = _score_rate(source, "return_points_won_surface", low=0.34, high=0.45) or _score_rate(source, "surface_adjusted_break_rate", low=0.12, high=0.35)
    first_set = _score_rate(source, "first_set_break_rate", low=0.10, high=0.34)
    deciding = _score_rate(source, "deciding_set_return_points_won", low=0.34, high=0.45)
    pressure = _score_rate(source, "pressure_return_points_won", low=0.34, high=0.45)
    tb_return = _score_rate(source, "tiebreak_return_points_won", low=0.32, high=0.45)
    sample = avg_prefixed(source, "sample_size") or 0.0
    limited_proxy = break_pct is not None and not any(value is not None for value in (return_points, first_return, second_attack, bp_created, bp_converted, surface))
    insufficient = sample < 20
    break_threat = weighted_average(((break_pct, 0.55), (return_games, 0.35), (return_points, 0.45), (bp_created, 0.3), (pressure, 0.2)))
    first_score = weighted_average(((first_return, 0.55), (depth, 0.2), (errors, 0.25), (surface, 0.15)))
    second_score = weighted_average(((second_attack, 0.55), (second_attack_proxy, 0.25), (winners, 0.2), (bp_created, 0.2)))
    conversion = weighted_average(((bp_converted, 0.55), (pressure, 0.3), (deciding, 0.2)))
    volatility = weighted_average(((100.0 - (bp_converted or 50.0), 0.3), (break_threat, 0.25), (pressure, 0.2)))
    surface_score = weighted_average(((surface, 0.65), (break_threat, 0.25), (first_set, 0.15)))
    return_score = weighted_average(((break_threat, 0.45), (first_score, 0.25), (second_score, 0.35), (conversion, 0.2), (surface_score, 0.2), (tb_return, 0.1)))
    no_bet: list[str] = []
    if bp_converted is not None and sample < 30:
        no_bet.append("break_point_conversion_sample_size_capped")
    if second_score and second_score >= 65 and break_threat and break_threat >= 55:
        no_bet.append("strong_return_vs_weak_second_serve_affects_handicap_under")
    confidence_cap = None
    if limited_proxy:
        confidence_cap = "break_percentage_limited_proxy_confidence_capped"
    if insufficient:
        confidence_cap = "sample_too_small" if not confidence_cap else f"{confidence_cap};sample_too_small"
    return finalize_tennis_response(
        {
            "return_impact_score": round(clamp(return_score or 0.0), 2),
            "break_threat_score": round(clamp(break_threat or 0.0), 2),
            "first_serve_return_score": round(clamp(first_score or 0.0), 2),
            "second_serve_attack_score": round(clamp(second_score or 0.0), 2),
            "break_point_conversion_score": round(clamp(conversion or 0.0), 2),
            "return_pressure_score": round(clamp(pressure or 0.0), 2),
            "return_game_volatility_score": round(clamp(volatility or 0.0), 2),
            "surface_adjusted_return_score": round(clamp(surface_score or 0.0), 2),
            "break_prop_relevance": round(clamp(weighted_average(((break_threat, 0.55), (bp_created, 0.35), (conversion, 0.25))) or 0.0), 2),
            "under_total_modifier": round(clamp(weighted_average(((break_threat, 0.55), (second_score, 0.3), (100.0 - (errors or 50.0), 0.1))) or 0.0), 2),
            "game_handicap_modifier": round(clamp(weighted_average(((break_threat, 0.45), (return_score, 0.35), (surface_score, 0.2))) or 0.0), 2),
            "return_depth_fabricated": False,
            "confidence_cap_reason": confidence_cap,
            "missing_inputs": compact_list(missing_fields(source, RETURN_INPUTS), limit=35),
            "no_bet_reasons": compact_list(no_bet, limit=10),
            "insufficient_sample": insufficient,
            "limited_proxy": limited_proxy,
        },
        source_payload=source,
    )
