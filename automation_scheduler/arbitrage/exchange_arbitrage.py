from __future__ import annotations

from typing import Any

from ..odds_math import american_to_decimal


def detect_exchange_back_lay_arbitrage(
    *,
    back_odds_american: Any,
    lay_decimal_odds: Any,
    total_stake: float = 100.0,
) -> dict[str, Any]:
    back_decimal = american_to_decimal(back_odds_american)
    lay_decimal = float(lay_decimal_odds)
    if lay_decimal <= 1:
        return {"candidate_found": False, "reason": "invalid_lay_odds"}
    back_stake = float(total_stake)
    lay_stake = (back_stake * back_decimal) / lay_decimal
    back_profit = back_stake * (back_decimal - 1)
    lay_liability = lay_stake * (lay_decimal - 1)
    outcome_a = round(back_profit - lay_liability, 2)
    outcome_b = round(lay_stake - back_stake, 2)
    if min(outcome_a, outcome_b) <= 0:
        return {"candidate_found": False, "reason": "no_exchange_arbitrage"}
    return {
        "candidate_found": True,
        "candidate_type": "arbitrage_candidate",
        "stake_plan": [
            {"side": "back", "stake": round(back_stake, 2), "odds": back_odds_american},
            {"side": "lay", "stake": round(lay_stake, 2), "odds": round(lay_decimal, 4)},
        ],
        "max_gain": max(outcome_a, outcome_b),
        "max_loss": 0.0,
        "estimated_roi_percent": round((min(outcome_a, outcome_b) / back_stake) * 100.0, 4),
    }
