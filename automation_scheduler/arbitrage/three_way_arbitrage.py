from __future__ import annotations

from typing import Any

from ..bookmaker_normalizer import normalize_offer
from src.core.opportunity_scanner import detect_n_way_arbitrage_from_normalized_offers


def detect_three_way_arbitrage(offers: list[dict[str, Any]], *, total_stake: float = 100.0) -> dict[str, Any]:
    normalized = [normalize_offer(offer) for offer in offers if isinstance(offer, dict)]
    if len(normalized) != 3:
        return {"candidate_found": False, "reason": "three_way_requires_three_offers"}
    return detect_n_way_arbitrage_from_normalized_offers(
        normalized,
        expected_selection_count=3,
        total_stake=total_stake,
    )
