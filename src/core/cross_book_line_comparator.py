from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.market_intelligence.bookmaker_normalizer import normalize_line_value, normalize_offer, normalize_selection_name
from src.data.market_identity_resolver import resolve_market_identity
from src.core.math_utils import american_to_decimal


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
            "candidate_type": "watch_recheck",
            "reason": "no_valid_offers",
        }

    decimals = [(american_to_decimal(offer["odds"]), idx, offer) for idx, offer in enumerate(normalized) if offer.get("odds") not in (None, 0)]
    decimals.sort(key=lambda row: (row[0], _line_value_for_ranking(row[2])), reverse=True)
    best_offer = decimals[0][2]
    worst_offer = decimals[-1][2]

    line_values = [float(offer["line"]) for offer in normalized if offer.get("line") is not None]
    odds_values = [float(offer["odds"]) for offer in normalized if offer.get("odds") is not None]
    timestamps = [int(offer["timestamp"]) for offer in normalized if offer.get("timestamp") is not None]
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
        "worst_book": worst_offer["bookmaker"],
        "worst_line": worst_offer.get("line"),
        "worst_odds": worst_offer.get("odds"),
        "line_spread": round(line_spread, 4),
        "odds_spread": round(odds_spread, 4),
        "book_disagreement_score": round(disagreement, 2),
        "line_match_confidence": round(sum(identity_scores) / len(identity_scores), 2) if identity_scores else 100.0,
        "market_identity_confidence": round(sum(identity_scores) / len(identity_scores), 2) if identity_scores else 100.0,
        "stale_data_risk": bool(timestamps and (max(timestamps) - min(timestamps) > 120)),
        "timestamp_mismatch_seconds": (max(timestamps) - min(timestamps)) if timestamps else 0,
        "candidate_type": "best_line_available",
    }


def group_cross_book_markets(offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for raw in offers:
        if not isinstance(raw, dict):
            continue
        normalized = normalize_offer(raw)
        event_id = str(raw.get("event_id") or raw.get("event_name") or normalized.get("event_name") or "").strip()
        market = str(normalized.get("market") or "").strip()
        selection = str(normalized.get("selection") or "").strip()
        line = normalize_line_value(raw.get("line"))
        line_key = "" if line is None else str(line)
        if not event_id or not market or not selection:
            continue
        grouped[(event_id, market, selection, line_key)].append(raw)

    comparisons: list[dict[str, Any]] = []
    for (event_id, market, selection, line_key), rows in grouped.items():
        comparison = compare_cross_book_lines(rows)
        books = {normalize_offer(row).get("bookmaker") for row in rows if isinstance(row, dict)}
        books.discard(None)
        if len(books) <= 1:
            comparison["candidate_type"] = "watch_recheck"
            comparison["reason"] = "single_book_only"
        comparisons.append(
            {
                "event_id": event_id,
                "market": market,
                "selection": selection,
                "line": None if line_key == "" else normalize_line_value(line_key),
                "books_compared": len(books),
                "comparison": comparison,
                "offers": [normalize_offer(row) for row in rows if isinstance(row, dict)],
            }
        )
    return comparisons
