from __future__ import annotations

from typing import Any

from .bookmaker_normalizer import normalize_offer
from .market_identity_resolver import resolve_market_identity
from .odds_math import american_to_decimal


def _is_stale(offers: list[dict[str, Any]], max_timestamp_skew_seconds: int) -> bool:
    timestamps = [int(offer.get("timestamp")) for offer in offers if isinstance(offer.get("timestamp"), (int, float))]
    if not timestamps:
        return False
    return (max(timestamps) - min(timestamps)) > max_timestamp_skew_seconds


def _best_prices_by_selection(offers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for raw_offer in offers:
        offer = normalize_offer(raw_offer)
        if offer.get("odds") in (None, 0):
            continue
        selection = str(offer.get("selection"))
        decimal_price = american_to_decimal(offer["odds"])
        existing = best.get(selection)
        if existing is None or decimal_price > existing["decimal_odds"]:
            best[selection] = {**offer, "decimal_odds": decimal_price}
    return best


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
    if stale_data_risk or _is_stale(offers, max_timestamp_skew_seconds):
        return {"candidate_found": False, "reason": "stale_data", "candidate_type": None}
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
    if market_identity_confidence < 85:
        return {"candidate_found": False, "reason": "low_market_identity_confidence", "candidate_type": None}

    best_by_selection = _best_prices_by_selection(normalized)
    if len(best_by_selection) < 2:
        return {"candidate_found": False, "reason": "same_side_only", "candidate_type": None}
    if len(best_by_selection) not in {2, 3}:
        return {"candidate_found": False, "reason": "unsupported_selection_count", "candidate_type": None}

    implied_sum = sum(1.0 / row["decimal_odds"] for row in best_by_selection.values())
    if implied_sum >= 1.0:
        return {
            "candidate_found": False,
            "reason": "no_arbitrage_after_vig",
            "candidate_type": None,
            "arbitrage_implied_sum": round(implied_sum, 6),
        }

    stake_plan = []
    payouts = []
    for selection, row in best_by_selection.items():
        stake = total_stake * ((1.0 / row["decimal_odds"]) / implied_sum)
        payout = stake * row["decimal_odds"]
        payouts.append(payout)
        stake_plan.append(
            {
                "selection": selection,
                "bookmaker": row["bookmaker"],
                "odds": row["odds"],
                "decimal_odds": round(row["decimal_odds"], 6),
                "stake": round(stake, 2),
                "payout": round(payout, 2),
            }
        )

    total_stake_value = round(sum(item["stake"] for item in stake_plan), 2)
    profits = [round(payout - total_stake_value, 2) for payout in payouts]
    min_profit = min(profits)
    max_profit = max(profits)
    return {
        "candidate_found": True,
        "candidate_type": "arbitrage_candidate",
        "books_compared": len({item["bookmaker"] for item in stake_plan}),
        "arbitrage_implied_sum": round(implied_sum, 6),
        "stake_plan": stake_plan,
        "total_stake": total_stake_value,
        "min_profit": min_profit,
        "max_profit": max_profit,
        "estimated_roi_percent": round((min_profit / total_stake_value) * 100.0, 4),
        "line_match_confidence": round(float(market_identity_confidence), 2),
        "stale_data_risk": False,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "user_facing_label": "arbitrage_candidate",
    }
