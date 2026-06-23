"""Canonical risk helpers.

These functions are stateless and dependency‑free (except math) so that
pricing, backtest, and dashboard code can share one implementation.
"""
from __future__ import annotations

import math
from typing import Sequence


def _ensure_positive(value: float, name: str) -> float:
    if value <= 0:
        raise ValueError(f"{name} must be positive.")
    return value


def sharpe_ratio(
    expected_return: float,
    volatility: float,
    risk_free_rate: float = 0.0,
) -> float:
    """Annualised Sharpe ratio.

    Parameters
    ----------
    expected_return : float
        Expected annual return (e.g. 0.10 for 10%).
    volatility : float
        Annual standard deviation of returns (must be >0).
    risk_free_rate : float
        Risk‑free annual rate (default 0.0).

    Returns
    -------
    float
        Sharpe ratio = (expected_return - risk_free_rate) / volatility.
    """
    vol = _ensure_positive(volatility, "volatility")
    return (expected_return - risk_free_rate) / vol


def max_drawdown(equity_curve: Sequence[float]) -> float:
    """Maximum drawdown as a negative percentage of peak value.

    Parameters
    ----------
    equity_curve : Sequence[float]
        Time‑ordered portfolio values.

    Returns
    -------
    float
        Maximum drawdown percentage (e.g. -20.0 for -20%).
        Returns 0.0 if the curve is always non‑decreasing.
    """
    if not equity_curve:
        raise ValueError("equity_curve must not be empty.")

    peak = equity_curve[0]
    max_dd = 0.0

    for value in equity_curve:
        peak = max(peak, value)
        dd = (value - peak) / peak if peak else 0.0
        if dd < max_dd:
            max_dd = dd

    return round(max_dd * 100.0, 4)


def portfolio_risk(
    weights: Sequence[float],
    covariance_matrix: Sequence[Sequence[float]],
) -> float:
    """Portfolio standard deviation given weights and covariance matrix.

    Parameters
    ----------
    weights : Sequence[float]
        Portfolio weights (must sum to 1).
    covariance_matrix : Sequence[Sequence[float]]
        N x N covariance matrix.

    Returns
    -------
    float
        Portfolio volatility (standard deviation).
    """
    w = list(weights)
    n = len(w)

    if n == 0:
        raise ValueError("weights must not be empty.")
    if len(covariance_matrix) != n:
        raise ValueError("covariance_matrix dimension must match weight count.")
    if not math.isclose(sum(w), 1.0, rel_tol=1e-6):
        raise ValueError("weights must sum to 1.")

    variance = 0.0
    for i in range(n):
        for j in range(n):
            variance += w[i] * w[j] * covariance_matrix[i][j]

    return math.sqrt(max(0.0, variance))


def exposure_summary(
    stakes: dict[str, float],
) -> dict:
    """Summarise exposure across positions.

    Parameters
    ----------
    stakes : dict[str, float]
        Map of position identifier -> stake amount.

    Returns
    -------
    dict
        - "total_exposure": sum of all stakes
        - "positions": dict of position_id -> {exposure, exposure_pct}
    """
    total = sum(stakes.values())
    positions = {}
    for key, amount in stakes.items():
        positions[key] = {
            "exposure": amount,
            "exposure_pct": round(amount / total, 6) if total else 0.0,
        }
    return {
        "total_exposure": total,
        "positions": positions,
    }
