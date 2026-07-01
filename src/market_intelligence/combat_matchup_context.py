from __future__ import annotations

from typing import Any

from .combat_impact_common import clamp, compact_list, finalize_combat_response, get_metric, percent_score, safe_float, score_from_range, weighted_average


def _stance_pair(row: dict[str, Any]) -> tuple[str, str]:
    a = str(row.get("fighter_a_stance") or row.get("stance") or "").strip().lower()
    b = str(row.get("fighter_b_stance") or row.get("opponent_stance") or "").strip().lower()
    return a, b


def evaluate_combat_matchup_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    reasons: list[str] = []
    notes: list[str] = []
    a_strike = score_from_range(get_metric(source, "significant_strikes_landed_per_minute"), low=0.5, high=7.5) or 0.0
    a_td = score_from_range(get_metric(source, "takedowns_per_15"), low=0.0, high=5.0) or 0.0
    b_td_def = percent_score(get_metric(source, "takedown_defense", prefix="fighter_b")) or 0.0
    sub = score_from_range(get_metric(source, "submission_attempts_per_15"), low=0.0, high=3.5) or 0.0
    b_sub_def = percent_score(get_metric(source, "submission_defense", prefix="fighter_b")) or 0.0
    pressure = score_from_range(get_metric(source, "pressure_striking_rate"), low=0.0, high=1.0) or 0.0
    counter = score_from_range(get_metric(source, "counter_strike_rate", prefix="fighter_b"), low=0.0, high=1.0) or 0.0
    durability_risk = score_from_range(get_metric(source, "knockdowns_absorbed", prefix="fighter_b"), low=0.0, high=4.0) or 0.0
    reach_a = safe_float(source.get("fighter_a_reach_inches") or source.get("reach_inches"))
    reach_b = safe_float(source.get("fighter_b_reach_inches") or source.get("opponent_reach_inches"))
    reach_score = 50.0
    if reach_a is not None and reach_b is not None:
        reach_score = clamp(50.0 + (reach_a - reach_b) * 7.0)
        reasons.append("reach_height_distance_management_context_supported")
    stance_a, stance_b = _stance_pair(source)
    stance_score = 50.0
    if stance_a and stance_b:
        stance_score = 62.0 if stance_a != stance_b else 52.0
        reasons.append("southpaw_orthodox_context_supported")
    if a_strike >= 55 and a_td >= 40:
        reasons.append("striker_grappler_blend_supported")
    elif a_strike >= 60:
        reasons.append("striker_vs_grappler_range_path_supported")
    if a_td >= 55:
        reasons.append("wrestler_vs_takedown_defense")
    if sub >= 45:
        reasons.append("submission_hunter_vs_submission_defense")
    if pressure >= 55 and counter >= 45:
        reasons.append("pressure_boxer_vs_counter_striker")
    if source.get("calf_kick_threat") not in (None, "") and source.get("stance_vulnerability") not in (None, ""):
        reasons.append("calf_kick_threat_vs_stance_vulnerability")
    if source.get("clinch_control") not in (None, ""):
        reasons.append("clinch_fighter_vs_open_space_fighter")
    if source.get("cage_wrestling_control") not in (None, "") or source.get("get_up_rate") not in (None, ""):
        reasons.append("cage_wrestler_vs_get_up_artist")
    if bool(source.get("short_notice_flag")) and (source.get("first_round_pace") not in (None, "") or pressure >= 55):
        reasons.append("short_notice_fighter_vs_pace_heavy_opponent")
    if source.get("ruleset") == "boxing" and (source.get("fighter_a_jab_rate") not in (None, "") or source.get("fighter_a_power_punch_rate") not in (None, "")):
        reasons.append("boxing_inside_outside_punch_profile_supported")
    mismatch = weighted_average(((a_strike, 0.22), (a_td, 0.22), (100.0 - b_td_def, 0.18), (sub, 0.14), (100.0 - b_sub_def, 0.12), (reach_score, 0.1), (stance_score, 0.08), (durability_risk, 0.12))) or 0.0
    risk = weighted_average(((abs(a_strike - a_td), 0.15), (100.0 - reach_score if reach_score < 50 else 20.0, 0.1), (durability_risk, 0.25), (counter, 0.15))) or 0.0
    if not stance_a or not stance_b:
        notes.append("stance_missing_not_fabricated")
    if reach_a is None or reach_b is None:
        notes.append("reach_missing_not_fabricated")
    if len(reasons) == 0:
        notes.append("style_matchup_not_claimed_without_supporting_fields")
    if risk >= 60:
        notes.append("conflicting_matchup_signals_reduce_confidence")
    return finalize_combat_response(
        {
            "matchup_advantage_score": round(clamp(mismatch), 2),
            "matchup_risk_score": round(clamp(risk), 2),
            "striking_matchup_score": round(clamp(a_strike), 2),
            "grappling_matchup_score": round(clamp(weighted_average(((a_td, 0.5), (100.0 - b_td_def, 0.35), (sub, 0.15))) or 0.0), 2),
            "phase_matchup_score": round(clamp(score_from_range(source.get("phase_control_score"), low=0.0, high=100.0) or mismatch), 2),
            "durability_matchup_score": round(clamp(durability_risk), 2),
            "cardio_matchup_score": round(clamp(score_from_range(source.get("cardio_rating_proxy"), low=0.0, high=1.0) or 0.0), 2),
            "tactical_mismatch_reasons": compact_list(reasons, limit=20),
            "no_bet_reasons": compact_list(notes, limit=20),
            "market_specific_matchup_notes": compact_list(reasons, limit=20),
            "moneyline_relevance": round(clamp(weighted_average(((mismatch, 0.5), (100.0 - risk, 0.2), (reach_score, 0.1), (stance_score, 0.1))) or 0.0), 2),
            "method_relevance": round(clamp(weighted_average(((sub, 0.25), (durability_risk, 0.35), (a_td, 0.2), (a_strike, 0.2))) or 0.0), 2),
            "total_rounds_relevance": round(clamp(weighted_average(((100.0 - durability_risk, 0.35), (100.0 - sub, 0.2), (100.0 - pressure, 0.15), (risk, 0.15))) or 0.0), 2),
            "fighter_prop_relevance": round(clamp(weighted_average(((a_strike, 0.25), (a_td, 0.25), (sub, 0.2), (reach_score, 0.1))) or 0.0), 2),
            "stance_fabricated": False,
            "reach_fabricated": False,
        },
        source_payload=source,
    )
