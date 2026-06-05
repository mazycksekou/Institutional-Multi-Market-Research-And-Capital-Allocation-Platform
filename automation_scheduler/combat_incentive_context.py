from __future__ import annotations

from typing import Any

from .combat_impact_common import boolish, clamp, compact_list, finalize_combat_response, score_from_range, weighted_average


def evaluate_combat_incentive_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    title = 70.0 if boolish(source.get("title_fight_context")) or boolish(source.get("title_eliminator_context")) else 0.0
    ranking = score_from_range(source.get("ranking_stakes_context"), low=0.0, high=1.0) or 0.0
    bonus = score_from_range(source.get("performance_bonus_motivation"), low=0.0, high=1.0) or 0.0
    retirement = score_from_range(source.get("retirement_announcement_context"), low=0.0, high=1.0) or 0.0
    rivalry = score_from_range(source.get("rivalry_context"), low=0.0, high=1.0) or score_from_range(source.get("grudge_match_context"), low=0.0, high=1.0) or 0.0
    urgency = score_from_range(source.get("post_loss_urgency_context"), low=0.0, high=1.0) or 0.0
    behavior = weighted_average(((title, 0.25), (ranking, 0.2), (bonus, 0.25), (urgency, 0.15), (rivalry, 0.15))) or 0.0
    finish_chase = weighted_average(((bonus, 0.45), (title, 0.2), (rivalry, 0.2), (urgency, 0.15))) or 0.0
    narrative = "low" if any(source.get(key) not in (None, "") for key in ("title_fight_context", "title_eliminator_context", "ranking_stakes_context", "performance_bonus_motivation")) else "high"
    no_bet = []
    if narrative == "high":
        no_bet.append("weak_incentive_evidence_narrative_overfit")
    if rivalry:
        no_bet.append("rivalry_grudge_context_volatility_only")
    if retirement:
        no_bet.append("retirement_or_shutdown_risk_modifier_only")
    return finalize_combat_response(
        {
            "incentive_context_status": "supplied" if narrative == "low" or rivalry or retirement else "unknown",
            "incentive_behavior_score": round(clamp(behavior), 2),
            "motivation_alignment_score": round(clamp(weighted_average(((title, 0.35), (ranking, 0.35), (100.0 - retirement, 0.2))) or 0.0), 2),
            "finish_chase_risk": round(clamp(finish_chase), 2),
            "narrative_overfit_risk": narrative,
            "retirement_or_shutdown_risk": round(clamp(retirement), 2),
            "confidence_modifier": -10.0 if narrative == "high" else 0.0,
            "market_relevance_modifier": {
                "method_market_adjustment": round(clamp(finish_chase) * 0.08, 2),
                "moneyline_confidence_adjustment": -5.0 if retirement else 0.0,
            },
            "incentive_is_standalone_edge": False,
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

