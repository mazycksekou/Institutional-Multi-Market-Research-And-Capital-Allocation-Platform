"""Closing line value and line movement helpers."""
from __future__ import annotations

from typing import Optional


def clv_percent_bettor_perspective(
    bet_price_implied_open: float,
    closing_implied: float,
    took_underdog_side: bool = True,
) -> float:
    """
    Simplified CLV%: for underdog side, positive CLV if closing implied > bet implied.
    """
    if took_underdog_side:
        return round((closing_implied - bet_price_implied_open) * 100, 3)
    return round((bet_price_implied_open - closing_implied) * 100, 3)


def steam_move_from_implied_series(implied_series: list[float], threshold: float = 0.012) -> bool:
    if len(implied_series) < 2:
        return False
    return abs(implied_series[-1] - implied_series[-2]) >= threshold


def projected_close_placeholder(current_implied: float) -> Optional[float]:
    """Without a closing model, return None."""
    return None
