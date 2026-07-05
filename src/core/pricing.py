"""Canonical pricing helpers.

This module owns deterministic odds/price math and no-vig helpers.
It has no provider, connector, dashboard, or network dependencies.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.core.math_utils import (
    american_to_decimal as _american_to_decimal,
    american_to_implied_probability as _american_to_implied_probability,
    book_hold_n_way as _book_hold_n_way,
    book_hold_two_way as _book_hold_two_way,
    break_even_probability_american as _break_even_probability_american,
    break_even_probability_decimal as _break_even_probability_decimal,
    decimal_to_american as _decimal_to_american,
    decimal_to_implied_probability as _decimal_to_implied_probability,
    edge_percent as _edge_percent,
    expected_value as _expected_value,
    expected_value_per_100 as _expected_value_per_100,
    expected_value_per_dollar as _expected_value_per_dollar,
    expected_value_per_unit as _expected_value_per_unit,
    fair_decimal_odds_from_probability as _fair_decimal_odds_from_probability,
    fair_odds_american_from_probability as _fair_odds_american_from_probability,
    fractional_kelly as _fractional_kelly,
    fractional_kelly_percent as _fractional_kelly_percent,
    full_kelly_fraction as _full_kelly_fraction,
    full_kelly_percent as _full_kelly_percent,
    implied_probability_from_american as _implied_probability_from_american,
    implied_probability_to_american as _implied_probability_to_american,
    no_vig_probabilities_n_way as _no_vig_probabilities_n_way,
    no_vig_probabilities_three_way as _no_vig_probabilities_three_way,
    no_vig_probabilities_two_way as _no_vig_probabilities_two_way,
)


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_american_odds(odds: Any) -> int:
    value = int(round(_to_float(odds)))
    if value == 0:
        raise ValueError("American odds must not be zero.")
    return value


def normalize_decimal_odds(decimal_odds: Any) -> float:
    value = _to_float(decimal_odds)
    if value <= 1.0:
        raise ValueError("Decimal odds must be greater than 1.")
    return value


def normalize_price_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    american_odds = payload.get("american_odds", payload.get("odds_american"))
    decimal_odds = payload.get("decimal_odds")
    true_probability = payload.get("true_probability")
    implied_probability = payload.get("implied_probability")

    if american_odds is not None:
        american_odds = normalize_american_odds(american_odds)
        decimal_odds = _american_to_decimal(american_odds)
        implied_probability = _implied_probability_from_american(american_odds)
    elif decimal_odds is not None:
        decimal_odds = normalize_decimal_odds(decimal_odds)
        implied_probability = _decimal_to_implied_probability(decimal_odds)

    if true_probability is not None:
        true_probability = clamp_probability(true_probability)

    edge_value = None
    edge_pct = None
    if true_probability is not None and implied_probability is not None:
        edge_value = edge(true_probability, implied_probability)
        edge_pct = edge_percentage(true_probability, implied_probability)

    return {
        "american_odds": american_odds,
        "decimal_odds": decimal_odds,
        "implied_probability": implied_probability,
        "true_probability": true_probability,
        "edge": edge_value,
        "edge_percent": edge_pct,
        "fair_decimal_odds": (
            _fair_decimal_odds_from_probability(true_probability)
            if true_probability is not None
            else None
        ),
        "fair_american_odds": (
            _fair_odds_american_from_probability(true_probability)
            if true_probability is not None
            else None
        ),
        "payout_units": payout_units(american_odds) if american_odds is not None else None,
        "profit_units": profit_units(american_odds) if american_odds is not None else None,
        "expected_value_per_unit": (
            expected_value_per_unit(american_odds, true_probability)
            if american_odds is not None and true_probability is not None
            else None
        ),
        "expected_value_per_100": (
            expected_value_per_100(american_odds, true_probability)
            if american_odds is not None and true_probability is not None
            else None
        ),
        "kelly_fraction": (
            full_kelly_fraction(american_odds, true_probability)
            if american_odds is not None and true_probability is not None
            else None
        ),
    }


def american_to_decimal(odds: int | float) -> float:
    return _american_to_decimal(odds)


def decimal_to_implied_probability(decimal_odds: int | float) -> float:
    return _decimal_to_implied_probability(decimal_odds)


def implied_probability_from_american(odds: int | float) -> float:
    return _implied_probability_from_american(odds)


def american_to_implied_probability(odds: int | float) -> float:
    return implied_probability_from_american(odds)


def decimal_to_american(decimal_odds: float) -> int:
    return _decimal_to_american(decimal_odds)


def implied_probability_to_american(probability: float) -> int:
    return _implied_probability_to_american(clamp_probability(probability))


def fair_odds_american_from_probability(probability: float) -> int:
    return _fair_odds_american_from_probability(clamp_probability(probability))


def fair_decimal_odds_from_probability(probability: float) -> float:
    return _fair_decimal_odds_from_probability(clamp_probability(probability))


def break_even_probability_american(odds: int | float) -> float:
    return _break_even_probability_american(odds)


def break_even_probability_decimal(decimal_odds: float) -> float:
    return _break_even_probability_decimal(decimal_odds)


def book_hold_two_way(implied_a: float, implied_b: float) -> float:
    return _book_hold_two_way(implied_a, implied_b)


def book_hold_n_way(implied_probabilities: list[float]) -> float:
    return _book_hold_n_way(implied_probabilities)


def no_vig_probabilities_two_way(implied_a: float, implied_b: float) -> tuple[float, float]:
    return _no_vig_probabilities_two_way(implied_a, implied_b)


def no_vig_probabilities_three_way(p1: float, p2: float, p3: float) -> tuple[float, float, float]:
    return _no_vig_probabilities_three_way(p1, p2, p3)


def no_vig_probabilities_n_way(implied: list[float]) -> list[float]:
    return _no_vig_probabilities_n_way(implied)


def expected_value(odds: int | float, true_probability: float, stake: float = 1.0) -> float:
    return _expected_value(odds, true_probability, stake)


def expected_value_per_unit(odds: int | float, true_probability: float) -> float:
    return _expected_value_per_unit(odds, true_probability)


def expected_value_per_100(odds: int | float, true_probability: float) -> float:
    return _expected_value_per_100(odds, true_probability)


def expected_value_per_dollar(odds: int | float, true_probability: float) -> float:
    return _expected_value_per_dollar(odds, true_probability)


def edge(true_probability: float, implied_probability: float) -> float:
    return round(clamp_probability(true_probability) - clamp_probability(implied_probability), 12)


def edge_percentage(true_probability: float, implied_probability: float) -> float:
    return _edge_percent(true_probability, implied_probability)


def payout_units(odds: int | float, stake: float = 1.0) -> float:
    decimal_odds = american_to_decimal(odds)
    return round(max(0.0, float(stake)) * max(0.0, decimal_odds - 1.0), 12)


def profit_units(odds: int | float, stake: float = 1.0) -> float:
    return payout_units(odds, stake)


def full_kelly_fraction(odds: int | float, true_probability: float) -> float:
    return _full_kelly_fraction(odds, true_probability)


def fractional_kelly_fraction(
    odds: int | float,
    true_probability: float,
    fraction: float = 0.25,
) -> float:
    return _fractional_kelly(odds, true_probability, fraction=fraction)


def full_kelly_percent(odds: int | float, true_probability: float) -> float:
    return _full_kelly_percent(odds, true_probability)


def fractional_kelly_percent(
    odds: int | float,
    true_probability: float,
    fraction: float = 0.25,
) -> float:
    return _fractional_kelly_percent(odds, true_probability, fraction=fraction)


def calculate_kelly_stake(
    bankroll: float,
    odds: int | float,
    true_probability: float,
    fraction: float = 0.25,
    max_bankroll_pct: float = 0.02,
) -> float:
    kelly = fractional_kelly_fraction(odds, true_probability, fraction=fraction)
    stake = float(bankroll) * max(0.0, kelly)
    cap = float(bankroll) * max(0.0, max_bankroll_pct)
    return round(min(max(0.0, stake), cap), 2)


def clamp_probability(value: Any, lower: float = 0.0, upper: float = 1.0) -> float:
    numeric = _to_float(value, default=lower)
    if numeric < lower:
        return lower
    if numeric > upper:
        return upper
    return numeric


def normalize_probability(value: Any) -> float:
    numeric = clamp_probability(value)
    if numeric <= 0.0 or numeric >= 1.0:
        raise ValueError("Probability must be between 0 and 1.")
    return numeric


def probability_to_edge(true_probability: Any, implied_probability: Any) -> float:
    return round(clamp_probability(true_probability) - clamp_probability(implied_probability), 12)


__all__ = [
    "american_to_decimal",
    "american_to_implied_probability",
    "book_hold_n_way",
    "book_hold_two_way",
    "break_even_probability_american",
    "break_even_probability_decimal",
    "calculate_kelly_stake",
    "clamp_probability",
    "decimal_to_american",
    "decimal_to_implied_probability",
    "edge",
    "edge_percentage",
    "expected_value",
    "expected_value_per_100",
    "expected_value_per_dollar",
    "expected_value_per_unit",
    "fair_decimal_odds_from_probability",
    "fair_odds_american_from_probability",
    "fractional_kelly_fraction",
    "fractional_kelly_percent",
    "full_kelly_fraction",
    "full_kelly_percent",
    "implied_probability_from_american",
    "implied_probability_to_american",
    "no_vig_probabilities_n_way",
    "no_vig_probabilities_three_way",
    "no_vig_probabilities_two_way",
    "normalize_american_odds",
    "normalize_decimal_odds",
    "normalize_price_payload",
    "normalize_probability",
    "payout_units",
    "probability_to_edge",
    "profit_units",
]
