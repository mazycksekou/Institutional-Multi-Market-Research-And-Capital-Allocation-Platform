from __future__ import annotations

from typing import Any

from .odds_math import american_to_decimal, decimal_to_american, normalize_probability


def calculate_market_hold(probabilities: list[Any]) -> float:
    normalized = [normalize_probability(value) for value in probabilities]
    hold = round(sum(normalized) - 1.0, 6)
    if sum(normalized) <= 0:
        raise ValueError("impossible market")
    return hold


def calculate_fair_probability(implied_probabilities: list[Any], index: int) -> float:
    normalized = [normalize_probability(value) for value in implied_probabilities]
    if not normalized or index < 0 or index >= len(normalized):
        raise ValueError("impossible market")
    total = sum(normalized)
    if total <= 0:
        raise ValueError("impossible market")
    return round(normalized[index] / total, 6)


def remove_two_way_vig(probability_a: Any, probability_b: Any) -> dict[str, float]:
    probabilities = [normalize_probability(probability_a), normalize_probability(probability_b)]
    total = sum(probabilities)
    if total <= 0:
        raise ValueError("impossible market")
    return {
        "fair_probability_a": round(probabilities[0] / total, 6),
        "fair_probability_b": round(probabilities[1] / total, 6),
        "market_hold": calculate_market_hold(probabilities),
    }


def remove_three_way_vig(probability_a: Any, probability_b: Any, probability_c: Any) -> dict[str, float]:
    probabilities = [
        normalize_probability(probability_a),
        normalize_probability(probability_b),
        normalize_probability(probability_c),
    ]
    total = sum(probabilities)
    if total <= 0:
        raise ValueError("impossible market")
    return {
        "fair_probability_a": round(probabilities[0] / total, 6),
        "fair_probability_b": round(probabilities[1] / total, 6),
        "fair_probability_c": round(probabilities[2] / total, 6),
        "market_hold": calculate_market_hold(probabilities),
    }


def calculate_fair_odds(probability: Any) -> dict[str, float | int]:
    normalized = normalize_probability(probability)
    if normalized <= 0:
        raise ValueError("impossible market")
    decimal_odds = round(1.0 / normalized, 6)
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
