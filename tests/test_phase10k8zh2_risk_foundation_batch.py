from __future__ import annotations

import pytest

from src.core.risk import (
    sharpe_ratio,
    max_drawdown,
    portfolio_risk,
    exposure_summary,
)


def test_sharpe_ratio_normal() -> None:
    # annualised ratio
    result = sharpe_ratio(expected_return=0.1, volatility=0.2, risk_free_rate=0.02)
    assert pytest.approx(result, 0.001) == 0.4


def test_sharpe_ratio_zero_volatility() -> None:
    with pytest.raises(ValueError):
        sharpe_ratio(expected_return=0.1, volatility=0.0)


def test_max_drawdown_normal() -> None:
    equity = [100.0, 90.0, 80.0, 100.0]
    result = max_drawdown(equity)
    # max drawdown from peak 100 to trough 80 -> -20%
    assert pytest.approx(result, 0.001) == -20.0


def test_max_drawdown_no_drawdown() -> None:
    equity = [100.0, 110.0, 120.0]
    result = max_drawdown(equity)
    assert result == 0.0


def test_portfolio_risk() -> None:
    weights = [0.6, 0.4]
    cov = [[0.04, 0.01], [0.01, 0.09]]
    result = portfolio_risk(weights, cov)
    assert isinstance(result, float)
    assert result > 0


def test_exposure_summary() -> None:
    stakes = {"A": 100.0, "B": 200.0}
    result = exposure_summary(stakes)
    assert result["total_exposure"] == 300.0
    assert len(result["positions"]) == 2
    assert result["positions"]["A"]["exposure"] == 100.0
    assert result["positions"]["A"]["exposure_pct"] == pytest.approx(100.0 / 300.0, 1e-3)


def test_exposure_summary_empty() -> None:
    result = exposure_summary({})
    assert result["total_exposure"] == 0.0
    assert result["positions"] == {}
