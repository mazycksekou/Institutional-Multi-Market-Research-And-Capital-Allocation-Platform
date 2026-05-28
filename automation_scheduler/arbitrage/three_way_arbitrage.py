from __future__ import annotations

from typing import Any

from ..bookmaker_normalizer import normalize_offer
from ..odds_math import american_to_decimal


def detect_three_way_arbitrage(offers: list[dict[str, Any]], *, total_stake: float = 100.0) -> dict[str, Any]:
    normalized = [normalize_offer(offer) for offer in offers if isinstance(offer, dict)]
    if len(normalized) != 3:
        return {"candidate_found": False, "reason": "three_way_requires_three_offers"}
    with_decimals = [{**offer, "decimal_odds": american_to_decimal(offer["odds"])} for offer in normalized]
    implied_sum = sum(1.0 / offer["decimal_odds"] for offer in with_decimals)
    if implied_sum >= 1:
        return {"candidate_found": False, "reason": "no_arbitrage_after_vig", "arbitrage_implied_sum": round(implied_sum, 6)}
    stake_plan = []
    for offer in with_decimals:
        stake = total_stake * ((1.0 / offer["decimal_odds"]) / implied_sum)
        stake_plan.append({**offer, "stake": round(stake, 2), "payout": round(stake * offer["decimal_odds"], 2)})
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
    }
