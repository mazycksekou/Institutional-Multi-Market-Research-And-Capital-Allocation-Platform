from __future__ import annotations

from typing import Any

from .combat_impact_common import clamp, compact_list, finalize_combat_response, get_metric, missing_fields, percent_score, safe_float, score_metric, weighted_average


SUMMARY_FIELDS = ("fighter_a_takedowns_per_15", "fighter_a_takedown_accuracy", "fighter_b_takedown_defense", "fighter_a_submission_attempts_per_15")
CONTROL_FIELDS = ("control_time_average", "top_control_time", "bottom_time", "get_up_rate", "scramble_success_rate")


def evaluate_combat_grappling_control_impact(row: dict[str, Any] | None = None, *, data_tier: int = 0) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    sample = safe_float(source.get("sample_size"), 0.0) or 0.0
    takedown_threat = weighted_average(
        (
            (score_metric(source, "takedowns_per_15", low=0.0, high=5.0), 0.4),
            (percent_score(get_metric(source, "takedown_accuracy")), 0.3),
            (score_metric(source, "takedown_attempts_per_15", low=0.0, high=10.0), 0.25),
            (score_metric(source, "opponent_adjusted_grappling_score", low=0.0, high=100.0), 0.25),
        )
    )
    td_def = weighted_average(((percent_score(get_metric(source, "takedown_defense", prefix="fighter_b")), 0.55), (percent_score(get_metric(source, "submission_defense", prefix="fighter_b")), 0.2)))
    control = weighted_average(
        (
            (score_metric(source, "control_time_average", low=0.0, high=9.0), 0.35),
            (score_metric(source, "top_control_time", low=0.0, high=7.0), 0.3),
            (score_metric(source, "clinch_control_rate", low=0.0, high=1.0), 0.15),
            (score_metric(source, "cage_control_rate", low=0.0, high=1.0), 0.15),
        )
    )
    top = weighted_average(((score_metric(source, "top_control_time", low=0.0, high=8.0), 0.55), (score_metric(source, "guard_pass_rate", low=0.0, high=1.0), 0.25), (score_metric(source, "ground_and_pound_rate", low=0.0, high=4.0), 0.2)))
    bottom = weighted_average(((score_metric(source, "get_up_rate", low=0.0, high=1.0), 0.45), (score_metric(source, "guard_retention_rate", low=0.0, high=1.0), 0.35), (score_metric(source, "bottom_time", low=6.0, high=0.0), 0.2)))
    scramble = weighted_average(((score_metric(source, "scramble_success_rate", low=0.0, high=1.0), 0.6), (score_metric(source, "get_up_rate", low=0.0, high=1.0), 0.25), (score_metric(source, "mat_return_rate", low=0.0, high=1.0), 0.15)))
    sub_threat = weighted_average(((score_metric(source, "submission_attempts_per_15", low=0.0, high=3.5), 0.4), (score_metric(source, "submission_attempt_quality", low=0.0, high=1.0), 0.35), (score_metric(source, "back_take_rate", low=0.0, high=1.0), 0.25)))
    sub_def = weighted_average(((percent_score(get_metric(source, "submission_defense", prefix="fighter_b")), 0.6), (score_metric(source, "guard_retention_rate", low=0.0, high=1.0), 0.25)))
    ground_damage = weighted_average(((score_metric(source, "ground_and_pound_rate", low=0.0, high=5.0), 0.45), (score_metric(source, "ground_and_pound_damage_proxy", low=0.0, high=1.0), 0.45), (top, 0.2)))
    impact = weighted_average(((takedown_threat, 0.25), (control, 0.25), (top, 0.2), (scramble, 0.15), (sub_threat, 0.15))) or 0.0
    limited_proxy = bool(missing_fields(source, CONTROL_FIELDS))
    no_bet = []
    if limited_proxy:
        no_bet.append("control_time_or_scramble_context_missing_not_fabricated")
    if get_metric(source, "submission_attempt_quality") in (None, ""):
        no_bet.append("submission_quality_missing_not_fabricated")
    return finalize_combat_response(
        {
            "grappling_impact_score": round(clamp(impact), 2),
            "takedown_threat_score": round(clamp(takedown_threat or 0.0), 2),
            "takedown_defense_score": round(clamp(td_def or 0.0), 2),
            "control_time_score": round(clamp(control or 0.0), 2),
            "top_control_score": round(clamp(top or 0.0), 2),
            "bottom_survival_score": round(clamp(bottom or 0.0), 2),
            "scramble_score": round(clamp(scramble or 0.0), 2),
            "submission_threat_score": round(clamp(sub_threat or 0.0), 2),
            "submission_defense_score": round(clamp(sub_def or 0.0), 2),
            "ground_damage_score": round(clamp(ground_damage or 0.0), 2),
            "grappling_prop_relevance": round(clamp(weighted_average(((takedown_threat, 0.35), (control, 0.3), (scramble, 0.15), (sub_threat, 0.15))) or 0.0), 2),
            "submission_relevance_modifier": round(clamp(weighted_average(((sub_threat, 0.55), (control, 0.25), (top, 0.2))) or 0.0), 2),
            "decision_relevance_modifier": round(clamp(weighted_average(((control, 0.35), (top, 0.25), (100.0 - (ground_damage or 0.0), 0.2))) or 0.0), 2),
            "missing_inputs": compact_list([*missing_fields(source, SUMMARY_FIELDS), *missing_fields(source, CONTROL_FIELDS)], limit=25),
            "insufficient_sample": bool(sample and sample < 6),
            "limited_proxy": limited_proxy,
            "control_time_fabricated": False,
            "submission_quality_fabricated": False,
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )
