from __future__ import annotations

from typing import Any

from ..odds_math import american_to_implied_probability, normalize_probability


def detect_prediction_market_vs_sportsbook_arbitrage(
    *,
    sportsbook_odds_american: Any,
    prediction_market_yes_price: Any,
    total_stake: float = 100.0,
) -> dict[str, Any]:
    sportsbook_prob = american_to_implied_probability(sportsbook_odds_american)
    prediction_prob = normalize_probability(prediction_market_yes_price)
    implied_sum = sportsbook_prob + prediction_prob
    if implied_sum >= 1:
        return {"candidate_found": False, "reason": "no_prediction_market_arbitrage", "arbitrage_implied_sum": round(implied_sum, 6)}
    sportsbook_stake = total_stake * (sportsbook_prob / implied_sum)
    prediction_stake = total_stake * (prediction_prob / implied_sum)
    return {
        "candidate_found": True,
        "candidate_type": "arbitrage_candidate",
        "arbitrage_implied_sum": round(implied_sum, 6),
        "stake_plan": [
            {"side": "sportsbook", "stake": round(sportsbook_stake, 2), "odds": sportsbook_odds_american},
            {"side": "prediction_market", "stake": round(prediction_stake, 2), "price": prediction_market_yes_price},
        ],
        "max_gain": round(total_stake * ((1 - implied_sum) / implied_sum), 2),
        "max_loss": 0.0,
        "estimated_roi_percent": round(((1 - implied_sum) / implied_sum) * 100.0, 4),
    }
