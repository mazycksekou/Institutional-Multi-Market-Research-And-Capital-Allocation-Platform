from __future__ import annotations

from typing import Any

from src.core.math_utils import (
    american_to_decimal as _core_american_to_decimal,
    american_to_implied_probability as _core_american_to_implied_probability,
    calculate_ev as _core_calculate_ev,
    calculate_ev_percent as _core_calculate_ev_percent,
    calculate_payout as _core_calculate_payout,
    calculate_profit_loss as _core_calculate_profit_loss,
    calculate_roi as _core_calculate_roi,
    decimal_to_american as _core_decimal_to_american,
    decimal_to_implied_probability as _core_decimal_to_implied_probability,
    normalize_probability as _core_normalize_probability,
    remove_two_way_vig as _core_remove_two_way_vig,
)


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
    return round(_core_american_to_decimal(float(odds)), 6)


def american_to_implied_probability(odds: Any) -> float:
    validate_odds(odds, odds_format="american")
    return round(_core_american_to_implied_probability(float(odds)), 6)


def decimal_to_implied_probability(decimal_odds: Any) -> float:
    validate_odds(decimal_odds, odds_format="decimal")
    return round(_core_decimal_to_implied_probability(float(decimal_odds)), 6)


def decimal_to_american(decimal_odds: Any) -> int:
    validate_odds(decimal_odds, odds_format="decimal")
    return _core_decimal_to_american(float(decimal_odds))


def remove_two_way_vig(probability_a: Any, probability_b: Any) -> dict[str, float]:
    fair = _core_remove_two_way_vig(probability_a, probability_b)
    return {
        "fair_probability_a": round(fair["fair_probability_a"], 6),
        "fair_probability_b": round(fair["fair_probability_b"], 6),
        "vig": round(fair["vig"], 6),
    }


def calculate_payout(stake: Any, odds: Any, *, odds_format: str = "american") -> float:
    return round(_core_calculate_payout(stake, odds, odds_format=odds_format), 6)


def calculate_profit_loss(stake: Any, odds: Any, *, won: bool, odds_format: str = "american") -> float:
    return round(_core_calculate_profit_loss(stake, odds, won=won, odds_format=odds_format), 6)


def calculate_ev(stake: Any, true_probability: Any, odds: Any, *, odds_format: str = "american") -> float:
    return round(_core_calculate_ev(stake, true_probability, odds, odds_format=odds_format), 6)


def calculate_ev_percent(stake: Any, true_probability: Any, odds: Any, *, odds_format: str = "american") -> float:
    return round(_core_calculate_ev_percent(stake, true_probability, odds, odds_format=odds_format), 6)


def calculate_roi(stake: Any, expected_value: Any) -> float:
    return round(_core_calculate_roi(stake, expected_value), 6)


def normalize_probability(probability: Any) -> float:
    return round(_core_normalize_probability(probability), 6)
