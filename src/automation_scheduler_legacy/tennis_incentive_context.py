from __future__ import annotations

from typing import Any

from .tennis_impact_common import clamp, compact_list, finalize_tennis_response, missing_fields, percent_score, weighted_average


INCENTIVE_INPUTS = (
    "ranking_points_context",
    "race_points_context",
    "defending_points_context",
    "tour_finals_context",
    "grand_slam_context",
    "davis_cup_billie_jean_king_cup_context",
    "home_country_context",
    "wild_card_context",
    "protected_ranking_context",
    "comeback_from_injury_context",
    "retirement_announcement_context",
    "contract_sponsor_context",
    "public_comments",
    "tanking_or_low_motivation_context",
    "schedule_priority_context",
)


def _context_score(value: Any, *, default: float = 58.0) -> float | None:
    if value in (None, "", [], False):
        return None
    numeric = percent_score(value)
    return numeric if numeric is not None else default


def evaluate_tennis_incentive_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    supplied = [key for key in INCENTIVE_INPUTS if source.get(key) not in (None, "", [])]
    motivation = weighted_average(
        (
            (_context_score(source.get("ranking_points_context")), 0.35),
            (_context_score(source.get("race_points_context")), 0.35),
            (_context_score(source.get("defending_points_context")), 0.25),
            (_context_score(source.get("tour_finals_context")), 0.25),
            (_context_score(source.get("grand_slam_context")), 0.25),
            (_context_score(source.get("davis_cup_billie_jean_king_cup_context")), 0.2),
            (_context_score(source.get("home_country_context"), default=55.0), 0.2),
            (_context_score(source.get("wild_card_context"), default=52.0), 0.12),
            (_context_score(source.get("protected_ranking_context"), default=50.0), 0.12),
            (_context_score(source.get("comeback_from_injury_context"), default=45.0), 0.1),
            (_context_score(source.get("schedule_priority_context"), default=58.0), 0.2),
        )
    )
    retirement_shutdown = weighted_average(((_context_score(source.get("retirement_announcement_context"), default=60.0), 0.35), (_context_score(source.get("tanking_or_low_motivation_context"), default=72.0), 0.45)))
    narrative = "unknown"
    if supplied:
        narrative = "high" if len(supplied) < 2 else "moderate" if len(supplied) < 4 else "low"
    confidence_modifier = 0.0
    if motivation is not None:
        confidence_modifier += min((motivation - 50.0) / 10.0, 6.0)
    if retirement_shutdown:
        confidence_modifier -= min(retirement_shutdown / 8.0, 10.0)
    no_bet: list[str] = []
    if supplied and len(supplied) < 2:
        no_bet.append("weak_incentive_evidence_narrative_overfit_risk")
    if retirement_shutdown:
        no_bet.append("retirement_or_low_motivation_risk_modifier_only")
    return finalize_tennis_response(
        {
            "incentive_context_status": "modifier_only" if supplied else "unknown",
            "incentive_behavior_score": round(clamp(motivation or 0.0), 2),
            "motivation_alignment_score": round(clamp(motivation or 0.0), 2),
            "narrative_overfit_risk": narrative,
            "retirement_or_shutdown_risk": round(clamp(retirement_shutdown or 0.0), 2),
            "confidence_modifier": round(confidence_modifier, 2),
            "market_relevance_modifier": {
                "match_market_adjustment": round(max(confidence_modifier, 0.0), 2),
                "retirement_shutdown_adjustment": round(min(confidence_modifier, 0.0), 2),
                "modifier_only": True,
            },
            "incentive_is_standalone_edge": False,
            "motivation_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, INCENTIVE_INPUTS), limit=35),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )
