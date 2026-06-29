from __future__ import annotations

from typing import Any

from .bookmaker_normalizer import normalize_offer
from .market_identity_resolver import resolve_market_identity
from src.core.opportunity_scanner import detect_arbitrage_from_normalized_offers


def detect_arbitrage(
    offers: list[dict[str, Any]],
    *,
    total_stake: float = 100.0,
    market_identity_confidence: float | None = None,
    max_timestamp_skew_seconds: int = 120,
    stale_data_risk: bool = False,
) -> dict[str, Any]:
    if len(offers) < 2:
        return {"candidate_found": False, "reason": "not_enough_offers", "candidate_type": None}
    normalized = [normalize_offer(offer) for offer in offers if isinstance(offer, dict)]
    identity_keys = {
        (str(offer.get("event_name") or ""), str(offer.get("market") or ""))
        for offer in normalized
    }
    if len(identity_keys) > 1:
        return {"candidate_found": False, "reason": "mismatched_event_market", "candidate_type": None}

    if market_identity_confidence is None:
        confidences = []
        for index in range(len(normalized) - 1):
            for other in range(index + 1, len(normalized)):
                confidences.append(resolve_market_identity(normalized[index], normalized[other])["confidence"])
        market_identity_confidence = min(confidences) if confidences else 100.0
    return detect_arbitrage_from_normalized_offers(
        normalized,
        total_stake=total_stake,
        market_identity_confidence=float(market_identity_confidence),
        max_timestamp_skew_seconds=max_timestamp_skew_seconds,
        stale_data_risk=stale_data_risk,
    )
