from __future__ import annotations

from typing import Any

from .tennis_impact_common import clamp, compact_list, finalize_tennis_response, missing_fields, percent_score, safe_float, score_from_range, weighted_average


PRESSURE_INPUTS = (
    "break_points_saved",
    "break_points_converted",
    "pressure_points_won",
    "deciding_points_won",
    "tiebreak_win_rate",
    "tiebreak_points_won",
    "first_set_tiebreak_rate",
    "tiebreaks_played_rate",
    "close_set_win_rate",
    "deciding_set_win_rate",
    "first_set_win_rate",
    "recent_tiebreak_sample",
    "long_term_tiebreak_sample",
    "clutch_proxy",
    "pressure_double_fault_rate",
)


def evaluate_tennis_pressure_tiebreak_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    bp_save = score_from_range(source.get("break_points_saved"), low=0.50, high=0.72)
    bp_conv = score_from_range(source.get("break_points_converted"), low=0.32, high=0.50)
    pressure = score_from_range(source.get("pressure_points_won"), low=0.45, high=0.58)
    deciding = score_from_range(source.get("deciding_points_won"), low=0.45, high=0.58)
    tb_win = score_from_range(source.get("tiebreak_win_rate") or source.get("player_a_tiebreak_win_rate"), low=0.42, high=0.62)
    tb_points = score_from_range(source.get("tiebreak_points_won"), low=0.45, high=0.58)
    first_tb_rate = score_from_range(source.get("first_set_tiebreak_rate"), low=0.08, high=0.35)
    tb_played = score_from_range(source.get("tiebreaks_played_rate"), low=0.08, high=0.38)
    close_set = score_from_range(source.get("close_set_win_rate"), low=0.42, high=0.62)
    deciding_set = score_from_range(source.get("deciding_set_win_rate"), low=0.42, high=0.62)
    first_set = score_from_range(source.get("first_set_win_rate"), low=0.42, high=0.62)
    clutch = percent_score(source.get("clutch_proxy"))
    pressure_df = score_from_range(source.get("pressure_double_fault_rate"), low=0.015, high=0.09)
    recent_tb = safe_float(source.get("recent_tiebreak_sample"), 0.0) or 0.0
    long_tb = safe_float(source.get("long_term_tiebreak_sample"), 0.0) or 0.0
    tb_sample = max(recent_tb, long_tb)
    tb_skill_raw = weighted_average(((tb_win, 0.45), (tb_points, 0.35), (100.0 - (pressure_df or 0.0), 0.15)))
    tb_skill = tb_skill_raw * min(tb_sample / 20.0, 1.0) if tb_skill_raw is not None and tb_sample else tb_skill_raw
    break_pressure = weighted_average(((bp_save, 0.35), (bp_conv, 0.35), (pressure, 0.25), (100.0 - (pressure_df or 0.0), 0.2)))
    first_set_pressure = weighted_average(((first_set, 0.4), (first_tb_rate, 0.25), (pressure, 0.2)))
    close_volatility = weighted_average(((tb_played, 0.35), (100.0 - (close_set or 50.0), 0.25), (100.0 - (deciding_set or 50.0), 0.2), (pressure_df, 0.2)))
    pressure_score = weighted_average(((break_pressure, 0.4), (tb_skill, 0.25), (pressure, 0.25), (deciding, 0.2), (clutch, 0.1)))
    tb_likelihood = weighted_average(((first_tb_rate, 0.3), (tb_played, 0.45), (tb_skill, 0.2)))
    no_bet: list[str] = []
    if tb_win is not None and tb_sample < 12:
        no_bet.append("tiebreak_record_sample_size_capped")
    if bp_conv is not None:
        no_bet.append("break_point_conversion_noisy_volatility_capped")
    if clutch is not None:
        no_bet.append("clutch_proxy_modifier_only_not_standalone_edge")
    if pressure_df and pressure_df >= 60:
        no_bet.append("pressure_double_fault_risk_no_bet_logic")
    return finalize_tennis_response(
        {
            "pressure_score": round(clamp(pressure_score or 0.0), 2),
            "break_point_pressure_score": round(clamp(break_pressure or 0.0), 2),
            "tiebreak_skill_score": round(clamp(tb_skill or 0.0), 2),
            "tiebreak_likelihood_modifier": round(clamp(tb_likelihood or 0.0), 2),
            "first_set_pressure_score": round(clamp(first_set_pressure or 0.0), 2),
            "close_set_volatility_score": round(clamp(close_volatility or 0.0), 2),
            "pressure_confidence_cap": "tiebreak_sample_size_capped" if tb_win is not None and tb_sample < 12 else "pressure_metrics_modifier_only" if pressure_score else None,
            "clutch_is_standalone_edge": False,
            "missing_inputs": compact_list(missing_fields(source, PRESSURE_INPUTS), limit=30),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )
