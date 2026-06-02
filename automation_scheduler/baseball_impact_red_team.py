from __future__ import annotations

from typing import Any

from .baseball_impact_common import PLAYER_PROP_MARKETS, clamp, compact_list, finalize_baseball_response, normalize_baseball_market


def evaluate_baseball_impact_red_team(
    *,
    market_type: str = "moneyline",
    data_availability: dict[str, Any] | None = None,
    run_value_impact: dict[str, Any] | None = None,
    pitcher_impact: dict[str, Any] | None = None,
    batter_impact: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    lineup_context: dict[str, Any] | None = None,
    bullpen_context: dict[str, Any] | None = None,
    park_weather_umpire_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    source_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    market = normalize_baseball_market(market_type)
    data = data_availability or {}
    rv = run_value_impact or {}
    pit = pitcher_impact or {}
    bat = batter_impact or {}
    matchup = matchup_context or {}
    lineup = lineup_context or {}
    bullpen = bullpen_context or {}
    park = park_weather_umpire_context or {}
    avail = availability_context or {}
    incentive = incentive_context or {}
    cal = calibration or {}
    source = source_payload or {}
    reasons: list[str] = []
    missing: list[str] = []
    no_bet: list[str] = []
    downgrade = 0.0
    available_groups = set(data.get("available_field_groups") or [])
    claimed = set(source.get("claimed_metrics") or source.get("model_claims") or [])
    if {"statcast", "xwoba", "barrel", "hard_hit"} & claimed and "contact_quality_context" not in available_groups:
        reasons.append("statcast_metric_missing_but_claimed")
        downgrade += 22
    if {"pitch_tracking", "spin", "movement", "extension"} & claimed and "pitch_tracking_context" not in available_groups:
        reasons.append("pitch_tracking_missing_but_claimed")
        downgrade += 22
    if {"bat_tracking", "bat_speed", "swing_length"} & claimed and "bat_tracking_context" not in available_groups:
        reasons.append("bat_tracking_missing_but_claimed")
        downgrade += 22
    if {"umpire", "umpire_tendency"} & claimed and "umpire_context" not in available_groups:
        reasons.append("umpire_tendency_missing_but_claimed")
        downgrade += 18
    lineup_reasons = set(lineup.get("no_bet_reasons") or [])
    pitcher_reasons = set(pit.get("no_bet_reasons") or [])
    availability_reasons = set(avail.get("no_bet_reasons") or [])
    if (
        (not lineup.get("confirmed_lineup", False) and market in PLAYER_PROP_MARKETS and (bat.get("batter_impact_score", 0.0) >= 50 or source.get("overconfidence_flag")))
        or source.get("overconfidence_flag") and {"lineup_unconfirmed_caps_batter_prop_confidence", "unconfirmed_lineup_caps_batter_prop_confidence"} & lineup_reasons
    ):
        reasons.append("lineup_unconfirmed_overconfidence")
        downgrade += 18
    if (
        avail.get("starter_certainty_score", 100.0) < 50 and (market.startswith("first_five") or market in {"pitcher_strikeouts", "pitcher_outs_recorded"})
        or {"starter_unconfirmed_caps_first_five_and_pitcher_props", "unconfirmed_starter_caps_pitcher_prop_and_first_five_confidence"} & pitcher_reasons
        or {"unconfirmed_starter_caps_pitcher_props_and_first_five", "unconfirmed_starter_caps_pitcher_prop_and_first_five_confidence"} & availability_reasons
    ):
        reasons.append("starter_unconfirmed_overconfidence")
        downgrade += 22
    if (
        avail.get("weather_delay_risk_score", 0.0) >= 60 and market in {"pitcher_strikeouts", "pitcher_outs_recorded"}
        or {"weather_delay_risk_can_break_pitcher_props", "weather_delay_breaks_pitcher_prop_confidence"} & availability_reasons
    ):
        reasons.append("weather_delay_pitcher_prop_risk")
        downgrade += 22
    if (
        {"pitch_count_limit_hard_warning_for_outs_and_strikeouts", "pitch_count_limit_caps_outs_and_strikeout_props"} & availability_reasons
        or {"pitch_count_limit_caps_outs_and_strikeout_props"} & pitcher_reasons
        or source.get("ignored_pitch_count_limit")
    ):
        reasons.append("pitch_count_limit_ignored")
        downgrade += 24
    if rv.get("insufficient_sample") and (rv.get("run_value_score", 0.0) >= 55 or source.get("split_sample_size", 100) < 30) or source.get("split_sample_size", 100) < 30:
        reasons.append("small_sample_split_overfit")
        downgrade += 16
    if "batter_vs_pitcher_history_low_weight_only" in (matchup.get("mismatch_reasons") or []) or source.get("batter_vs_pitcher_history_weight", 0) and source.get("batter_vs_pitcher_history_weight", 0) > 0.2:
        reasons.append("batter_vs_pitcher_history_overfit")
        downgrade += 12
    if source.get("recent_form_weight", 0) and source.get("recent_form_weight", 0) > 0.25:
        reasons.append("recent_form_overfit")
        downgrade += 10
    if park.get("confidence_cap_reason") == "weather_delay_risk" or source.get("park_weather_weight", 0) and source.get("park_weather_weight", 0) > 0.4:
        reasons.append("park_weather_overfit")
        downgrade += 10
    if incentive.get("narrative_overfit_risk") == "high":
        reasons.append("narrative_incentive_overfit")
        downgrade += 12
    if "bullpen_availability_missing_caps_full_game_confidence" in (bullpen.get("no_bet_reasons") or []) and market in {"moneyline", "runline", "total", "team_total"}:
        reasons.append("bullpen_availability_missing_overconfidence")
        downgrade += 12
    if cal.get("calibration_status") == "insufficient_data":
        reasons.append("calibration_missing")
        missing.extend(cal.get("next_required_data") or ["settled_outcomes"])
        downgrade += 12
    if source.get("uses_bullpen_for_first_five"):
        reasons.append("first_five_full_game_context_confusion")
        downgrade += 16
    if source.get("ignores_bullpen_for_full_game"):
        reasons.append("first_five_full_game_context_confusion")
        downgrade += 16
    for hard in (
        "statcast_metric_missing_but_claimed",
        "pitch_tracking_missing_but_claimed",
        "bat_tracking_missing_but_claimed",
        "starter_unconfirmed_overconfidence",
        "weather_delay_pitcher_prop_risk",
        "pitch_count_limit_ignored",
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
    return finalize_baseball_response(
        {
            "red_team_status": "downgrade" if downgrade else "pass_review_only",
            "downgrade_score": round(clamp(downgrade), 2),
            "recommended_action_adjustment": adjustment,
            "no_bet_reasons": compact_list(no_bet, limit=15),
            "red_team_reasons": compact_list(reasons or ["no_red_team_hard_block"], limit=25),
            "missing_inputs": compact_list(missing, limit=20),
            "confidence_cap_reason": "red_team_downgrade" if downgrade else None,
            "red_team_only": True,
        },
        source_payload=source,
    )
