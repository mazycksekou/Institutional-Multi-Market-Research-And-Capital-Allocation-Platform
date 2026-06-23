from __future__ import annotations

import math
import pytest

from src.core.math_utils import (
    mean,
    median,
    variance,
    std_dev,
    dot_product,
    weighted_sum,
    covariance,
    correlation,
    correlation_matrix,
    portfolio_return,
    portfolio_variance,
)


def test_mean_normal() -> None:
    assert mean([1.0, 2.0, 3.0]) == 2.0


def test_mean_empty() -> None:
    with pytest.raises(ValueError):
        mean([])


def test_median_odd() -> None:
    assert median([3.0, 1.0, 2.0]) == 2.0


def test_median_even() -> None:
    assert median([1.0, 2.0, 3.0, 4.0]) == 2.5


def test_variance() -> None:
    result = variance([1.0, 2.0, 3.0])
    assert pytest.approx(result, 0.001) == 1.0


def test_std_dev() -> None:
    result = std_dev([1.0, 2.0, 3.0])
    assert pytest.approx(result, 0.001) == 1.0


def test_dot_product() -> None:
    assert dot_product([1.0, 2.0], [3.0, 4.0]) == 11.0


def test_dot_product_mismatch() -> None:
    with pytest.raises(ValueError):
        dot_product([1.0], [1.0, 2.0])


def test_weighted_sum() -> None:
    assert weighted_sum([1.0, 2.0], [0.3, 0.7]) == 1.7


def test_weighted_sum_bad_weights() -> None:
    with pytest.raises(ValueError):
        weighted_sum([1.0, 2.0], [1.0, 1.0])


def test_covariance() -> None:
    x = [1.0, 2.0, 3.0]
    y = [4.0, 5.0, 6.0]
    result = covariance(x, y)
    assert pytest.approx(result, 0.001) == 1.0


def test_covariance_mismatch() -> None:
    with pytest.raises(ValueError):
        covariance([1.0], [1.0, 2.0])


def test_correlation() -> None:
    x = [1.0, 2.0, 3.0]
    y = [4.0, 5.0, 6.0]
    assert pytest.approx(correlation(x, y), 0.001) == 1.0


def test_correlation_zero_variance() -> None:
    with pytest.raises(ValueError):
        correlation([1.0, 1.0, 1.0], [4.0, 5.0, 6.0])


def test_correlation_matrix_symmetry() -> None:
    data = [[1.0, 2.0], [3.0, 4.0]]
    mat = correlation_matrix(data)
    assert len(mat) == 2
    assert pytest.approx(mat[0][1], 0.001) == mat[1][0]


def test_portfolio_return() -> None:
    returns = [0.1, 0.2]
    weights = [0.5, 0.5]
    assert portfolio_return(returns, weights) == 0.15


def test_portfolio_variance() -> None:
    weights = [0.5, 0.5]
    cov = [[0.04, 0.02], [0.02, 0.09]]
    result = portfolio_variance(weights, cov)
    assert round(result, 4) > 0


def test_empty_input_errors() -> None:
    with pytest.raises(ValueError):
        variance([])
    with pytest.raises(ValueError):
        std_dev([])
    with pytest.raises(ValueError):
        covariance([], [])


def test_no_live_imports() -> None:
    import inspect
    for func in [mean, median, variance, std_dev, dot_product, weighted_sum,
                  covariance, correlation, correlation_matrix,
                  portfolio_return, portfolio_variance]:
        source = inspect.getsource(func)
        assert "importlib" not in source
        assert "requests" not in source
