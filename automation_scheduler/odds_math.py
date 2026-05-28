from __future__ import annotations

from typing import Any


def validate_odds(odds: Any, *, odds_format: str = "american") -> bool:
    value = float(odds)
    if odds_format == "american":
        if value == 0:
            raise ValueError("american odds cannot be zero")
    elif odds_format == "decimal":
        if value <= 1:
            raise ValueError("decimal odds must be greater than 1")
    else:
        raise ValueError("unsupported odds format")
    return True


def validate_probability(probability: Any) -> bool:
    value = float(probability)
    if value < 0 or value > 1:
        raise ValueError("probability must be between 0 and 1")
    return True


def american_to_decimal(odds: Any) -> float:
    validate_odds(odds, odds_format="american")
    odds_value = float(odds)
    if odds_value > 0:
        return round(1 + (odds_value / 100.0), 6)
    return round(1 + (100.0 / abs(odds_value)), 6)


def american_to_implied_probability(odds: Any) -> float:
    validate_odds(odds, odds_format="american")
    odds_value = float(odds)
    if odds_value > 0:
        return round(100.0 / (odds_value + 100.0), 6)
    return round(abs(odds_value) / (abs(odds_value) + 100.0), 6)


def decimal_to_implied_probability(decimal_odds: Any) -> float:
    validate_odds(decimal_odds, odds_format="decimal")
    return round(1.0 / float(decimal_odds), 6)


def decimal_to_american(decimal_odds: Any) -> int:
    validate_odds(decimal_odds, odds_format="decimal")
    decimal_value = float(decimal_odds)
    if decimal_value >= 2:
        return int(round((decimal_value - 1) * 100))
    return int(round(-100 / (decimal_value - 1)))


def remove_two_way_vig(probability_a: Any, probability_b: Any) -> dict[str, float]:
    prob_a = float(probability_a)
    prob_b = float(probability_b)
    total = prob_a + prob_b
    if total <= 0:
        raise ValueError("probabilities must sum to a positive value")
    return {
        "fair_probability_a": round(prob_a / total, 6),
        "fair_probability_b": round(prob_b / total, 6),
        "vig": round(max(0.0, total - 1.0), 6),
    }


def calculate_payout(stake: Any, odds: Any, *, odds_format: str = "american") -> float:
    stake_value = float(stake)
    decimal_odds = float(odds) if odds_format == "decimal" else american_to_decimal(odds)
    return round(stake_value * decimal_odds, 6)


def calculate_profit_loss(stake: Any, odds: Any, *, won: bool, odds_format: str = "american") -> float:
    stake_value = float(stake)
    if not won:
        return round(-stake_value, 6)
    return round(calculate_payout(stake_value, odds, odds_format=odds_format) - stake_value, 6)


def calculate_ev(stake: Any, true_probability: Any, odds: Any, *, odds_format: str = "american") -> float:
    stake_value = float(stake)
    probability = float(true_probability)
    validate_probability(probability)
    win_profit = calculate_profit_loss(stake_value, odds, won=True, odds_format=odds_format)
    loss = calculate_profit_loss(stake_value, odds, won=False, odds_format=odds_format)
    return round((probability * win_profit) + ((1 - probability) * loss), 6)


def calculate_ev_percent(stake: Any, true_probability: Any, odds: Any, *, odds_format: str = "american") -> float:
    stake_value = float(stake)
    if stake_value <= 0:
        raise ValueError("stake must be positive")
    return round((calculate_ev(stake_value, true_probability, odds, odds_format=odds_format) / stake_value) * 100.0, 6)


def calculate_roi(stake: Any, expected_value: Any) -> float:
    stake_value = float(stake)
    if stake_value <= 0:
        raise ValueError("stake must be positive")
    return round((float(expected_value) / stake_value) * 100.0, 6)


def normalize_probability(probability: Any) -> float:
    value = float(probability)
    if value > 1:
        value = value / 100.0
    if value < 0 or value > 1:
        raise ValueError("probability must be between 0 and 1")
    return round(value, 6)
