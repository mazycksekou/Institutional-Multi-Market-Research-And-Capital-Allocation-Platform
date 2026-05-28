from __future__ import annotations

import math
from typing import Any

from .bookmaker_normalizer import normalize_market_name, normalize_offer, normalize_selection_name
from .market_identity_resolver import resolve_market_identity
from .odds_math import american_to_decimal


def _normal_probability_between(low: float, high: float, mean: float, std_dev: float) -> float:
    if std_dev <= 0:
        return 0.0
    z_low = (low - mean) / (std_dev * math.sqrt(2))
    z_high = (high - mean) / (std_dev * math.sqrt(2))
    return max(0.0, min(1.0, (math.erf(z_high) - math.erf(z_low)) / 2))


def detect_middle_opportunity(
    left_offer: dict[str, Any],
    right_offer: dict[str, Any],
    *,
    stake_per_side: float = 100.0,
    market_identity_confidence: float | None = None,
    stale_data_risk: bool = False,
    max_timestamp_skew_seconds: int = 120,
    model_distribution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    left = normalize_offer(left_offer)
    right = normalize_offer(right_offer)
    market = normalize_market_name(left.get("market"))
    confidence = market_identity_confidence if market_identity_confidence is not None else resolve_market_identity(left, right)["confidence"]
    if confidence < 85:
        return {"candidate_found": False, "reason": "low_market_identity_confidence"}
    if stale_data_risk:
        return {"candidate_found": False, "reason": "stale_data"}
    left_ts = left_offer.get("timestamp")
    right_ts = right_offer.get("timestamp")
    if isinstance(left_ts, (int, float)) and isinstance(right_ts, (int, float)) and abs(int(left_ts) - int(right_ts)) > max_timestamp_skew_seconds:
        return {"candidate_found": False, "reason": "timestamp_mismatch"}

    left_line = float(left.get("line") or 0)
    right_line = float(right.get("line") or 0)
    left_decimal = american_to_decimal(left["odds"])
    right_decimal = american_to_decimal(right["odds"])
    left_profit = stake_per_side * (left_decimal - 1)
    right_profit = stake_per_side * (right_decimal - 1)
    max_loss = round(stake_per_side * 2 - min(left_profit, right_profit), 2)
    non_middle_profit = min(left_profit - stake_per_side, right_profit - stake_per_side)

    if market == "total":
        over_line = left_line if normalize_selection_name(left["selection"]) == "over" else right_line
        under_line = left_line if normalize_selection_name(left["selection"]) == "under" else right_line
        middle_width = round(under_line - over_line, 4)
        middle_zone = [round(over_line, 4), round(under_line, 4)]
    else:
        favorite_line = left_line if left_line < right_line else right_line
        dog_line = right_line if favorite_line == left_line else left_line
        middle_width = round(dog_line - favorite_line, 4)
        middle_zone = [round(abs(favorite_line), 4), round(abs(dog_line), 4)]

    if middle_width <= 0:
        return {"candidate_found": False, "reason": "no_middle_width"}

    middle_hit_probability = float(
        (model_distribution or {}).get("middle_hit_probability")
        or _normal_probability_between(
            middle_zone[0],
            middle_zone[1],
            float((model_distribution or {}).get("mean", sum(middle_zone) / 2.0)),
            float((model_distribution or {}).get("std_dev", max(1.0, middle_width))),
        )
    )
    middle_win = round(left_profit + right_profit, 2)
    break_even_probability = round(max_loss / (middle_win + max_loss), 6) if (middle_win + max_loss) > 0 else 1.0
    expected_value = round((middle_hit_probability * middle_win) + ((1 - middle_hit_probability) * non_middle_profit), 4)
    risk_acceptable = middle_hit_probability >= break_even_probability
    if expected_value <= 0 and not risk_acceptable:
        return {
            "candidate_found": False,
            "reason": "negative_middle_ev",
            "middle_width": middle_width,
            "break_even_probability": break_even_probability,
        }

    return {
        "candidate_found": True,
        "candidate_type": "middle_candidate",
        "market": market,
        "middle_zone": middle_zone,
        "middle_width": middle_width,
        "middle_hit_probability": round(middle_hit_probability, 6),
        "break_even_probability": break_even_probability,
        "expected_value": expected_value,
        "estimated_roi_percent": round((expected_value / (stake_per_side * 2)) * 100.0, 4),
        "max_loss": round(max_loss, 2),
        "max_gain": middle_win,
        "line_match_confidence": round(float(confidence), 2),
        "stale_data_risk": False,
        "stake_plan": [
            {"bookmaker": left["bookmaker"], "selection": left["selection"], "line": left_line, "stake": round(stake_per_side, 2)},
            {"bookmaker": right["bookmaker"], "selection": right["selection"], "line": right_line, "stake": round(stake_per_side, 2)},
        ],
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
    }
