from __future__ import annotations

from typing import Any

from .combat_impact_common import clamp, compact_list, finalize_combat_response, get_metric, missing_fields, percent_score, safe_float, score_from_range, score_metric, weighted_average


SUMMARY_FIELDS = (
    "fighter_a_significant_strikes_landed_per_minute",
    "fighter_a_significant_strikes_absorbed_per_minute",
    "fighter_a_striking_accuracy",
    "fighter_a_striking_defense",
)
PUNCH_TRACKING_FIELDS = ("fighter_a_jab_rate", "fighter_a_jab_accuracy", "fighter_a_power_punch_rate", "fighter_a_power_punch_accuracy")


def evaluate_combat_striking_impact(row: dict[str, Any] | None = None, *, data_tier: int = 0) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    volume = weighted_average(
        (
            (score_metric(source, "significant_strikes_landed_per_minute", low=0.5, high=7.5), 0.45),
            (score_metric(source, "first_round_striking_pace", low=0.0, high=8.0), 0.2),
            (score_metric(source, "pressure_striking_rate", low=0.0, high=1.0), 0.2),
            (score_metric(source, "opponent_adjusted_striking_score", low=0.0, high=100.0), 0.25),
        )
    )
    accuracy = weighted_average(
        (
            (percent_score(get_metric(source, "striking_accuracy")), 0.45),
            (percent_score(get_metric(source, "jab_accuracy")), 0.2),
            (percent_score(get_metric(source, "power_punch_accuracy")), 0.2),
            (percent_score(get_metric(source, "pocket_exchange_success_rate")), 0.2),
        )
    )
    defense = weighted_average(
        (
            (percent_score(get_metric(source, "striking_defense")), 0.45),
            (score_metric(source, "significant_strikes_absorbed_per_minute", low=6.5, high=1.0), 0.35),
            (score_metric(source, "knockdowns_absorbed", low=2.5, high=0.0), 0.2),
        )
    )
    kd_raw = score_metric(source, "knockdown_average", low=0.0, high=0.8)
    sample = safe_float(source.get("sample_size"), 0.0) or 0.0
    kd_cap = 0.55 if sample and sample < 6 else 1.0
    power = weighted_average(
        (
            ((kd_raw or 0.0) * kd_cap, 0.35),
            (score_metric(source, "knockdowns_landed", low=0.0, high=3.0), 0.25),
            (percent_score(get_metric(source, "power_punch_accuracy")), 0.25),
            (score_metric(source, "power_punch_rate", low=0.0, high=30.0), 0.15),
        )
    )
    absorption_risk = weighted_average(
        (
            (score_metric(source, "significant_strikes_absorbed_per_minute", low=1.0, high=7.0), 0.4),
            (score_metric(source, "head_strike_rate", low=0.0, high=1.0), 0.25),
            (100.0 - (defense or 0.0), 0.35),
        )
    )
    boxing_profile = weighted_average(
        (
            (score_metric(source, "jab_rate", low=0.0, high=35.0), 0.3),
            (percent_score(get_metric(source, "jab_accuracy")), 0.25),
            (score_metric(source, "power_punch_rate", low=0.0, high=30.0), 0.3),
            (percent_score(get_metric(source, "power_punch_accuracy")), 0.25),
        )
    )
    impact = weighted_average(((volume, 0.3), (accuracy, 0.25), (defense, 0.25), (power, 0.2))) or 0.0
    missing = compact_list(missing_fields(source, SUMMARY_FIELDS), limit=20)
    limited_proxy = bool(missing) or not any(get_metric(source, field.replace("fighter_a_", "")) not in (None, "") for field in PUNCH_TRACKING_FIELDS)
    no_bet = []
    if sample and sample < 6 and kd_raw is not None:
        no_bet.append("knockdown_average_sample_capped")
    if missing_fields(source, PUNCH_TRACKING_FIELDS):
        no_bet.append("punch_tracking_missing_not_fabricated")
    return finalize_combat_response(
        {
            "striking_impact_score": round(clamp(impact), 2),
            "volume_score": round(clamp(volume or 0.0), 2),
            "accuracy_score": round(clamp(accuracy or 0.0), 2),
            "defense_score": round(clamp(defense or 0.0), 2),
            "power_score": round(clamp(power or 0.0), 2),
            "knockdown_threat_score": round(clamp((kd_raw or 0.0) * kd_cap), 2),
            "damage_absorption_risk_score": round(clamp(absorption_risk or 0.0), 2),
            "boxing_punch_profile_score": round(clamp(boxing_profile or 0.0), 2),
            "striking_prop_relevance": round(clamp(weighted_average(((volume, 0.45), (accuracy, 0.25), (100.0 - (absorption_risk or 0.0), 0.1))) or 0.0), 2),
            "ko_tko_relevance_modifier": round(clamp(weighted_average(((power, 0.45), (volume, 0.2), (absorption_risk, 0.15))) or 0.0), 2),
            "over_under_rounds_modifier": round(clamp(weighted_average(((volume, 0.2), (100.0 - (power or 0.0), 0.3), (defense, 0.25))) or 0.0), 2),
            "missing_inputs": missing,
            "insufficient_sample": bool(sample and sample < 6),
            "limited_proxy": limited_proxy,
            "punch_tracking_fabricated": False,
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

