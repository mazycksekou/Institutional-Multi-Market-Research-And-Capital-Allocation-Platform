from __future__ import annotations

from typing import Any

from .baseball_impact_common import clamp, compact_list, finalize_baseball_response, missing_fields, normalize_baseball_role, percent_score, safe_float, score_centered, score_from_range, weighted_average


PITCHER_INPUTS = (
    "k_rate",
    "bb_rate",
    "k_minus_bb_rate",
    "whiff_rate",
    "chase_rate",
    "zone_rate",
    "first_pitch_strike_rate",
    "called_strike_plus_whiff_proxy",
    "swinging_strike_rate",
    "ground_ball_rate",
    "fly_ball_rate",
    "barrel_allowed_rate",
    "hard_hit_allowed_rate",
    "xwoba_allowed",
    "xba_allowed",
    "xslg_allowed",
    "hr_per_9_proxy",
    "pitch_count_recent",
    "innings_per_start",
    "times_through_order_penalty",
    "velocity_trend",
    "command_trend",
    "pitch_mix",
    "pitch_type_run_values",
    "pitch_movement_proxy",
    "spin_rate_proxy",
    "extension_proxy",
    "release_point_stability",
    "rest_days",
    "injury_status",
    "confirmed_starter",
    "opener_risk",
    "pitch_count_limit",
    "back_to_back_usage",
    "three_in_four_usage",
    "bullpen_fatigue_score",
)


def evaluate_baseball_pitcher_impact(row: dict[str, Any] | None = None, *, pitcher_level_allowed: bool = True, data_tier: int | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    role = normalize_baseball_role(source.get("role") or ("RELIEF_PITCHER" if source.get("leverage_role") else "STARTING_PITCHER"))
    if not pitcher_level_allowed and not any(source.get(k) not in (None, "", []) for k in ("confirmed_starter", "probable_pitcher", "starter_status")):
        return finalize_baseball_response(
            {
                "pitcher_role": role,
                "pitcher_impact_score": 0.0,
                "strikeout_skill_score": 0.0,
                "command_score": 0.0,
                "contact_suppression_score": 0.0,
                "home_run_risk_score": 0.0,
                "pitch_mix_quality_score": 0.0,
                "workload_fatigue_score": 0.0,
                "times_through_order_risk": 0.0,
                "pitcher_market_relevance": [],
                "missing_pitcher_inputs": ["pitcher_box_score_context", "pitch_level_context"],
                "no_bet_reasons": [],
                "confidence_cap_reason": "pitcher_level_data_not_available",
                "pitch_tracking_inferred": False,
            },
            source_payload=source,
        )
    k_minus_bb = safe_float(source.get("k_minus_bb_rate"))
    if k_minus_bb is None and safe_float(source.get("k_rate")) is not None and safe_float(source.get("bb_rate")) is not None:
        k_minus_bb = (safe_float(source.get("k_rate")) or 0.0) - (safe_float(source.get("bb_rate")) or 0.0)
    strikeout = weighted_average(
        (
            (score_from_range(source.get("k_rate"), low=0.14, high=0.34), 0.9),
            (score_from_range(source.get("whiff_rate"), low=0.18, high=0.38), 0.8),
            (score_from_range(source.get("called_strike_plus_whiff_proxy"), low=0.22, high=0.36), 0.65),
            (score_from_range(source.get("swinging_strike_rate"), low=0.08, high=0.18), 0.55),
            (score_from_range(source.get("chase_rate"), low=0.24, high=0.38), 0.35),
        )
    )
    command = weighted_average(
        (
            (score_from_range(source.get("bb_rate"), low=0.04, high=0.13, inverse=True), 0.8),
            (score_from_range(k_minus_bb, low=0.04, high=0.26), 0.75),
            (score_from_range(source.get("zone_rate"), low=0.39, high=0.52), 0.35),
            (score_from_range(source.get("first_pitch_strike_rate"), low=0.54, high=0.70), 0.45),
            (score_centered(source.get("command_trend"), center=0.0, span=0.08), 0.35),
        )
    )
    contact = weighted_average(
        (
            (score_from_range(source.get("barrel_allowed_rate"), low=0.035, high=0.12, inverse=True), 0.75),
            (score_from_range(source.get("hard_hit_allowed_rate"), low=0.30, high=0.48, inverse=True), 0.65),
            (score_from_range(source.get("xwoba_allowed"), low=0.270, high=0.380, inverse=True), 0.75),
            (score_from_range(source.get("xba_allowed"), low=0.205, high=0.285, inverse=True), 0.45),
            (score_from_range(source.get("xslg_allowed"), low=0.330, high=0.520, inverse=True), 0.5),
            (score_from_range(source.get("ground_ball_rate"), low=0.32, high=0.55), 0.25),
        )
    )
    hr_risk = weighted_average(((score_from_range(source.get("hr_per_9_proxy"), low=0.5, high=1.8), 0.75), (score_from_range(source.get("fly_ball_rate"), low=0.28, high=0.48), 0.25), (score_from_range(source.get("barrel_allowed_rate"), low=0.035, high=0.12), 0.65))) or 0.0
    pitch_mix_quality = weighted_average(((score_centered(source.get("pitch_type_run_values"), center=0.0, span=0.24), 0.55), (percent_score(source.get("pitch_mix_quality_proxy")), 0.35), (score_centered(source.get("velocity_trend"), center=0.0, span=1.8), 0.35), (score_from_range(source.get("release_point_stability"), low=0.0, high=100.0), 0.25)))
    rest = score_from_range(source.get("rest_days"), low=3.0, high=6.0)
    pitch_count = score_from_range(source.get("pitch_count_recent"), low=55.0, high=105.0)
    pitch_limit = safe_float(source.get("pitch_count_limit"))
    fatigue = weighted_average(
        (
            (100.0 - (rest if rest is not None else 65.0), 0.45),
            (pitch_count, 0.35),
            (score_from_range(source.get("back_to_back_usage"), low=0.0, high=1.0), 0.45),
            (score_from_range(source.get("three_in_four_usage"), low=0.0, high=1.0), 0.45),
            (score_from_range(source.get("bullpen_fatigue_score"), low=0.0, high=100.0), 0.25),
            (85.0 if pitch_limit is not None and pitch_limit < 80 else None, 0.65),
        )
    ) or 0.0
    tto = score_from_range(source.get("times_through_order_penalty"), low=0.0, high=0.12) or max(0.0, 100.0 - (score_from_range(source.get("innings_per_start"), low=3.5, high=6.8) or 65.0))
    impact = weighted_average(((strikeout, 0.7), (command, 0.75), (contact, 0.7), (pitch_mix_quality, 0.35), (100.0 - hr_risk, 0.35), (100.0 - fatigue, 0.25), (100.0 - tto, 0.2)))
    no_bet = []
    cap_reason = None
    if source.get("confirmed_starter") is False or str(source.get("starter_status") or "").lower() in {"unconfirmed", "unknown", "opener_possible"}:
        no_bet.append("starter_unconfirmed_caps_first_five_and_pitcher_props")
        no_bet.append("unconfirmed_starter_caps_pitcher_prop_and_first_five_confidence")
        cap_reason = "starter_unconfirmed"
    if pitch_limit is not None and pitch_limit < 85:
        no_bet.append("pitch_count_limit_caps_outs_and_strikeout_props")
        cap_reason = "pitch_count_limit"
    if source.get("opener_risk") or str(source.get("pitcher_role_pattern") or "").lower() in {"opener", "bulk", "opener_bulk"}:
        no_bet.append("opener_or_bulk_pattern_caps_starter_props")
        no_bet.append("opener_bulk_pattern_caps_starter_props")
        cap_reason = "opener_bulk_pattern"
    missing = missing_fields(source, PITCHER_INPUTS)
    tracking_missing = [key for key in ("pitch_movement_proxy", "spin_rate_proxy", "extension_proxy") if source.get(key) in (None, "", [])]
    return finalize_baseball_response(
        {
            "pitcher_role": role,
            "pitcher_impact_score": round(clamp(impact or 0.0), 2),
            "strikeout_skill_score": round(clamp(strikeout or 0.0), 2),
            "command_score": round(clamp(command or 0.0), 2),
            "contact_suppression_score": round(clamp(contact or 0.0), 2),
            "home_run_risk_score": round(clamp(hr_risk), 2),
            "pitch_mix_quality_score": round(clamp(pitch_mix_quality or 0.0), 2),
            "workload_fatigue_score": round(clamp(fatigue), 2),
            "times_through_order_risk": round(clamp(tto), 2),
            "pitcher_market_relevance": ["pitcher_strikeouts", "pitcher_outs_recorded", "pitcher_earned_runs", "pitcher_hits_allowed", "first_five_moneyline", "first_five_total"],
            "missing_pitcher_inputs": compact_list(missing, limit=35),
            "missing_pitch_tracking_inputs": compact_list(tracking_missing, limit=10),
            "no_bet_reasons": compact_list(no_bet, limit=12),
            "confidence_cap_reason": cap_reason or ("pitch_count_rest_missing_caps_fatigue_confidence" if source.get("pitch_count_recent") in (None, "") or source.get("rest_days") in (None, "") else None),
            "pitch_tracking_inferred": False,
            "data_tier": data_tier,
        },
        source_payload=source,
    )
