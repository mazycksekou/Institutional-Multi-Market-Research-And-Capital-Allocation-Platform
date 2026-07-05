from __future__ import annotations

from typing import Any

from src.market_intelligence.tennis_impact_common import CORRECT_SCORE_MARKETS, clamp, compact_list, finalize_tennis_response, normalize_tennis_market, safe_float


def evaluate_tennis_impact_red_team(
    *,
    market_type: str = "moneyline",
    data_availability: dict[str, Any] | None = None,
    serve_impact: dict[str, Any] | None = None,
    return_impact: dict[str, Any] | None = None,
    surface_context: dict[str, Any] | None = None,
    format_markov_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    pressure_tiebreak_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    source_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    market = normalize_tennis_market(market_type)
    data = data_availability or {}
    serve = serve_impact or {}
    ret = return_impact or {}
    surface = surface_context or {}
    fmt = format_markov_context or {}
    matchup = matchup_context or {}
    pressure = pressure_tiebreak_context or {}
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
    checks = [
        ({"serve_placement", "serve_location"}, "serve_placement_context", "serve_placement_missing_but_claimed", 20),
        ({"serve_speed", "serve_velocity"}, "tracking_context", "serve_speed_missing_but_claimed", 18),
        ({"return_position"}, "return_position_context", "return_position_missing_but_claimed", 16),
        ({"shot_pattern", "rally_directionality", "forehand_backhand_pattern"}, "shot_pattern_context", "shot_pattern_missing_but_claimed", 20),
        ({"court_speed", "court_speed_index"}, "court_speed_context", "court_speed_missing_but_claimed", 18),
        ({"ball_type", "balls"}, "ball_type_context", "ball_type_missing_but_claimed", 14),
        ({"injury", "health"}, "injury_retirement_context", "injury_status_missing_but_claimed", 18),
        ({"retirement_risk", "withdrawal_risk"}, "injury_retirement_context", "retirement_risk_missing_but_claimed", 22),
        ({"weather", "conditions", "wind"}, "weather_conditions_context", "weather_conditions_missing_but_claimed", 14),
    ]
    for claim_names, group, reason, weight in checks:
        if claim_names & claimed and group not in available_groups:
            reasons.append(reason)
            downgrade += weight
    if "surface_split_small_sample_capped" in (surface.get("no_bet_reasons") or []) or source.get("surface_split_overfit"):
        reasons.append("surface_split_small_sample_overfit")
        downgrade += 14
    if "head_to_head_low_weight_sample_capped" in (matchup.get("no_bet_reasons") or []) and source.get("overconfidence_flag"):
        reasons.append("head_to_head_overfit")
        downgrade += 12
    if source.get("recent_form_weight", 0) and safe_float(source.get("recent_form_weight"), 0.0) > 0.35:
        reasons.append("recent_form_overfit")
        downgrade += 12
    if "tiebreak_record_sample_size_capped" in (pressure.get("no_bet_reasons") or []) and source.get("overconfidence_flag"):
        reasons.append("tiebreak_record_overfit")
        downgrade += 14
    if "break_point_conversion_noisy_volatility_capped" in (pressure.get("no_bet_reasons") or []) and source.get("overconfidence_flag"):
        reasons.append("break_point_conversion_overfit")
        downgrade += 12
    if incentive.get("narrative_overfit_risk") == "high" or source.get("clutch_narrative_overfit"):
        reasons.append("clutch_narrative_overfit")
        downgrade += 10
    if market in CORRECT_SCORE_MARKETS and (source.get("overconfidence_flag") or cal.get("calibration_status") != "calibration_ready"):
        reasons.append("correct_score_overconfidence")
        downgrade += 22
    if avail.get("retirement_risk_score", 0.0) >= 55 and source.get("ignores_retirement_risk"):
        reasons.append("retirement_risk_ignored")
        downgrade += 24
    if "best_of_missing_caps_correct_score_total_sets" in (fmt.get("no_bet_reasons") or []) and market in CORRECT_SCORE_MARKETS | {"total_sets"}:
        reasons.append("best_of_format_confusion")
        downgrade += 20
    if cal.get("calibration_status") == "insufficient_data":
        reasons.append("calibration_missing")
        missing.extend(cal.get("next_required_data") or ["settled_tennis_outcomes"])
        downgrade += 12
    for hard in (
        "serve_placement_missing_but_claimed",
        "shot_pattern_missing_but_claimed",
        "court_speed_missing_but_claimed",
        "injury_status_missing_but_claimed",
        "retirement_risk_missing_but_claimed",
        "weather_conditions_missing_but_claimed",
        "correct_score_overconfidence",
        "retirement_risk_ignored",
        "best_of_format_confusion",
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
    return finalize_tennis_response(
        {
            "red_team_status": "downgrade" if downgrade else "pass_review_only",
            "downgrade_score": round(clamp(downgrade), 2),
            "recommended_action_adjustment": adjustment,
            "no_bet_reasons": compact_list(no_bet, limit=20),
            "red_team_reasons": compact_list(reasons or ["no_red_team_hard_block"], limit=35),
            "missing_inputs": compact_list(missing, limit=20),
            "confidence_cap_reason": "red_team_downgrade" if downgrade else None,
            "red_team_only": True,
        },
        source_payload=source,
    )
