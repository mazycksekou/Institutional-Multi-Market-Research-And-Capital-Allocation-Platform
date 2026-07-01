from __future__ import annotations

from typing import Any

from .soccer_impact_common import boolish, clamp, compact_list, finalize_soccer_response, score_from_range, weighted_average


def evaluate_soccer_incentive_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    known_bonus = source.get("known_bonus_thresholds") not in (None, "", [])
    weak_narrative = bool(source.get("rivalry_context") or source.get("revenge_narrative_context") or source.get("manager_public_comments")) and not known_bonus
    stat_chase = weighted_average(((70.0 if known_bonus else 0.0, 0.25), (score_from_range(source.get("golden_boot_context"), low=0, high=1), 0.35), (score_from_range(source.get("assist_leader_context"), low=0, high=1), 0.25), (score_from_range(source.get("bonus_progress_context"), low=0, high=1), 0.25), (score_from_range(source.get("award_race_context"), low=0, high=1), 0.2)))
    team_alignment = weighted_average(((score_from_range(source.get("promotion_race_context"), low=0, high=1), 0.3), (score_from_range(source.get("relegation_risk_context"), low=0, high=1), 0.3), (score_from_range(source.get("title_race_context"), low=0, high=1), 0.25), (score_from_range(source.get("top_four_context"), low=0, high=1), 0.25), (score_from_range(source.get("fixture_priority"), low=0, high=1), 0.3))) or 30.0
    rotation_risk = weighted_average(((score_from_range(source.get("cup_rotation_context"), low=0, high=1), 0.45), (score_from_range(source.get("rest_shutdown_risk"), low=0, high=1), 0.35), (score_from_range(source.get("fixture_priority"), low=0, high=1, inverse=True), 0.3))) or 0.0
    behavior = weighted_average(((stat_chase, 0.35), (team_alignment, 0.35), (100.0 - rotation_risk, 0.15), (55.0 if boolish(source.get("contract_year")) else 0.0, 0.1))) or 0.0
    narrative_risk = "high" if weak_narrative or not known_bonus else "moderate" if source else "unknown"
    no_bet = []
    if not known_bonus:
        no_bet.append("bonus_threshold_unknown_not_fabricated")
    if weak_narrative:
        no_bet.append("weak_narrative_context")
    if rotation_risk >= 55:
        no_bet.append("cup_rotation_or_fixture_priority_caps_lineup_confidence")
    return finalize_soccer_response(
        {
            "incentive_context_status": "modifier_ready" if source else "unknown",
            "incentive_behavior_score": round(clamp(behavior), 2),
            "stat_chase_risk": round(clamp(stat_chase or 0.0), 2),
            "team_alignment_score": round(clamp(team_alignment), 2),
            "rotation_motivation_risk": round(clamp(rotation_risk), 2),
            "narrative_overfit_risk": narrative_risk,
            "confidence_modifier": round(-10.0 if narrative_risk == "high" else 4.0 if known_bonus else 0.0, 2),
            "market_relevance_modifier": {
                "player_prop_relevance_adjustment": round(8.0 if (stat_chase or 0.0) >= 55 else 0.0, 2),
                "team_market_confidence_adjustment": round(-7.0 if rotation_risk >= 55 or ((stat_chase or 0.0) >= 55 and team_alignment < 45) else 0.0, 2),
            },
            "incentive_is_standalone_edge": False,
            "bonus_threshold_fabricated": False,
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )
