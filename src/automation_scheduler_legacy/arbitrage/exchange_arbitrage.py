from __future__ import annotations

from typing import Any

from src.core.opportunity_scanner import detect_exchange_back_lay_arbitrage_from_prices


def detect_exchange_back_lay_arbitrage(
    *,
    back_odds_american: Any,
    lay_decimal_odds: Any,
    total_stake: float = 100.0,
) -> dict[str, Any]:
    return detect_exchange_back_lay_arbitrage_from_prices(
        back_odds_american=back_odds_american,
        lay_decimal_odds=lay_decimal_odds,
        total_stake=total_stake,
    )
