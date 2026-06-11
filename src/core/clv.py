"""Canonical closing-line value helpers.

This module owns pure CLV and line-movement math. It has no scheduler state,
provider calls, or file I/O.
"""
from __future__ import annotations

from typing import Any

from src.core.math_utils import american_to_decimal, american_to_implied_probability


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def implied_probability_from_american_safe(odds: Any) -> float:
    """Return implied probability for American odds, or 0 for unusable odds."""
    try:
        return american_to_implied_probability(float(odds))
    except (TypeError, ValueError):
        return 0.0


def calculate_clv_percent(
    recommended_implied_probability: float,
    closing_implied_probability: float,
) -> float:
    """CLV as closing implied probability minus entry implied probability."""
    return round(
        (_to_float(closing_implied_probability) - _to_float(recommended_implied_probability)) * 100.0,
        4,
    )


def calculate_clv_for_american_odds(recommended_odds: Any, closing_odds: Any) -> float:
    """CLV percentage from entry and closing American prices."""
    recommended_ip = implied_probability_from_american_safe(recommended_odds)
    closing_ip = implied_probability_from_american_safe(closing_odds)
    return calculate_clv_percent(recommended_ip, closing_ip)


def price_ratio_clv_percent(bet_odds: Any, closing_odds: Any) -> float | None:
    """Bettor price-ratio CLV using decimal odds, positive when entry price beat close."""
    try:
        bet_decimal = american_to_decimal(float(bet_odds))
        closing_decimal = american_to_decimal(float(closing_odds))
    except (TypeError, ValueError):
        return None
    if closing_decimal <= 0:
        return None
    return round(((bet_decimal - closing_decimal) / closing_decimal) * 100.0, 4)


def clv_percent_bettor_perspective(
    bet_price_implied_open: float,
    closing_implied: float,
    took_underdog_side: bool = True,
) -> float:
    """CLV from the bettor side, preserving legacy underdog/favorite direction."""
    if took_underdog_side:
        return round((_to_float(closing_implied) - _to_float(bet_price_implied_open)) * 100.0, 3)
    return round((_to_float(bet_price_implied_open) - _to_float(closing_implied)) * 100.0, 3)


def opening_vs_current_clv_implied_change_pct(opening_american: Any, current_american: Any) -> float | None:
    """Percent change in implied probability from opener to current price."""
    opening = implied_probability_from_american_safe(opening_american)
    current = implied_probability_from_american_safe(current_american)
    if opening <= 0:
        return None
    return round((current - opening) / opening * 100.0, 3)


def current_vs_projected_close_delta(
    current_implied: float,
    projected_close_implied: float | None,
) -> float | None:
    """Point delta between current implied probability and a projected close."""
    if projected_close_implied is None:
        return None
    return round((_to_float(current_implied) - _to_float(projected_close_implied)) * 100.0, 3)


def closing_line_value_pct(
    bet_implied_at_bet: float,
    closing_implied: float | None,
) -> float | None:
    """Legacy market-pricing CLV point delta for an entry implied price vs close."""
    if closing_implied is None:
        return None
    return round((_to_float(bet_implied_at_bet) - _to_float(closing_implied)) * 100.0, 3)


def steam_move_from_implied_series(implied_series: list[float], threshold: float = 0.012) -> bool:
    """Detect whether the latest implied-probability step exceeds a threshold."""
    if len(implied_series) < 2:
        return False
    return abs(_to_float(implied_series[-1]) - _to_float(implied_series[-2])) >= _to_float(threshold, default=0.012)


def projected_close_placeholder(current_implied: float) -> float | None:
    """Keep explicit no-projection behavior until a real model supplies projected close."""
    return None


def calculate_positive_clv_rate(clv_values: list[float]) -> float:
    """Share of CLV observations above zero."""
    if not clv_values:
        return 0.0
    positives = sum(1 for value in clv_values if _to_float(value) > 0)
    return round(positives / len(clv_values), 4)


def detect_clv_decay(clv_values: list[float], threshold_percent: float = 1.5) -> bool:
    """Detect whether late-period CLV has degraded materially versus early-period CLV."""
    if len(clv_values) < 6:
        return False
    values = [_to_float(value) for value in clv_values]
    midpoint = len(values) // 2
    early_avg = sum(values[:midpoint]) / max(1, len(values[:midpoint]))
    late_avg = sum(values[midpoint:]) / max(1, len(values[midpoint:]))
    return (early_avg - late_avg) >= _to_float(threshold_percent, default=1.5)


def calculate_clv(opening_odds: Any, current_odds: Any, closing_odds: Any | None = None) -> dict[str, float]:
    """Simple American-odds line movement deltas for CLV watch records."""
    opening = _to_float(opening_odds)
    current = _to_float(current_odds)
    closing = _to_float(closing_odds if closing_odds is not None else current_odds)
    return {
        "opening_to_current": round(current - opening, 4),
        "opening_to_closing": round(closing - opening, 4),
        "current_to_closing": round(closing - current, 4),
    }


def average_clv(clv_values: list[float | None]) -> float | None:
    """Average non-null CLV values."""
    values = [_to_float(value) for value in clv_values if value is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 3)
