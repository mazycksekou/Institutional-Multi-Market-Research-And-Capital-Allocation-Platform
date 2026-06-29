from __future__ import annotations

from typing import Any

from .golf_impact_common import OUTRIGHT_MARKETS, clamp, compact_list, finalize_golf_response, normalize_golf_market


def evaluate_golf_impact_red_team(
    *,
    market_type: str = "top_20",
    data_availability: dict[str, Any] | None = None,
    strokes_gained_impact: dict[str, Any] | None = None,
    off_tee_impact: dict[str, Any] | None = None,
    approach_impact: dict[str, Any] | None = None,
    short_game_putting_context: dict[str, Any] | None = None,
    course_fit_context: dict[str, Any] | None = None,
    weather_wave_context: dict[str, Any] | None = None,
    field_tournament_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    source_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    market = normalize_golf_market(market_type)
    data = data_availability or {}
    sg = strokes_gained_impact or {}
    app = approach_impact or {}
    short = short_game_putting_context or {}
    course = course_fit_context or {}
    weather = weather_wave_context or {}
    field = field_tournament_context or {}
    avail = availability_context or {}
    incentive = incentive_context or {}
    cal = calibration or {}
    source = source_payload or {}
    available_groups = set(data.get("available_field_groups") or [])
    claimed = set(source.get("claimed_metrics") or source.get("model_claims") or [])
    reasons: list[str] = []
    missing: list[str] = []
    no_bet: list[str] = []
    downgrade = 0.0
    if {"strokes_gained", "sg", "sg_total"} & claimed and "strokes_gained_total_context" not in available_groups:
        reasons.append("strokes_gained_missing_but_claimed")
        downgrade += 24
    if {"sg_split", "sg_splits", "tee_to_green", "approach", "putting"} & claimed and "strokes_gained_split_context" not in available_groups:
        reasons.append("sg_split_missing_but_claimed")
        downgrade += 22
    if {"approach_bucket", "distance_bucket"} & claimed and "approach_distance_bucket_context" not in available_groups:
        reasons.append("approach_bucket_missing_but_claimed")
        downgrade += 18
    if {"course_architecture", "course_fit"} & claimed and "course_architecture_context" not in available_groups:
        reasons.append("course_architecture_missing_but_claimed")
        downgrade += 20
    if {"grass_fit", "grass"} & claimed and "grass_surface_context" not in available_groups:
        reasons.append("grass_fit_missing_but_claimed")
        downgrade += 16
    if {"tee_time_wave", "wave_draw"} & claimed and "tee_time_wave_context" not in available_groups:
        reasons.append("tee_time_wave_missing_but_claimed")
        downgrade += 18
    if {"weather_wave_edge", "wave_edge"} & claimed and "tee_time_wave_context" not in available_groups:
        reasons.append("weather_wave_edge_missing_but_claimed")
        downgrade += 18
    if {"injury", "health"} & claimed and "injury_context" not in available_groups:
        reasons.append("injury_status_missing_but_claimed")
        downgrade += 18
    if {"field_strength"} & claimed and "field_strength_context" not in available_groups:
        reasons.append("field_strength_missing_but_claimed")
        downgrade += 18
    if "recent_putting_spike_volatility_warning" in (short.get("no_bet_reasons") or []) or source.get("putting_spike_overfit"):
        reasons.append("putting_spike_overfit")
        downgrade += 14
    if source.get("recent_form_weight", 0) and source.get("recent_form_weight", 0) > 0.35:
        reasons.append("recent_form_overfit")
        downgrade += 12
    if "course_history_small_sample_capped" in (course.get("no_bet_reasons") or []) and source.get("overconfidence_flag"):
        reasons.append("course_history_overfit")
        downgrade += 12
    if "comparable_course_history_small_sample_capped" in (course.get("no_bet_reasons") or []) and source.get("overconfidence_flag"):
        reasons.append("comp_course_overfit")
        downgrade += 12
    if sg.get("insufficient_sample") and (sg.get("strokes_gained_score", 0.0) >= 55 or source.get("overconfidence_flag")):
        reasons.append("small_sample_sg_overfit")
        downgrade += 16
    if market in OUTRIGHT_MARKETS and (source.get("longshot_odds") or source.get("market_implied_probability", 1.0) and source.get("market_implied_probability", 1.0) < 0.025):
        if cal.get("calibration_status") != "calibration_ready" or source.get("overconfidence_flag"):
            reasons.append("outright_longshot_overconfidence")
            downgrade += 22
    if market == "first_round_leader" and (sg.get("volatility_score", 0.0) >= 60 or short.get("putting_volatility_score", 0.0) >= 60) and source.get("ignores_volatility"):
        reasons.append("first_round_leader_volatility_ignored")
        downgrade += 20
    if avail.get("withdrawal_risk_score", 0.0) >= 60 and source.get("ignores_withdrawal_risk"):
        reasons.append("withdrawal_risk_ignored")
        downgrade += 24
    if "no_cut_event_disables_make_miss_cut_logic" in (field.get("no_bet_reasons") or []) and market in {"make_cut", "miss_cut"}:
        reasons.append("cut_rule_context_confusion")
        downgrade += 22
    if incentive.get("narrative_overfit_risk") == "high":
        reasons.append("narrative_incentive_overfit")
        downgrade += 10
    if cal.get("calibration_status") == "insufficient_data":
        reasons.append("calibration_missing")
        missing.extend(cal.get("next_required_data") or ["settled_golf_outcomes"])
        downgrade += 12
    for hard in (
        "strokes_gained_missing_but_claimed",
        "sg_split_missing_but_claimed",
        "course_architecture_missing_but_claimed",
        "tee_time_wave_missing_but_claimed",
        "weather_wave_edge_missing_but_claimed",
        "injury_status_missing_but_claimed",
        "field_strength_missing_but_claimed",
        "outright_longshot_overconfidence",
        "first_round_leader_volatility_ignored",
        "withdrawal_risk_ignored",
        "cut_rule_context_confusion",
    ):
        if hard in reasons:
            no_bet.append(hard)
    if downgrade >= 35:
        adjustment = "NO_BET"
    elif downgrade >= 18:
        adjustment = "DATA_INSUFFICIENT"
    elif downgrade > 0:
        adjustment = "WATCHLIST_REVIEW"
    else:
        adjustment = "NO_CHANGE"
    return finalize_golf_response(
        {
            "red_team_status": "downgrade" if downgrade else "pass_review_only",
            "downgrade_score": round(clamp(downgrade), 2),
            "recommended_action_adjustment": adjustment,
            "no_bet_reasons": compact_list(no_bet, limit=18),
            "red_team_reasons": compact_list(reasons or ["no_red_team_hard_block"], limit=30),
            "missing_inputs": compact_list(missing, limit=20),
            "confidence_cap_reason": "red_team_downgrade" if downgrade else None,
            "red_team_only": True,
        },
        source_payload=source,
    )
