from __future__ import annotations

from typing import Any

from src.core.math_utils import (
    book_hold_n_way,
    decimal_to_american,
    fair_decimal_odds_from_probability,
    no_vig_probabilities_n_way,
    no_vig_probabilities_three_way,
    no_vig_probabilities_two_way,
    normalize_probability,
)


def calculate_market_hold(probabilities: list[Any]) -> float:
    normalized = [normalize_probability(value) for value in probabilities]
    if sum(normalized) <= 0:
        raise ValueError("impossible market")
    return round(book_hold_n_way(normalized), 6)


def calculate_fair_probability(implied_probabilities: list[Any], index: int) -> float:
    normalized = [normalize_probability(value) for value in implied_probabilities]
    if not normalized or index < 0 or index >= len(normalized):
        raise ValueError("impossible market")
    total = sum(normalized)
    if total <= 0:
        raise ValueError("impossible market")
    return round(no_vig_probabilities_n_way(normalized)[index], 6)


def remove_two_way_vig(probability_a: Any, probability_b: Any) -> dict[str, float]:
    probabilities = [normalize_probability(probability_a), normalize_probability(probability_b)]
    fair_a, fair_b = no_vig_probabilities_two_way(probabilities[0], probabilities[1])
    return {
        "fair_probability_a": round(fair_a, 6),
        "fair_probability_b": round(fair_b, 6),
        "market_hold": calculate_market_hold(probabilities),
    }


def remove_three_way_vig(probability_a: Any, probability_b: Any, probability_c: Any) -> dict[str, float]:
    probabilities = [
        normalize_probability(probability_a),
        normalize_probability(probability_b),
        normalize_probability(probability_c),
    ]
    fair_a, fair_b, fair_c = no_vig_probabilities_three_way(probabilities[0], probabilities[1], probabilities[2])
    return {
        "fair_probability_a": round(fair_a, 6),
        "fair_probability_b": round(fair_b, 6),
        "fair_probability_c": round(fair_c, 6),
        "market_hold": calculate_market_hold(probabilities),
    }


def calculate_fair_odds(probability: Any) -> dict[str, float | int]:
    normalized = normalize_probability(probability)
    if normalized <= 0:
        raise ValueError("impossible market")
    decimal_odds = round(fair_decimal_odds_from_probability(normalized), 6)
    return {
        "fair_probability": normalized,
        "decimal_odds": decimal_odds,
        "american_odds": decimal_to_american(decimal_odds),
    }


def calculate_consensus_probability(probabilities: list[Any]) -> float:
    normalized = [normalize_probability(value) for value in probabilities]
    if not normalized:
        raise ValueError("at least one probability is required")
    return round(sum(normalized) / len(normalized), 6)
