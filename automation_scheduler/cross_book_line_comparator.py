from __future__ import annotations

from typing import Any

from .bookmaker_normalizer import normalize_line_value, normalize_offer, normalize_selection_name
from .market_identity_resolver import resolve_market_identity
from .odds_math import american_to_decimal


def _line_value_for_ranking(offer: dict[str, Any]) -> float:
    market = offer.get("market")
    selection = normalize_selection_name(offer.get("selection"))
    line = normalize_line_value(offer.get("line"))
    if line is None:
        return 0.0
    numeric = float(line)
    if market == "total":
        return -numeric if selection == "over" else numeric
    return numeric


def compare_cross_book_lines(offers: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = [normalize_offer(offer) for offer in offers if isinstance(offer, dict)]
    if not normalized:
        return {
            "books_compared": 0,
            "best_offer": None,
            "worst_offer": None,
            "best_book": None,
            "best_line": None,
            "best_odds": None,
            "line_spread": 0.0,
            "odds_spread": 0.0,
            "book_disagreement_score": 0.0,
            "line_match_confidence": 0.0,
        }

    decimals = [(american_to_decimal(offer["odds"]), idx, offer) for idx, offer in enumerate(normalized) if offer.get("odds") not in (None, 0)]
    decimals.sort(key=lambda row: (row[0], _line_value_for_ranking(row[2])), reverse=True)
    best_offer = decimals[0][2]
    worst_offer = decimals[-1][2]

    line_values = [float(offer["line"]) for offer in normalized if offer.get("line") is not None]
    odds_values = [float(offer["odds"]) for offer in normalized if offer.get("odds") is not None]
    identity_scores = []
    for index in range(len(normalized) - 1):
        for other in range(index + 1, len(normalized)):
            identity_scores.append(resolve_market_identity(normalized[index], normalized[other])["confidence"])

    line_spread = (max(line_values) - min(line_values)) if line_values else 0.0
    odds_spread = (max(odds_values) - min(odds_values)) if odds_values else 0.0
    disagreement = min(100.0, abs(odds_spread) / 3.0 + abs(line_spread) * 12.0)

    return {
        "books_compared": len({offer["bookmaker"] for offer in normalized}),
        "offers": normalized,
        "best_offer": best_offer,
        "worst_offer": worst_offer,
        "best_book": best_offer["bookmaker"],
        "best_line": best_offer.get("line"),
        "best_odds": best_offer.get("odds"),
        "line_spread": round(line_spread, 4),
        "odds_spread": round(odds_spread, 4),
        "book_disagreement_score": round(disagreement, 2),
        "line_match_confidence": round(sum(identity_scores) / len(identity_scores), 2) if identity_scores else 100.0,
    }
