from __future__ import annotations

from typing import Any

from .bookmaker_normalizer import normalize_offer
from .cross_book_line_comparator import compare_cross_book_lines
from .market_identity_resolver import resolve_market_identity
from .odds_math import american_to_implied_probability, calculate_ev, calculate_roi


def shop_ev_lines(
    offers: list[dict[str, Any]],
    *,
    model_probability: float | None,
    stake: float = 100.0,
    stale_data_risk: bool = False,
) -> dict[str, Any]:
    if model_probability is None:
        return {"candidate_found": False, "reason": "model_probability_required", "ranked_offers": []}
    if stale_data_risk:
        return {"candidate_found": False, "reason": "stale_data", "ranked_offers": []}

    normalized = [normalize_offer(offer) for offer in offers if isinstance(offer, dict)]
    ranked = []
    for offer in normalized:
        if offer.get("odds") in (None, 0):
            continue
        implied_probability = american_to_implied_probability(offer["odds"])
        ev_value = calculate_ev(stake, model_probability, offer["odds"])
        roi = calculate_roi(stake, ev_value)
        ranked.append(
            {
                **offer,
                "model_probability": round(float(model_probability), 6),
                "implied_probability": round(implied_probability, 6),
                "ev_percent": round((ev_value / stake) * 100.0, 6),
                "estimated_roi_percent": round(roi, 6),
                "candidate_type": "positive_ev" if ev_value > 0 else "best_line_available",
                "human_approval_required": True,
                "auto_execution_enabled": False,
                "auto_bet_enabled": False,
                "auto_trade_enabled": False,
            }
        )
    ranked.sort(key=lambda row: (row["ev_percent"], row["odds"]), reverse=True)
    comparator = compare_cross_book_lines(ranked)
    best = ranked[0] if ranked else None
    if not best or best["ev_percent"] <= 0:
        return {
            "candidate_found": False,
            "reason": "no_positive_ev",
            "ranked_offers": ranked,
            "best_line_available": best,
        }

    confidences = []
    for index in range(len(ranked) - 1):
        for other in range(index + 1, len(ranked)):
            confidences.append(resolve_market_identity(ranked[index], ranked[other])["confidence"])
    best["candidate_type"] = "best_line_available"
    best["best_line_available"] = True
    best["books_compared"] = comparator["books_compared"]
    best["best_book"] = comparator["best_book"]
    best["best_line"] = comparator["best_line"]
    best["best_odds"] = comparator["best_odds"]
    best["line_match_confidence"] = round(sum(confidences) / len(confidences), 2) if confidences else 100.0
    best["book_disagreement_score"] = comparator["book_disagreement_score"]
    best["stale_data_risk"] = False
    return {
        "candidate_found": True,
        "ranked_offers": ranked,
        "best_line_available": best,
    }
