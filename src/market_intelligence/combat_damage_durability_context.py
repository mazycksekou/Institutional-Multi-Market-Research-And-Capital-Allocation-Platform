from __future__ import annotations

from typing import Any

from .combat_impact_common import clamp, compact_list, finalize_combat_response, get_metric, missing_fields, score_from_range, weighted_average


DAMAGE_FIELDS = ("knockdowns_absorbed", "head_strike_absorption_rate", "body_strike_absorption_rate", "leg_kick_absorption_rate", "cut_history", "recent_damage_taken")


def evaluate_combat_damage_durability_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    def any_metric(base: str):
        value = get_metric(source, base, prefix="fighter_b")
        return value if value not in (None, "") else get_metric(source, base, prefix="fighter_a")

    threat = weighted_average(((score_from_range(get_metric(source, "knockdowns_landed"), low=0.0, high=3.0), 0.35), (score_from_range(get_metric(source, "knockdown_rate_landed"), low=0.0, high=0.7), 0.35), (score_from_range(get_metric(source, "ko_wins"), low=0.0, high=12.0), 0.15)))
    chin = weighted_average(((score_from_range(any_metric("knockdowns_absorbed"), low=0.0, high=4.0), 0.45), (score_from_range(any_metric("knockdown_rate_absorbed"), low=0.0, high=0.8), 0.35), (score_from_range(any_metric("stun_or_wobble_history"), low=0.0, high=1.0), 0.2)))
    body = score_from_range(any_metric("body_strike_absorption_rate"), low=0.0, high=1.0) or 0.0
    leg = score_from_range(any_metric("leg_kick_absorption_rate"), low=0.0, high=1.0) or 0.0
    cut = weighted_average(((score_from_range(any_metric("cut_history"), low=0.0, high=1.0), 0.45), (score_from_range(any_metric("swelling_history"), low=0.0, high=1.0), 0.2), (score_from_range(any_metric("doctor_stoppage_history"), low=0.0, high=1.0), 0.35))) or 0.0
    attrition = weighted_average(((score_from_range(any_metric("strikes_absorbed_per_minute"), low=1.0, high=7.0), 0.3), (score_from_range(any_metric("recent_damage_taken"), low=0.0, high=1.0), 0.35), (score_from_range(any_metric("short_layoff_after_damage"), low=0.0, high=1.0), 0.25), (score_from_range(any_metric("weight_cut_damage_risk"), low=0.0, high=1.0), 0.2))) or 0.0
    durability_risk = weighted_average(((chin, 0.35), (body, 0.15), (leg, 0.15), (cut, 0.2), (attrition, 0.25))) or 0.0
    no_bet = []
    if not any(any_metric(field) not in (None, "") for field in DAMAGE_FIELDS):
        no_bet.append("durability_data_missing_no_chin_certainty")
    if source.get("medical_suspension_context") in (None, ""):
        no_bet.append("medical_suspension_not_fabricated")
    if source.get("recent_damage_taken") not in (None, ""):
        no_bet.append("recent_damage_context_caps_confidence")
    if source.get("ko_losses") not in (None, "") and any_metric("knockdowns_absorbed") in (None, ""):
        no_bet.append("chin_not_inferred_from_record_only")
    return finalize_combat_response(
        {
            "damage_threat_score": round(clamp(threat or 0.0), 2),
            "durability_risk_score": round(clamp(durability_risk), 2),
            "chin_risk_score": round(clamp(chin or 0.0), 2),
            "body_damage_risk_score": round(clamp(body), 2),
            "leg_damage_risk_score": round(clamp(leg), 2),
            "cut_stoppage_risk_score": round(clamp(cut), 2),
            "doctor_stoppage_risk_score": round(clamp(score_from_range(any_metric("doctor_stoppage_history"), low=0.0, high=1.0) or 0.0), 2),
            "attritional_damage_score": round(clamp(attrition), 2),
            "finish_volatility_score": round(clamp(weighted_average(((threat, 0.35), (durability_risk, 0.4), (cut, 0.25))) or 0.0), 2),
            "durability_fabricated": False,
            "medical_suspension_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, DAMAGE_FIELDS), limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )
