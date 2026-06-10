"""Canonical betting math helpers.

These functions are deliberately stateless and dependency-free so route code,
pricing helpers, risk code, and backtests can share one implementation.
"""
from __future__ import annotations

from typing import Any


def _as_float(value: Any, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc


def _validate_american_odds(odds: Any) -> float:
    value = _as_float(odds, "American odds")
    if value == 0:
        raise ValueError("American odds must be positive or negative.")
    return value


def _validate_probability(probability: Any, name: str = "Probability") -> float:
    value = _as_float(probability, name)
    if value <= 0.0 or value >= 1.0:
        raise ValueError(f"{name} must be between 0 and 1.")
    return value


def american_to_decimal(odds: int | float) -> float:
    """Convert American odds to decimal odds."""
    value = _validate_american_odds(odds)
    if value > 0:
        return 1.0 + value / 100.0
    return 1.0 + 100.0 / abs(value)


def american_to_implied_probability(odds: int | float) -> float:
    """Convert American odds to implied win probability."""
    value = _validate_american_odds(odds)
    if value > 0:
        return 100.0 / (value + 100.0)
    return abs(value) / (abs(value) + 100.0)


def implied_probability_to_american(probability: float) -> int:
    """Convert an implied probability to fair American odds."""
    p = _validate_probability(probability, "Implied probability")
    if p >= 0.5:
        return int(round(-100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def strip_vig_two_way(
    side_a: int | float,
    side_b: int | float,
    *,
    input_type: str = "american",
) -> tuple[float, float]:
    """Remove two-way overround from American odds or raw implied probabilities."""
    if input_type.lower() in {"american", "odds"}:
        implied_a = american_to_implied_probability(side_a)
        implied_b = american_to_implied_probability(side_b)
    elif input_type.lower() in {"implied", "probability", "probabilities"}:
        implied_a = _as_float(side_a, "side_a")
        implied_b = _as_float(side_b, "side_b")
    else:
        raise ValueError("input_type must be 'american' or 'implied'.")

    total = implied_a + implied_b
    if total <= 0:
        raise ValueError("Implied probabilities must sum to a positive value.")
    return implied_a / total, implied_b / total


def expected_value(odds: int | float, true_probability: float, stake: float = 1.0) -> float:
    """Expected profit for a bet at American odds and a given stake."""
    p = _validate_probability(true_probability, "True probability")
    stake_value = max(0.0, _as_float(stake, "Stake"))
    profit_if_win = profit_units(odds, stake_value)
    return p * profit_if_win - (1.0 - p) * stake_value


def edge_percent(true_probability: float, implied_probability: float) -> float:
    """Return model edge in percentage points."""
    p = _as_float(true_probability, "True probability")
    implied = _as_float(implied_probability, "Implied probability")
    return (p - implied) * 100.0


def fractional_kelly(
    odds: int | float,
    true_probability: float,
    *,
    fraction: float = 1.0,
    max_fraction: float | None = None,
) -> float:
    """Return fractional Kelly stake as a bankroll fraction."""
    p = _validate_probability(true_probability, "True probability")
    decimal_odds = american_to_decimal(odds)
    b = decimal_odds - 1.0
    if b <= 0:
        return 0.0

    full_kelly = max(0.0, (b * p - (1.0 - p)) / b)
    sized = full_kelly * max(0.0, _as_float(fraction, "Kelly fraction"))
    if max_fraction is not None:
        sized = min(sized, max(0.0, _as_float(max_fraction, "Max Kelly fraction")))
    return sized


def calculate_kelly_stake(
    bankroll: float,
    odds: int | float,
    true_probability: float,
    *,
    fraction: float = 0.25,
    max_bankroll_pct: float = 0.02,
) -> float:
    """Wrapper that converts fractional Kelly into a capped dollar stake."""
    bankroll_value = max(0.0, _as_float(bankroll, "Bankroll"))
    max_pct = max(0.0, _as_float(max_bankroll_pct, "Max bankroll percent"))
    kelly = fractional_kelly(odds, true_probability, fraction=fraction)
    return min(bankroll_value * kelly, bankroll_value * max_pct)


def profit_units(odds: int | float, stake: float = 1.0) -> float:
    """Profit, excluding returned stake, if the wager wins."""
    stake_value = max(0.0, _as_float(stake, "Stake"))
    return stake_value * (american_to_decimal(odds) - 1.0)


def clv_percent(bet_odds: int | float, closing_odds: int | float) -> float:
    """Closing-line value from the bettor's price perspective."""
    bet_decimal = american_to_decimal(bet_odds)
    close_decimal = american_to_decimal(closing_odds)
    if close_decimal <= 0:
        raise ValueError("Closing decimal odds must be positive.")
    return (bet_decimal / close_decimal - 1.0) * 100.0
