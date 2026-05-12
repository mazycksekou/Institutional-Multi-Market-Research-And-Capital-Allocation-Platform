"""Bankroll and exposure risk calculations (stateless helpers)."""
from __future__ import annotations

from typing import Any, Optional


def bankroll_percentage_risked(stake: float, bankroll: float) -> float:
    if bankroll <= 0:
        return 0.0
    return max(0.0, min(1.0, stake / bankroll))


def exposure_single_bet(stake: float) -> float:
    return max(0.0, float(stake))


def exposure_daily(stakes: list[float]) -> float:
    return sum(max(0.0, s) for s in stakes)


def exposure_by_key(stakes_by_key: dict[str, float], key: str) -> float:
    return max(0.0, float(stakes_by_key.get(key, 0.0)))


def correlation_group_exposure(stakes_by_group: dict[str, float], group: str) -> float:
    return exposure_by_key(stakes_by_group, group)


def max_loss_correlated_bets(stakes: list[float], correlation_matrix_max: float = 1.0) -> float:
    """Upper bound if all legs lose together."""
    if not stakes:
        return 0.0
    return sum(stakes) * min(1.0, max(0.0, correlation_matrix_max))


def drawdown_tracker(equity_series: list[float]) -> dict[str, Any]:
    if not equity_series:
        return {"max_drawdown_pct": None, "current_drawdown_pct": None}
    peak = equity_series[0]
    max_dd = 0.0
    for x in equity_series:
        peak = max(peak, x)
        dd = (peak - x) / peak if peak else 0.0
        max_dd = max(max_dd, dd)
    cur_peak = max(equity_series)
    cur = equity_series[-1]
    cur_dd = (cur_peak - cur) / cur_peak if cur_peak else 0.0
    return {"max_drawdown_pct": round(max_dd * 100, 2), "current_drawdown_pct": round(cur_dd * 100, 2)}


def risk_of_ruin_estimate(
    win_prob: float,
    payoff_ratio: float,
    bankroll_units: float,
    units_risked: float,
    trials: int = 1000,
) -> float:
    """
    Very rough Monte-Carlo-free upper bound using gambler's ruin approximation for even bets.
    For production use simulation. Returns approximate probability (0-1).
    """
    if win_prob <= 0 or win_prob >= 1 or bankroll_units <= 0 or units_risked <= 0:
        return 1.0
    q = 1 - win_prob
    if abs(payoff_ratio - 1) < 1e-9:
        try:
            r = q / win_prob
            if r >= 1:
                return min(1.0, (q / win_prob) ** bankroll_units)
        except Exception:
            pass
    return min(1.0, max(0.0, (1 - win_prob) ** 10))


def roi_pct(profit: float, staked: float) -> Optional[float]:
    if staked == 0:
        return None
    return round(profit / staked * 100, 2)


def yield_pct(profit: float, num_bets: int) -> Optional[float]:
    if num_bets == 0:
        return None
    return round(profit / num_bets, 4)


def profit_factor(gross_wins: float, gross_losses: float) -> Optional[float]:
    if gross_losses == 0:
        return None if gross_wins == 0 else float("inf")
    return round(gross_wins / abs(gross_losses), 3)


def average_clv(clv_values: list[Optional[float]]) -> Optional[float]:
    vals = [v for v in clv_values if v is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 3)
