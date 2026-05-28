from __future__ import annotations

from typing import Any

from ..odds_math import american_to_decimal


def simulate_middle_ev(
    *,
    left_odds_american: Any,
    right_odds_american: Any,
    middle_hit_probability: float,
    stake_per_side: float = 100.0,
) -> dict[str, Any]:
    left_decimal = american_to_decimal(left_odds_american)
    right_decimal = american_to_decimal(right_odds_american)
    left_win = stake_per_side * (left_decimal - 1)
    right_win = stake_per_side * (right_decimal - 1)
    max_gain = round(left_win + right_win, 2)
    non_middle_profit = round(min(left_win - stake_per_side, right_win - stake_per_side), 2)
    max_loss = abs(non_middle_profit)
    break_even_probability = round(max_loss / (max_gain + max_loss), 6) if (max_gain + max_loss) > 0 else 1.0
    estimated_ev = round((middle_hit_probability * max_gain) + ((1 - middle_hit_probability) * non_middle_profit), 4)
    return {
        "max_gain": max_gain,
        "max_loss": round(max_loss, 2),
        "break_even_probability": break_even_probability,
        "estimated_ev": estimated_ev,
        "estimated_roi_percent": round((estimated_ev / (stake_per_side * 2)) * 100.0, 4),
    }
