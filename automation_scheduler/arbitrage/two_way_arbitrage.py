from __future__ import annotations

from typing import Any

from ..bookmaker_normalizer import normalize_offer
from ..market_identity_resolver import resolve_market_identity
from ..odds_math import american_to_decimal


def _stake_split(best_prices: list[dict[str, Any]], total_stake: float) -> tuple[list[dict[str, Any]], float]:
    implied_sum = sum(1.0 / price["decimal_odds"] for price in best_prices)
    plan = []
    for price in best_prices:
        stake = total_stake * ((1.0 / price["decimal_odds"]) / implied_sum)
        plan.append({**price, "stake": round(stake, 2), "payout": round(stake * price["decimal_odds"], 2)})
    return plan, implied_sum


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
    if market_identity_confidence < 85:
        return {"candidate_found": False, "reason": "low_market_identity_confidence"}
    best_prices = [{**offer, "decimal_odds": american_to_decimal(offer["odds"])} for offer in normalized]
    stake_plan, implied_sum = _stake_split(best_prices, total_stake)
    if implied_sum >= 1:
        return {"candidate_found": False, "reason": "no_arbitrage_after_vig", "arbitrage_implied_sum": round(implied_sum, 6)}
    total = round(sum(item["stake"] for item in stake_plan), 2)
    profits = [round(item["payout"] - total, 2) for item in stake_plan]
    return {
        "candidate_found": True,
        "candidate_type": "arbitrage_candidate",
        "stake_plan": stake_plan,
        "arbitrage_implied_sum": round(implied_sum, 6),
        "estimated_roi_percent": round((min(profits) / total) * 100.0, 4),
        "max_gain": max(profits),
        "max_loss": 0.0,
        "market_identity_confidence": round(float(market_identity_confidence), 2),
    }


def detect_cross_book_moneyline_arbitrage(offers: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return detect_two_way_arbitrage(offers, **kwargs)


def detect_cross_book_spread_arbitrage(offers: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return detect_two_way_arbitrage(offers, **kwargs)


def detect_cross_book_total_arbitrage(offers: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return detect_two_way_arbitrage(offers, **kwargs)


def detect_alt_line_arbitrage(offers: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    return detect_two_way_arbitrage(offers, **kwargs)
