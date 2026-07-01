from __future__ import annotations

from typing import Any

from ..bookmaker_normalizer import normalize_offer
from src.data.market_identity_resolver import resolve_market_identity
from src.core.opportunity_scanner import detect_n_way_arbitrage_from_normalized_offers


def detect_two_way_arbitrage(
    offers: list[dict[str, Any]],
    *,
    total_stake: float = 100.0,
    market_identity_confidence: float | None = None,
) -> dict[str, Any]:
    normalized = [normalize_offer(offer) for offer in offers if isinstance(offer, dict)]
    if len(normalized) != 2:
        return {"candidate_found": False, "reason": "two_way_requires_two_offers"}
    if market_identity_confidence is None:
        market_identity_confidence = resolve_market_identity(normalized[0], normalized[1])["confidence"]
    return detect_n_way_arbitrage_from_normalized_offers(
        normalized,
        expected_selection_count=2,
        total_stake=total_stake,
        market_identity_confidence=float(market_identity_confidence),
        confidence_field="market_identity_confidence",
    )


def detect_cross_book_moneyline_arbitrage(offers: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return detect_two_way_arbitrage(offers, **kwargs)


def detect_cross_book_spread_arbitrage(offers: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return detect_two_way_arbitrage(offers, **kwargs)


def detect_cross_book_total_arbitrage(offers: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return detect_two_way_arbitrage(offers, **kwargs)


def detect_alt_line_arbitrage(offers: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return detect_two_way_arbitrage(offers, **kwargs)


def detect_prediction_arbitrage(
    yes_price: float,
    no_price: float,
    fee: float = 0.0,
) -> bool:
    """Return True if yes+no price (after fee) < 1 indicating arbitrage."""
    if yes_price <= 0.0 or no_price <= 0.0:
        raise ValueError("prices must be positive")
    if fee < 0.0:
        raise ValueError("fee cannot be negative")
    return (yes_price + no_price) < (1.0 - fee)
