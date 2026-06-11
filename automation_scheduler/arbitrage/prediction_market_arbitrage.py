from __future__ import annotations

from typing import Any

from src.core.opportunity_scanner import detect_prediction_market_vs_sportsbook_arbitrage_from_prices


def detect_prediction_market_vs_sportsbook_arbitrage(
    *,
    sportsbook_odds_american: Any,
    prediction_market_yes_price: Any,
    total_stake: float = 100.0,
) -> dict[str, Any]:
    return detect_prediction_market_vs_sportsbook_arbitrage_from_prices(
        sportsbook_odds_american=sportsbook_odds_american,
        prediction_market_yes_price=prediction_market_yes_price,
        total_stake=total_stake,
    )
