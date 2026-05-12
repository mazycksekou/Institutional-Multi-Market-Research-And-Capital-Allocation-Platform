"""Asian handicap / totals helpers and Eastern odds format conversions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from quant_engine import american_to_decimal, implied_probability_from_american


def hong_kong_to_decimal(hk_odds: float) -> float:
    x = float(hk_odds)
    if x == 0:
        raise ValueError("Hong Kong odds cannot be zero.")
    return 1 + x


def malaysian_to_decimal(my_odds: float) -> float:
    """Malaysian odds: positive like HK; negative as risk/return ratio."""
    x = float(my_odds)
    if x == 0:
        raise ValueError("Malaysian odds cannot be zero.")
    if x > 0:
        return 1 + x
    return 1 + (1 / abs(x))


def indonesian_to_decimal(indo_odds: float) -> float:
    """Indonesian odds same shape as American but scaled by 1/100 vs HK-style."""
    x = float(indo_odds)
    if x == 0:
        raise ValueError("Indonesian odds cannot be zero.")
    if x > 0:
        return 1 + x
    return 1 + (1 / abs(x))


def decimal_to_hong_kong(decimal_odds: float) -> float:
    d = float(decimal_odds)
    if d <= 1:
        raise ValueError("Decimal odds must exceed 1.")
    return d - 1


def decimal_to_malaysian(decimal_odds: float) -> float:
    d = float(decimal_odds)
    if d <= 1:
        raise ValueError("Decimal odds must exceed 1.")
    if d >= 2:
        return d - 1
    return -(1 / (d - 1))


def decimal_to_indonesian(decimal_odds: float) -> float:
    return decimal_to_malaysian(decimal_odds)


def american_to_hong_kong(american: int | float) -> float:
    return decimal_to_hong_kong(american_to_decimal(american))


def quarter_line_split(line: float) -> tuple[float, float]:
    """Split a quarter (.25) handicap/total into two half-stake legs on adjacent half lines."""
    x = float(line)
    frac = abs(x - int(x))
    if abs(frac - 0.25) > 1e-9 and abs(frac - 0.75) > 1e-9:
        return x, x
    lower = int(x * 4) / 4
    upper = lower + 0.5
    if x < 0:
        lower, upper = -upper, -lower
    return lower, upper


@dataclass
class AsianHandicapSettlement:
    line: float
    push_probability: float
    half_win_probability: float
    half_loss_probability: float
    full_win_probability: float
    full_loss_probability: float
    notes: str


def asian_handicap_push_half_probabilities(
    spread_line: float,
    goal_diff_distribution: Optional[dict[int, float]] = None,
) -> AsianHandicapSettlement:
    """
    Placeholder distribution: without a model, return structural flags for quarter/half/full.
    If goal_diff_distribution provided (net goals vs line side), approximate win/push/half outcomes.
    """
    line = float(spread_line)
    lower, upper = quarter_line_split(line)
    is_quarter = abs(lower - upper) > 1e-9

    if goal_diff_distribution is None:
        return AsianHandicapSettlement(
            line=line,
            push_probability=0.0 if is_quarter else 0.08,
            half_win_probability=0.25 if is_quarter else 0.0,
            half_loss_probability=0.25 if is_quarter else 0.0,
            full_win_probability=0.25,
            full_loss_probability=0.25,
            notes="Uniform placeholder; supply goal_diff_distribution for calibrated probabilities.",
        )

    # Minimal example: sum P(net = k) for push at integer line, etc. — left as extension hook.
    return AsianHandicapSettlement(
        line=line,
        push_probability=0.0,
        half_win_probability=0.0,
        half_loss_probability=0.0,
        full_win_probability=0.0,
        full_loss_probability=0.0,
        notes="Distribution supplied but mapping not implemented in this build.",
    )


def compare_asian_handicap_to_american_spread(
    asian_decimal_price: float,
    american_spread_price: int,
) -> dict[str, Any]:
    """Compare implied probs between Asian-priced side and American spread price."""
    p_asian = 1 / float(asian_decimal_price) if asian_decimal_price > 1 else None
    p_us = implied_probability_from_american(american_spread_price)
    if p_asian is None:
        return {"value_gap": None, "better_side": None}
    gap = (p_asian - p_us) * 100
    better = "asian" if gap < 0 else "american" if gap > 0 else "tie"
    return {"value_gap_percent": round(gap, 3), "better_side": better}


def asian_total_quarter_split(total_line: float) -> tuple[float, float]:
    return quarter_line_split(total_line)


def asian_market_lead_lag_score(sharp_move_bps: float, soft_move_bps: float) -> float:
    """Heuristic lead/lag: positive if soft trails sharp move (bps = basis points of implied move)."""
    return float(sharp_move_bps - soft_move_bps)


def mlb_market_grading_placeholder(market_type: str, result: str) -> dict[str, Any]:
    """Stub grading hooks for MLB markets — integrate with settlement feed in production."""
    return {
        "market_type": market_type,
        "result": result,
        "graded": False,
        "message": "MLB grading requires official settlement data; placeholder only.",
    }


def mlb_adjustment_placeholder(name: str, factor: float = 1.0) -> dict[str, Any]:
    return {"adjustment": name, "factor": factor, "active": False, "message": "Placeholder — wire model inputs to enable."}


def mlb_grade_full_game_moneyline(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_full_game_ml", result)


def mlb_grade_run_line(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_run_line", result)


def mlb_grade_totals(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_totals", result)


def mlb_grade_team_totals(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_team_totals", result)


def mlb_grade_first5_moneyline(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_f5_ml", result)


def mlb_grade_first5_run_line(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_f5_rl", result)


def mlb_grade_first5_total(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_f5_total", result)


def mlb_grade_pitcher_strikeouts(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_pitcher_k", result)


def mlb_grade_pitcher_outs(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_pitcher_outs", result)


def mlb_grade_batter_hits(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_batter_hits", result)


def mlb_grade_batter_total_bases(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_batter_tb", result)


def mlb_grade_batter_rbi(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_batter_rbi", result)


def mlb_grade_batter_runs(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_batter_runs", result)


def mlb_grade_home_run_prop(result: str) -> dict[str, Any]:
    return mlb_market_grading_placeholder("mlb_hr", result)


def mlb_bullpen_fatigue_adjustment() -> dict[str, Any]:
    return mlb_adjustment_placeholder("bullpen_fatigue")


def mlb_starting_pitcher_adjustment() -> dict[str, Any]:
    return mlb_adjustment_placeholder("starting_pitcher")


def mlb_park_factor_adjustment() -> dict[str, Any]:
    return mlb_adjustment_placeholder("park_factor")


def mlb_weather_adjustment() -> dict[str, Any]:
    return mlb_adjustment_placeholder("weather")


def mlb_umpire_adjustment() -> dict[str, Any]:
    return mlb_adjustment_placeholder("umpire")


def mlb_lineup_strength_adjustment() -> dict[str, Any]:
    return mlb_adjustment_placeholder("lineup_strength")

