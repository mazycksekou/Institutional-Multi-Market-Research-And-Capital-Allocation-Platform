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


def decimal_to_american(decimal_odds: int | float) -> int:
    """Convert decimal odds to American odds."""
    decimal_value = _as_float(decimal_odds, "Decimal odds")
    if decimal_value <= 1.0:
        raise ValueError("Decimal odds must be greater than 1.")
    if decimal_value >= 2.0:
        return int(round((decimal_value - 1.0) * 100.0))
    return int(round(-100.0 / (decimal_value - 1.0)))


def american_to_implied_probability(odds: int | float) -> float:
    """Convert American odds to implied win probability."""
    value = _validate_american_odds(odds)
    if value > 0:
        return 100.0 / (value + 100.0)
    return abs(value) / (abs(value) + 100.0)


def implied_probability_from_american(odds: int | float) -> float:
    """Backward-compatible alias for American odds implied probability."""
    return american_to_implied_probability(odds)


def decimal_to_implied_probability(decimal_odds: int | float) -> float:
    """Convert decimal odds to implied win probability."""
    decimal_value = _as_float(decimal_odds, "Decimal odds")
    if decimal_value <= 1.0:
        raise ValueError("Decimal odds must be greater than 1.")
    return 1.0 / decimal_value


def implied_probability_from_decimal(decimal_odds: int | float) -> float:
    """Backward-compatible alias for decimal odds implied probability."""
    return decimal_to_implied_probability(decimal_odds)


def implied_probability_to_american(probability: float) -> int:
    """Convert an implied probability to fair American odds."""
    p = _validate_probability(probability, "Implied probability")
    if p >= 0.5:
        return int(round(-100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def probability_to_fair_american(probability: float) -> int:
    """Convert fair win probability to American odds."""
    return implied_probability_to_american(probability)


def fair_odds_american_from_probability(probability: float) -> int:
    """Backward-compatible alias for fair American odds."""
    return implied_probability_to_american(probability)


def fair_decimal_odds_from_probability(probability: float) -> float:
    """Convert fair win probability to decimal odds."""
    p = _validate_probability(probability)
    return 1.0 / p


def break_even_probability_american(odds: int | float) -> float:
    """Minimum win probability needed to break even at American odds."""
    return american_to_implied_probability(odds)


def break_even_probability_decimal(decimal_odds: int | float) -> float:
    """Minimum win probability needed to break even at decimal odds."""
    return decimal_to_implied_probability(decimal_odds)


def normalize_probability(probability: Any) -> float:
    """Normalize a probability supplied as 0-1 or 0-100 percentage."""
    value = _as_float(probability, "Probability")
    if value > 1.0:
        value /= 100.0
    if value < 0.0 or value > 1.0:
        raise ValueError("Probability must be between 0 and 1.")
    return value


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


def no_vig_probabilities_two_way(implied_a: float, implied_b: float) -> tuple[float, float]:
    """Remove overround from a two-outcome market."""
    return strip_vig_two_way(implied_a, implied_b, input_type="implied")


def no_vig_probabilities_three_way(p1: float, p2: float, p3: float) -> tuple[float, float, float]:
    """Remove overround from a three-outcome market."""
    fair = no_vig_probabilities_n_way([p1, p2, p3])
    return fair[0], fair[1], fair[2]


def no_vig_probabilities_n_way(implied_probabilities: list[float]) -> list[float]:
    """Remove overround from an N-outcome market."""
    implied = [_as_float(probability, "Implied probability") for probability in implied_probabilities]
    total = sum(implied)
    if total <= 0:
        raise ValueError("Implied probabilities must sum to a positive value.")
    return [probability / total for probability in implied]


def book_hold_two_way(implied_a: float, implied_b: float) -> float:
    """Two-way market overround."""
    return _as_float(implied_a, "implied_a") + _as_float(implied_b, "implied_b") - 1.0


def book_hold_n_way(implied_probabilities: list[float]) -> float:
    """N-way market overround."""
    return sum(_as_float(probability, "Implied probability") for probability in implied_probabilities) - 1.0


def remove_two_way_vig(probability_a: Any, probability_b: Any) -> dict[str, float]:
    """Return two-way fair probabilities plus market hold."""
    normalized = [normalize_probability(probability_a), normalize_probability(probability_b)]
    fair_a, fair_b = no_vig_probabilities_two_way(normalized[0], normalized[1])
    return {
        "fair_probability_a": fair_a,
        "fair_probability_b": fair_b,
        "market_hold": book_hold_n_way(normalized),
        "vig": max(0.0, book_hold_n_way(normalized)),
    }


def remove_three_way_vig(probability_a: Any, probability_b: Any, probability_c: Any) -> dict[str, float]:
    """Return three-way fair probabilities plus market hold."""
    normalized = [
        normalize_probability(probability_a),
        normalize_probability(probability_b),
        normalize_probability(probability_c),
    ]
    fair_a, fair_b, fair_c = no_vig_probabilities_three_way(normalized[0], normalized[1], normalized[2])
    return {
        "fair_probability_a": fair_a,
        "fair_probability_b": fair_b,
        "fair_probability_c": fair_c,
        "market_hold": book_hold_n_way(normalized),
    }


def expected_value(odds: int | float, true_probability: float, stake: float = 1.0) -> float:
    """Expected profit for a bet at American odds and a given stake."""
    p = _validate_probability(true_probability, "True probability")
    stake_value = max(0.0, _as_float(stake, "Stake"))
    profit_if_win = profit_units(odds, stake_value)
    return p * profit_if_win - (1.0 - p) * stake_value


def expected_value_per_unit(odds: int | float, true_probability: float) -> float:
    """Expected profit for one unit staked."""
    return expected_value(odds, true_probability, stake=1.0)


def expected_value_per_100(odds: int | float, true_probability: float) -> float:
    """Expected profit per 100 units staked."""
    return expected_value(odds, true_probability, stake=100.0)


def expected_value_per_dollar(odds: int | float, true_probability: float) -> float:
    """Expected profit per dollar staked."""
    return expected_value_per_unit(odds, true_probability)


def calculate_payout(stake: Any, odds: Any, *, odds_format: str = "american") -> float:
    """Total payout, including returned stake, if a wager wins."""
    stake_value = _as_float(stake, "Stake")
    if odds_format not in {"american", "decimal"}:
        raise ValueError("odds_format must be 'american' or 'decimal'.")
    decimal_odds = _as_float(odds, "Decimal odds") if odds_format == "decimal" else american_to_decimal(odds)
    if odds_format == "decimal" and decimal_odds <= 1.0:
        raise ValueError("Decimal odds must be greater than 1.")
    return stake_value * decimal_odds


def calculate_profit_loss(stake: Any, odds: Any, *, won: bool, odds_format: str = "american") -> float:
    """Profit or loss for a settled single wager."""
    stake_value = _as_float(stake, "Stake")
    if not won:
        return -stake_value
    return calculate_payout(stake_value, odds, odds_format=odds_format) - stake_value


def calculate_ev(stake: Any, true_probability: Any, odds: Any, *, odds_format: str = "american") -> float:
    """Expected profit for a wager using American or decimal odds."""
    stake_value = _as_float(stake, "Stake")
    probability = _validate_probability(true_probability, "True probability")
    win_profit = calculate_profit_loss(stake_value, odds, won=True, odds_format=odds_format)
    loss = calculate_profit_loss(stake_value, odds, won=False, odds_format=odds_format)
    return probability * win_profit + (1.0 - probability) * loss


def calculate_ev_percent(stake: Any, true_probability: Any, odds: Any, *, odds_format: str = "american") -> float:
    """Expected profit as a percentage of stake."""
    stake_value = _as_float(stake, "Stake")
    if stake_value <= 0:
        raise ValueError("Stake must be positive.")
    return calculate_ev(stake_value, true_probability, odds, odds_format=odds_format) / stake_value * 100.0


def calculate_roi(stake: Any, expected_value_amount: Any) -> float:
    """Return ROI percentage for an expected or realized profit value."""
    stake_value = _as_float(stake, "Stake")
    if stake_value <= 0:
        raise ValueError("Stake must be positive.")
    return _as_float(expected_value_amount, "Expected value") / stake_value * 100.0


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


def kelly_binary_fraction_from_decimal(probability: float, decimal_odds: float) -> float:
    """Full Kelly fraction from a true probability and decimal odds."""
    p = _validate_probability(probability, "True probability")
    decimal_value = _as_float(decimal_odds, "Decimal odds")
    if decimal_value <= 1.0:
        raise ValueError("Decimal odds must be greater than 1.")
    b = decimal_value - 1.0
    return max(0.0, (b * p - (1.0 - p)) / b)


def full_kelly_fraction(odds: int | float, true_probability: float) -> float:
    """Full Kelly fraction for American odds."""
    return fractional_kelly(odds, true_probability, fraction=1.0)


def full_kelly_percent(odds: int | float, true_probability: float) -> float:
    """Full Kelly as a percentage."""
    return full_kelly_fraction(odds, true_probability) * 100.0


def fractional_kelly_percent(odds: int | float, true_probability: float, fraction: float = 0.25) -> float:
    """Fractional Kelly as a percentage."""
    return fractional_kelly(odds, true_probability, fraction=fraction) * 100.0


def scale_kelly_fraction(raw_full_kelly: Any, fraction: Any) -> float:
    """Scale a raw full-Kelly fraction by a non-negative fraction."""
    return max(0.0, _as_float(raw_full_kelly, "Raw full Kelly")) * max(0.0, _as_float(fraction, "Kelly fraction"))


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
