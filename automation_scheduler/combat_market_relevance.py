from __future__ import annotations

from typing import Any

from .combat_impact_common import BOXING_PROP_MARKETS, FIGHTER_PROP_MARKETS, METHOD_MARKETS, MONEYLINE_MARKETS, ROUND_TOTAL_MARKETS, clamp, compact_list, finalize_combat_response, normalize_combat_market, score_from_range, weighted_average


def _score(payload: dict[str, Any] | None, key: str) -> float:
    if not isinstance(payload, dict):
        return 0.0
    return clamp(payload.get(key, 0.0) or 0.0)


def _top(scores: dict[str, float], threshold: float = 55.0) -> list[str]:
    return [market for market, value in sorted(scores.items(), key=lambda item: item[1], reverse=True) if value >= threshold][:12]


def evaluate_combat_market_relevance(
    row: dict[str, Any] | None = None,
    *,
    market_type: str | None = None,
    striking_impact: dict[str, Any] | None = None,
    grappling_control_impact: dict[str, Any] | None = None,
    phase_control_context: dict[str, Any] | None = None,
    damage_durability_context: dict[str, Any] | None = None,
    pace_cardio_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    ruleset_referee_judging_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    market = normalize_combat_market(market_type or source.get("market_type") or "moneyline")
    striking = striking_impact or {}
    grappling = grappling_control_impact or {}
    phase = phase_control_context or {}
    damage = damage_durability_context or {}
    pace = pace_cardio_context or {}
    matchup = matchup_context or {}
    avail = availability_context or {}
    rules = ruleset_referee_judging_context or {}
    incentive = incentive_context or {}

    strike = _score(striking, "striking_impact_score")
    strike_prop = _score(striking, "striking_prop_relevance")
    ko = _score(striking, "ko_tko_relevance_modifier")
    boxing = _score(striking, "boxing_punch_profile_score")
    grapple = _score(grappling, "grappling_impact_score")
    sub = _score(grappling, "submission_relevance_modifier")
    control = _score(grappling, "control_time_score")
    decision_control = _score(grappling, "decision_relevance_modifier")
    phase_score = _score(phase, "phase_control_score")
    phase_mod = _score(phase, "market_relevance_modifier")
    dmg = _score(damage, "damage_threat_score")
    durability_risk = _score(damage, "durability_risk_score")
    finish_vol = _score(damage, "finish_volatility_score")
    pace_score = _score(pace, "pace_score")
    cardio = _score(pace, "cardio_score")
    late_risk = _score(pace, "late_fight_risk_score")
    over_mod = _score(pace, "over_under_rounds_modifier")
    match = _score(matchup, "matchup_advantage_score")
    match_risk = _score(matchup, "matchup_risk_score")
    availability = _score(avail, "availability_score")
    fight_week_risk = max(_score(avail, "injury_risk_score"), _score(avail, "weight_cut_risk_score"), _score(avail, "short_notice_risk_score"))
    ruleset = _score(rules, "ruleset_context_score")
    five = _score(rules, "five_round_context_score")
    ref_stop = _score(rules, "referee_stoppage_modifier")
    judging = _score(rules, "judging_volatility_score")
    method_adj = 0.0
    if isinstance(incentive.get("market_relevance_modifier"), dict):
        method_adj = float(incentive["market_relevance_modifier"].get("method_market_adjustment", 0.0) or 0.0)

    moneyline = weighted_average(((strike, 0.22), (grapple, 0.22), (phase_score, 0.16), (100.0 - durability_risk, 0.12), (cardio, 0.12), (availability, 0.12), (match, 0.18), (100.0 - match_risk, 0.08))) or 0.0
    ko_score = weighted_average(((ko, 0.35), (dmg, 0.3), (durability_risk, 0.25), (ref_stop, 0.1))) or 0.0
    sub_score = weighted_average(((sub, 0.45), (control, 0.25), (grapple, 0.2), (100.0 - match_risk, 0.1))) or 0.0
    decision_score = weighted_average(((decision_control, 0.35), (100.0 - finish_vol, 0.25), (cardio, 0.2), (100.0 - judging, 0.1))) or 0.0
    not_distance = weighted_average(((ko_score, 0.35), (sub_score, 0.3), (finish_vol, 0.25), (late_risk, 0.1))) or 0.0
    distance = weighted_average(((100.0 - not_distance, 0.4), (decision_score, 0.35), (cardio, 0.2), (100.0 - ref_stop, 0.1))) or 0.0
    over_rounds = weighted_average(((over_mod, 0.35), (distance, 0.3), (control, 0.15), (100.0 - finish_vol, 0.2))) or 0.0
    under_rounds = weighted_average(((not_distance, 0.45), (finish_vol, 0.25), (pace_score, 0.15), (late_risk, 0.15))) or 0.0
    exact_round = weighted_average(((under_rounds, 0.3), (late_risk, 0.2), (five, 0.1), (score_from_range(source.get("round_timing_sample_size"), low=0.0, high=150.0) or 0.0, 0.2))) or 0.0
    scores = {
        "moneyline": moneyline,
        "fight_winner": moneyline,
        "method_of_victory": clamp(max(ko_score, sub_score, decision_score) + method_adj),
        "ko_tko": ko_score,
        "submission": sub_score,
        "decision": decision_score,
        "draw": max(0.0, judging * 0.35),
        "fight_goes_distance": distance,
        "fight_does_not_go_distance": not_distance,
        "over_rounds": over_rounds,
        "under_rounds": under_rounds,
        "exact_round": exact_round,
        "round_group": exact_round,
        "winning_method_round": weighted_average(((exact_round, 0.45), (max(ko_score, sub_score), 0.35))) or 0.0,
        "inside_distance": not_distance,
        "points_decision": decision_score,
        "split_decision": max(0.0, judging * 0.65),
        "unanimous_decision": max(0.0, decision_score - judging * 0.2),
        "fighter_significant_strikes": weighted_average(((strike_prop, 0.45), (pace_score, 0.25), (phase_mod, 0.15), (100.0 - grapple, 0.1))) or 0.0,
        "fighter_total_strikes": weighted_average(((strike_prop, 0.35), (pace_score, 0.3), (distance, 0.2))) or 0.0,
        "fighter_takedowns": weighted_average(((grapple, 0.35), (_score(grappling, "takedown_threat_score"), 0.35), (distance, 0.1))) or 0.0,
        "fighter_takedown_attempts": weighted_average(((_score(grappling, "takedown_threat_score"), 0.45), (pace_score, 0.2), (100.0 - _score(grappling, "takedown_defense_score"), 0.2))) or 0.0,
        "fighter_submission_attempts": sub_score,
        "fighter_control_time": weighted_average(((control, 0.45), (grapple, 0.3), (distance, 0.15))) or 0.0,
        "fighter_knockdowns": ko_score,
        "fighter_round_1_finish": weighted_average(((ko_score, 0.35), (sub_score, 0.2), (_score(striking, "volume_score"), 0.2))) or 0.0,
        "fighter_round_2_finish": under_rounds,
        "fighter_round_3_finish": weighted_average(((late_risk, 0.25), (not_distance, 0.3), (cardio, 0.1))) or 0.0,
        "fighter_round_4_5_finish": weighted_average(((late_risk, 0.35), (five, 0.35), (not_distance, 0.2))) or 0.0,
        "performance_bonus_style_prop": clamp(max(ko_score, sub_score) + method_adj),
        "fighter_jabs_landed": weighted_average(((boxing, 0.4), (pace_score, 0.25), (distance, 0.2))) or 0.0,
        "fighter_power_punches_landed": weighted_average(((boxing, 0.35), (ko_score, 0.3), (pace_score, 0.15))) or 0.0,
        "fighter_total_punches_landed": weighted_average(((boxing, 0.35), (pace_score, 0.3), (distance, 0.2), (strike_prop, 0.15))) or 0.0,
        "knockdowns": ko_score,
        "stoppage": ko_score,
    }
    scores = {key: round(clamp(value), 2) for key, value in scores.items()}
    caps = {}
    no_bet = []
    if market in {"exact_round", "winning_method_round"}:
        caps["exact_round"] = "extra_conservative_calibration_required"
        no_bet.append("exact_round_market_heavily_calibration_capped")
    if market == "split_decision":
        caps["split_decision"] = "judging_volatility_and_sample_cap"
        no_bet.append("split_decision_market_extra_conservative")
    if fight_week_risk >= 60:
        caps["fight_week_uncertainty"] = "injury_weight_cut_short_notice_cap"
        no_bet.append("fight_week_uncertainty_caps_market_confidence")
    return finalize_combat_response(
        {
            "market_relevance_scores": scores,
            "strongest_market_links": compact_list(_top(scores), limit=12),
            "weak_market_links": [key for key, value in scores.items() if value < 35.0][:12],
            "no_bet_market_reasons": compact_list(no_bet, limit=20),
            "moneyline_relevance": round(max((scores.get(key, 0.0) for key in MONEYLINE_MARKETS), default=0.0), 2),
            "method_relevance": round(max((scores.get(key, 0.0) for key in METHOD_MARKETS), default=0.0), 2),
            "round_total_relevance": round(max((scores.get(key, 0.0) for key in ROUND_TOTAL_MARKETS), default=0.0), 2),
            "distance_relevance": round(max(scores.get("fight_goes_distance", 0.0), scores.get("fight_does_not_go_distance", 0.0)), 2),
            "fighter_prop_relevance": round(max((scores.get(key, 0.0) for key in FIGHTER_PROP_MARKETS), default=0.0), 2),
            "boxing_prop_relevance": round(max((scores.get(key, 0.0) for key in BOXING_PROP_MARKETS), default=0.0), 2),
            "market_confidence_caps": caps,
            "selected_market_type": market,
            "selected_market_relevance_score": scores.get(market, 0.0),
            "edge_fabricated": False,
        },
        source_payload=source,
    )

