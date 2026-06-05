from __future__ import annotations

from typing import Any

from .combat_impact_common import boolish, categorical_score, clamp, compact_list, finalize_combat_response, missing_fields, score_from_range, weighted_average


RULESET_FIELDS = ("organization", "ruleset", "scheduled_rounds", "cage_or_ring", "referee_stoppage_tendency", "judging_variance_proxy")


def evaluate_combat_ruleset_referee_judging_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    ruleset_raw = str(source.get("ruleset") or source.get("sport") or "").strip().lower()
    is_boxing = ruleset_raw == "boxing"
    scheduled_rounds = score_from_range(source.get("scheduled_rounds"), low=3.0 if not is_boxing else 4.0, high=5.0 if not is_boxing else 12.0) or 0.0
    five_round = 85.0 if boolish(source.get("title_fight")) or boolish(source.get("main_event")) or str(source.get("scheduled_rounds")) == "5" else 0.0
    rule_context = weighted_average(
        (
            (scheduled_rounds, 0.35),
            (categorical_score(source.get("cage_or_ring"), {"cage": 65.0, "ring": 55.0}, 45.0), 0.15),
            (categorical_score(source.get("ruleset"), {"mma": 65.0, "ufc": 70.0, "boxing": 60.0}, 45.0), 0.25),
            (score_from_range(source.get("glove_size"), low=4.0, high=12.0), 0.1),
        )
    )
    ref_stop = score_from_range(source.get("referee_stoppage_tendency"), low=0.0, high=1.0) or 0.0
    ref_standup = score_from_range(source.get("referee_standup_tendency"), low=0.0, high=1.0) or 0.0
    judging = weighted_average(((score_from_range(source.get("judging_variance_proxy"), low=0.0, high=1.0), 0.45), (score_from_range(source.get("split_decision_rate_proxy"), low=0.0, high=1.0), 0.35), (score_from_range(source.get("hometown_or_regional_bias_proxy"), low=0.0, high=1.0), 0.2))) or 0.0
    decision_risk = weighted_average(((judging, 0.55), (100.0 - ref_stop, 0.15), (score_from_range(source.get("scheduled_rounds"), low=3.0, high=12.0), 0.2))) or 0.0
    no_bet = []
    if source.get("referee_stoppage_tendency") in (None, ""):
        no_bet.append("referee_stoppage_tendency_missing_not_fabricated")
    if source.get("referee_standup_tendency") in (None, ""):
        no_bet.append("referee_standup_tendency_missing_not_fabricated")
    if source.get("judging_variance_proxy") in (None, ""):
        no_bet.append("judge_tendency_missing_not_fabricated")
    if judging >= 55:
        no_bet.append("judging_volatility_caps_decision_split_markets")
    return finalize_combat_response(
        {
            "ruleset_context_score": round(clamp(rule_context or 0.0), 2),
            "five_round_context_score": round(clamp(five_round), 2),
            "referee_stoppage_modifier": round(clamp(ref_stop), 2),
            "referee_standup_modifier": round(clamp(ref_standup), 2),
            "judging_volatility_score": round(clamp(judging), 2),
            "decision_market_risk_score": round(clamp(decision_risk), 2),
            "draw_or_split_decision_risk_score": round(clamp(weighted_average(((judging, 0.65), (score_from_range(source.get("split_decision_rate_proxy"), low=0.0, high=1.0), 0.25))) or 0.0), 2),
            "ruleset": "boxing" if is_boxing else "mma" if ruleset_raw in {"mma", "ufc", "ufc_mma"} else ruleset_raw or "unknown",
            "referee_tendency_fabricated": False,
            "judge_tendency_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, RULESET_FIELDS), limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

