from __future__ import annotations

from typing import Any

from .baseball_impact_common import boolish, clamp, compact_list, finalize_baseball_response, missing_fields, present_fields, score_from_range, weighted_average


INCENTIVE_INPUTS = (
    "contract_year",
    "known_bonus_thresholds",
    "bonus_progress_context",
    "award_race_context",
    "milestone_context",
    "playoff_elimination_status",
    "playoff_seeding_motivation",
    "record_chasing_context",
    "manager_public_comments",
    "rest_shutdown_risk",
    "callup_service_time_context",
    "rivalry_context",
    "revenge_narrative_context",
)


def _threshold(value: Any) -> tuple[float, bool]:
    if isinstance(value, dict):
        if "distance_to_threshold" in value:
            try:
                return clamp(100.0 - abs(float(value["distance_to_threshold"])) * 18.0), True
            except (TypeError, ValueError):
                return 55.0, True
        return 55.0, True
    if isinstance(value, list):
        return clamp(len(value) * 20.0), bool(value)
    if boolish(value):
        return 50.0, True
    return 0.0, False


def evaluate_baseball_incentive_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    present = present_fields(source, INCENTIVE_INPUTS)
    missing = missing_fields(source, INCENTIVE_INPUTS)
    if not present:
        return finalize_baseball_response(
            {
                "incentive_context_status": "unknown",
                "incentive_behavior_score": 0.0,
                "stat_chase_risk": 0.0,
                "team_alignment_score": 0.0,
                "narrative_overfit_risk": "unknown",
                "confidence_modifier": 0.0,
                "market_relevance_modifier": {"modifier_only": True},
                "no_bet_reasons": [],
                "incentive_is_standalone_edge": False,
                "bonus_threshold_fabricated": False,
                "missing_inputs": compact_list(missing, limit=25),
            },
            source_payload=source,
        )
    bonus, known_bonus = _threshold(source.get("known_bonus_thresholds") or source.get("bonus_progress_context"))
    milestone, _ = _threshold(source.get("milestone_context"))
    stat_chase = weighted_average(((bonus, 0.55), (milestone, 0.55), (score_from_range(source.get("award_race_context"), low=0.0, high=100.0), 0.35), (score_from_range(source.get("record_chasing_context"), low=0.0, high=100.0), 0.35))) or 0.0
    team_alignment = weighted_average(((score_from_range(source.get("playoff_seeding_motivation"), low=0.0, high=100.0), 0.65), (100.0 - (score_from_range(source.get("rest_shutdown_risk"), low=0.0, high=100.0) or 0.0), 0.45), (100.0 - (score_from_range(source.get("callup_service_time_context"), low=0.0, high=100.0) or 0.0), 0.25), (score_from_range(source.get("rivalry_context"), low=0.0, high=100.0), 0.15)))
    contract = 65.0 if boolish(source.get("contract_year")) else 0.0
    behavior = weighted_average(((contract, 0.3), (stat_chase, 0.45), (team_alignment, 0.35))) or 0.0
    weak = len(present) < 3 or (boolish(source.get("known_bonus_thresholds")) and not known_bonus) or score_from_range(source.get("revenge_narrative_context"), low=0.0, high=100.0)
    narrative = "high" if weak else "moderate" if len(present) < 5 else "low"
    confidence = -12.0 if narrative == "high" else -4.0 if narrative == "moderate" else 3.0
    no_bet = []
    if narrative == "high":
        no_bet.append("weak_incentive_evidence_narrative_overfit_risk")
    if boolish(source.get("known_bonus_thresholds")) and not known_bonus:
        no_bet.append("bonus_threshold_unknown_not_fabricated")
    return finalize_baseball_response(
        {
            "incentive_context_status": "modifier_only",
            "incentive_behavior_score": round(clamp(behavior), 2),
            "stat_chase_risk": round(clamp(stat_chase), 2),
            "team_alignment_score": round(clamp(team_alignment or 0.0), 2),
            "narrative_overfit_risk": narrative,
            "confidence_modifier": round(confidence, 2),
            "market_relevance_modifier": {
                "player_prop_relevance_adjustment": 5.0 if stat_chase >= 60.0 and (team_alignment or 0.0) >= 35.0 else 0.0,
                "team_market_confidence_adjustment": -8.0 if stat_chase >= 60.0 and (team_alignment or 0.0) < 45.0 else 0.0,
                "modifier_only": True,
            },
            "no_bet_reasons": compact_list(no_bet, limit=10),
            "incentive_is_standalone_edge": False,
            "bonus_threshold_fabricated": False,
            "missing_inputs": compact_list(missing, limit=25),
        },
        source_payload=source,
    )
