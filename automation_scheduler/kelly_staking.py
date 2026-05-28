from __future__ import annotations

from typing import Any


KELLY_PARAMS = {
    "kelly_mode": "full_kelly_primary",
    "full_kelly_fraction": 1.00,
    "half_kelly_fraction": 0.50,
    "quarter_kelly_fraction": 0.25,
    "eighth_kelly_fraction": 0.125,
    "full_kelly_allowed_for_review": True,
    "full_kelly_auto_execution_allowed": False,
}


def return_zero_if_no_edge() -> float:
    return 0.0


def return_zero_if_probability_invalid() -> float:
    return 0.0


def return_zero_if_odds_invalid() -> float:
    return 0.0


def _valid_probability(probability: float) -> bool:
    return isinstance(probability, (int, float)) and 0 < float(probability) < 1


def _american_to_decimal(american_odds: float) -> float:
    if american_odds == 0:
        raise ValueError("american_odds cannot be zero")
    if american_odds > 0:
        return 1.0 + (american_odds / 100.0)
    return 1.0 + (100.0 / abs(american_odds))


def calculate_full_kelly_binary(probability: float, decimal_odds: float) -> float:
    if not _valid_probability(probability):
        return return_zero_if_probability_invalid()
    if not isinstance(decimal_odds, (int, float)) or float(decimal_odds) <= 1.0:
        return return_zero_if_odds_invalid()
    b = float(decimal_odds) - 1.0
    p = float(probability)
    q = 1.0 - p
    edge = (b * p) - q
    if edge <= 0:
        return return_zero_if_no_edge()
    return max(0.0, edge / b)


def calculate_full_kelly_american(probability: float, american_odds: float) -> float:
    try:
        decimal_odds = _american_to_decimal(float(american_odds))
    except Exception:
        return return_zero_if_odds_invalid()
    return calculate_full_kelly_binary(probability, decimal_odds)


def calculate_raw_full_kelly(probability: float, odds: float) -> float:
    if odds > 1.0:
        return calculate_full_kelly_binary(probability, odds)
    return calculate_full_kelly_american(probability, odds)


def calculate_fractional_kelly(raw_full_kelly: float, fraction: float) -> float:
    return max(0.0, float(raw_full_kelly) * max(0.0, float(fraction)))


def select_kelly_mode(raw_full_kelly: float, confidence_inputs: dict[str, Any], risk_inputs: dict[str, Any]) -> str:
    if raw_full_kelly <= 0:
        return "no_stake"
    hard_block = bool(confidence_inputs.get("hard_block")) or bool(risk_inputs.get("hard_block"))
    if hard_block:
        return "no_stake"
    confidence_tier = str(confidence_inputs.get("confidence_tier", "low"))
    if confidence_tier == "high" and bool(risk_inputs.get("full_kelly_allowed", True)):
        return "operating_full_kelly"
    if confidence_tier == "medium":
        return "half_kelly" if float(raw_full_kelly) >= 0.02 else "quarter_kelly"
    return "no_stake"


def calculate_operating_full_kelly(raw_full_kelly: float, confidence_inputs: dict[str, Any], risk_inputs: dict[str, Any]) -> dict[str, Any]:
    mode = select_kelly_mode(raw_full_kelly, confidence_inputs, risk_inputs)
    if mode == "operating_full_kelly":
        operating = calculate_fractional_kelly(raw_full_kelly, KELLY_PARAMS["full_kelly_fraction"])
        fallback = calculate_fractional_kelly(raw_full_kelly, KELLY_PARAMS["half_kelly_fraction"])
    elif mode == "half_kelly":
        operating = calculate_fractional_kelly(raw_full_kelly, KELLY_PARAMS["half_kelly_fraction"])
        fallback = calculate_fractional_kelly(raw_full_kelly, KELLY_PARAMS["quarter_kelly_fraction"])
    elif mode == "quarter_kelly":
        operating = calculate_fractional_kelly(raw_full_kelly, KELLY_PARAMS["quarter_kelly_fraction"])
        fallback = calculate_fractional_kelly(raw_full_kelly, KELLY_PARAMS["eighth_kelly_fraction"])
    else:
        operating = 0.0
        fallback = 0.0
    return {
        "raw_full_kelly_fraction": round(max(0.0, raw_full_kelly), 6),
        "operating_full_kelly_fraction": round(operating, 6),
        "fractional_fallback_fraction": round(fallback, 6),
        "recommended_kelly_mode": mode,
        "full_kelly_allowed_for_review": True,
        "full_kelly_auto_execution_allowed": False,
        "auto_execution_enabled": False,
    }
