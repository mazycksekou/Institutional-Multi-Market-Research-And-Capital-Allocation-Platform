from __future__ import annotations

from typing import Any

from .football_impact_schema import boolish, clamp, compact_list, finalize_football_response, missing_fields, present_fields, score_from_range, weighted_average


INCENTIVE_INPUTS = (
    "contract_year",
    "known_bonus_thresholds",
    "award_race_context",
    "playoff_elimination_status",
    "seeding_motivation",
    "record_chasing_context",
    "coach_public_comments",
    "rest_shutdown_risk",
    "tanking_or_draft_context",
    "rivalry_context",
    "revenge_narrative_context",
)


def _threshold_pressure(value: Any) -> tuple[float, bool]:
    if isinstance(value, dict):
        if "distance_to_threshold" in value:
            try:
                distance = abs(float(value.get("distance_to_threshold")))
            except (TypeError, ValueError):
                distance = 4.0
            return clamp(100.0 - distance * 18.0), True
        return 60.0, True
    if isinstance(value, list):
        return clamp(min(len(value), 4) * 22.0), bool(value)
    if boolish(value):
        return 55.0, True
    return 0.0, False


def evaluate_football_incentive_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    present = present_fields(source, INCENTIVE_INPUTS)
    missing = missing_fields(source, INCENTIVE_INPUTS)
    if not present:
        return finalize_football_response(
            {
                "incentive_context_status": "unknown",
                "incentive_behavior_score": 0.0,
                "stat_chase_risk": 0.0,
                "team_alignment_score": 0.0,
                "narrative_overfit_risk": "unknown",
                "confidence_modifier": 0.0,
                "no_bet_reasons": [],
                "incentive_is_standalone_edge": False,
                "bonus_threshold_fabricated": False,
                "known_bonus_threshold_present": False,
                "missing_inputs": compact_list(missing, limit=25),
            },
            source_payload=source,
        )
    bonus_pressure, threshold_known = _threshold_pressure(source.get("known_bonus_thresholds"))
    contract_pressure = weighted_average(((70.0 if boolish(source.get("contract_year")) else 0.0, 0.45), (bonus_pressure, 0.75)))
    award_pressure = score_from_range(source.get("award_race_context"), low=0.0, high=100.0)
    record_pressure = score_from_range(source.get("record_chasing_context"), low=0.0, high=100.0)
    seeding = score_from_range(source.get("seeding_motivation"), low=0.0, high=100.0)
    elimination_raw = str(source.get("playoff_elimination_status") or "").strip().lower()
    eliminated = elimination_raw in {"eliminated", "out", "no_playoffs", "true"}
    shutdown = score_from_range(source.get("rest_shutdown_risk"), low=0.0, high=100.0)
    tanking = score_from_range(source.get("tanking_or_draft_context"), low=0.0, high=100.0)
    rivalry = score_from_range(source.get("rivalry_context"), low=0.0, high=100.0)
    revenge = score_from_range(source.get("revenge_narrative_context"), low=0.0, high=100.0)
    comment_signal = 45.0 if source.get("coach_public_comments") not in (None, "", []) else None

    stat_chase = weighted_average(((bonus_pressure, 0.75), (award_pressure, 0.4), (record_pressure, 0.55), (comment_signal, 0.15))) or 0.0
    team_alignment = weighted_average(
        (
            (seeding, 0.75),
            (100.0 - (shutdown or 0.0), 0.45),
            (100.0 - (tanking or 0.0), 0.45),
            (rivalry, 0.2),
            (35.0 if eliminated else 75.0 if elimination_raw else None, 0.35),
        )
    )
    behavior = weighted_average(((contract_pressure, 0.35), (stat_chase, 0.45), (team_alignment, 0.4), (rivalry, 0.15))) or 0.0
    weak_evidence = len(present) < 3 or (not threshold_known and stat_chase >= 40.0)
    narrative_overfit = "high" if weak_evidence or (revenge or 0.0) >= 60.0 else "moderate" if len(present) < 5 else "low"
    confidence_modifier = 0.0
    if narrative_overfit == "low":
        confidence_modifier = 4.0
    elif narrative_overfit == "moderate":
        confidence_modifier = -3.0
    else:
        confidence_modifier = -12.0
    if (shutdown or 0.0) >= 65.0 or (tanking or 0.0) >= 65.0:
        confidence_modifier -= 8.0

    no_bet = []
    if narrative_overfit == "high":
        no_bet.append("weak_incentive_evidence_narrative_overfit_risk")
    if (shutdown or 0.0) >= 65.0:
        no_bet.append("rest_shutdown_risk_caps_props_and_team_markets")
    if (tanking or 0.0) >= 65.0:
        no_bet.append("draft_incentive_or_tanking_context_caps_team_market_confidence")
    if boolish(source.get("known_bonus_thresholds")) and not threshold_known:
        no_bet.append("bonus_threshold_claim_not_verified")

    return finalize_football_response(
        {
            "incentive_context_status": "unknown" if not present else "modifier_only",
            "incentive_behavior_score": round(clamp(behavior), 2),
            "stat_chase_risk": round(clamp(stat_chase), 2),
            "team_alignment_score": round(clamp(team_alignment or 0.0), 2),
            "narrative_overfit_risk": narrative_overfit,
            "confidence_modifier": round(confidence_modifier, 2),
            "no_bet_reasons": compact_list(no_bet, limit=10),
            "incentive_is_standalone_edge": False,
            "bonus_threshold_fabricated": False,
            "known_bonus_threshold_present": bool(threshold_known),
            "missing_inputs": compact_list(missing, limit=25),
        },
        source_payload=source,
    )
