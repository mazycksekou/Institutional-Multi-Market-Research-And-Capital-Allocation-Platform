from __future__ import annotations

from typing import Any

from .bookmaker_normalizer import normalize_offer
from .clv_tracker import build_clv_record
from .cross_book_line_comparator import compare_cross_book_lines
from .market_identity_resolver import resolve_market_identity
from .odds_math import american_to_implied_probability, calculate_ev, calculate_roi
from .no_vig_pricing import calculate_consensus_probability


def _ev_candidate(
    offer: dict[str, Any],
    *,
    stake: float,
    probability: float | None,
    candidate_type: str,
    probability_field: str,
) -> dict[str, Any]:
    if probability is None:
        return {}
    implied_probability = american_to_implied_probability(offer["odds"])
    ev_value = calculate_ev(stake, probability, offer["odds"])
    return {
        **offer,
        probability_field: round(float(probability), 6),
        "implied_probability": round(implied_probability, 6),
        "ev_percent": round((ev_value / stake) * 100.0, 6),
        "estimated_roi_percent": round(calculate_roi(stake, ev_value), 6),
        "candidate_type": candidate_type,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
    }


def model_ev(offers: list[dict[str, Any]], *, model_probability: float | None, stake: float = 100.0) -> dict[str, Any]:
    return shop_ev_lines(offers, model_probability=model_probability, stake=stake)


def no_vig_market_ev(offers: list[dict[str, Any]], *, fair_probability: float | None, stake: float = 100.0) -> dict[str, Any]:
    normalized = [normalize_offer(offer) for offer in offers if isinstance(offer, dict)]
    ranked = [_ev_candidate(offer, stake=stake, probability=fair_probability, candidate_type="no_vig_ev", probability_field="no_vig_probability") for offer in normalized]
    ranked = [row for row in ranked if row]
    ranked.sort(key=lambda row: row["ev_percent"], reverse=True)
    return {"candidate_found": bool(ranked and ranked[0]["ev_percent"] > 0), "ranked_offers": ranked, "best_line_available": ranked[0] if ranked else None}


def consensus_market_ev(offers: list[dict[str, Any]], *, probabilities: list[float], stake: float = 100.0) -> dict[str, Any]:
    consensus_probability = calculate_consensus_probability(probabilities)
    normalized = [normalize_offer(offer) for offer in offers if isinstance(offer, dict)]
    ranked = [_ev_candidate(offer, stake=stake, probability=consensus_probability, candidate_type="consensus_ev", probability_field="consensus_probability") for offer in normalized]
    ranked.sort(key=lambda row: row["ev_percent"], reverse=True)
    return {"candidate_found": bool(ranked and ranked[0]["ev_percent"] > 0), "ranked_offers": ranked, "best_line_available": ranked[0] if ranked else None}


def stale_line_ev(offers: list[dict[str, Any]], *, model_probability: float | None, stake: float = 100.0, stale_seconds: int = 300) -> dict[str, Any]:
    result = shop_ev_lines(offers, model_probability=model_probability, stake=stake)
    best = result.get("best_line_available")
    if best:
        best["candidate_type"] = "stale_line_ev"
        best["stale_data_risk"] = True
    return result


def prop_projection_ev(offers: list[dict[str, Any]], *, projection_probability: float | None, stake: float = 100.0) -> dict[str, Any]:
    return no_vig_market_ev(offers, fair_probability=projection_probability, stake=stake)


def alt_line_ev(offers: list[dict[str, Any]], *, model_probability: float | None, stake: float = 100.0) -> dict[str, Any]:
    result = shop_ev_lines(offers, model_probability=model_probability, stake=stake)
    best = result.get("best_line_available")
    if best:
        best["candidate_type"] = "positive_ev"
    return result


def derivative_market_ev(offers: list[dict[str, Any]], *, fair_probability: float | None, stake: float = 100.0) -> dict[str, Any]:
    return no_vig_market_ev(offers, fair_probability=fair_probability, stake=stake)


def shop_ev_lines(
    offers: list[dict[str, Any]],
    *,
    model_probability: float | None,
    stake: float = 100.0,
    stale_data_risk: bool = False,
) -> dict[str, Any]:
    if model_probability is None:
        return {
            "candidate_found": False,
            "reason": "no_probability_context",
            "candidate_type": "watch_recheck",
            "ranked_offers": [],
        }
    if stale_data_risk:
        return {
            "candidate_found": False,
            "reason": "stale_data",
            "candidate_type": "watch_recheck",
            "ranked_offers": [],
        }

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
                "candidate_type": "positive_ev_candidate" if ev_value > 0 else "best_line_available",
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
            "candidate_type": "best_line_available" if best else "watch_recheck",
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
    best["clv_tracking_ready"] = build_clv_record(
        {
            "event": best.get("event_name"),
            "market": best.get("market"),
            "selection": best.get("selection"),
            "opening_odds": best.get("odds"),
            "current_odds": best.get("odds"),
        }
    )
    return {
        "candidate_found": True,
        "ranked_offers": ranked,
        "best_line_available": best,
    }
