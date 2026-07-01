from __future__ import annotations

from typing import Any

from .golf_impact_common import boolish, clamp, compact_list, finalize_golf_response, missing_fields, percent_score, weighted_average


INCENTIVE_INPUTS = (
    "fedex_cup_context",
    "race_to_dubai_context",
    "ryder_cup_context",
    "presidents_cup_context",
    "olympic_context",
    "major_exemption_context",
    "tour_card_status",
    "sponsor_invite_context",
    "home_event_context",
    "defending_champion_context",
    "record_chasing_context",
    "milestone_context",
    "public_comments",
    "withdrawal_incentive",
    "tune_up_event_context",
)


def _context_score(value: Any, *, default: float = 60.0) -> float | None:
    if value in (None, "", [], False):
        return None
    numeric = percent_score(value)
    if numeric is not None:
        return numeric
    return default


def evaluate_golf_incentive_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    supplied = [key for key in INCENTIVE_INPUTS if source.get(key) not in (None, "", [])]
    motivation = weighted_average(
        (
            (_context_score(source.get("fedex_cup_context")), 0.35),
            (_context_score(source.get("race_to_dubai_context")), 0.35),
            (_context_score(source.get("ryder_cup_context")), 0.25),
            (_context_score(source.get("presidents_cup_context")), 0.25),
            (_context_score(source.get("olympic_context")), 0.2),
            (_context_score(source.get("major_exemption_context")), 0.25),
            (_context_score(source.get("tour_card_status"), default=65.0), 0.3),
            (_context_score(source.get("home_event_context"), default=55.0), 0.2),
            (_context_score(source.get("defending_champion_context"), default=55.0), 0.15),
        )
    )
    narrative = 35.0 if len(supplied) >= 2 else 80.0 if supplied else 0.0
    withdrawal_tuneup = weighted_average(((percent_score(source.get("withdrawal_incentive")), 0.45), (55.0 if boolish(source.get("tune_up_event_context")) else None, 0.35)))
    confidence_modifier = 0.0
    if motivation is not None:
        confidence_modifier += min((motivation - 50.0) / 10.0, 6.0)
    if withdrawal_tuneup:
        confidence_modifier -= min(withdrawal_tuneup / 8.0, 10.0)
    no_bet: list[str] = []
    if supplied and len(supplied) < 2:
        no_bet.append("weak_incentive_evidence_narrative_overfit_risk")
    if withdrawal_tuneup:
        no_bet.append("withdrawal_or_tuneup_risk_lowers_confidence")
    return finalize_golf_response(
        {
            "incentive_context_status": "modifier_only" if supplied else "unknown",
            "incentive_behavior_score": round(clamp(motivation or 0.0), 2),
            "motivation_alignment_score": round(clamp(motivation or 0.0), 2),
            "narrative_overfit_risk": "high" if narrative >= 70 else "moderate" if narrative >= 40 else "low" if supplied else "unknown",
            "withdrawal_or_tuneup_risk": round(clamp(withdrawal_tuneup or 0.0), 2),
            "confidence_modifier": round(confidence_modifier, 2),
            "market_relevance_modifier": {
                "cut_top_finish_adjustment": round(max(confidence_modifier, 0.0), 2),
                "outright_confidence_adjustment": round(confidence_modifier - (withdrawal_tuneup or 0.0) / 20.0, 2),
                "modifier_only": True,
            },
            "incentive_is_standalone_edge": False,
            "motivation_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, INCENTIVE_INPUTS), limit=30),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )
