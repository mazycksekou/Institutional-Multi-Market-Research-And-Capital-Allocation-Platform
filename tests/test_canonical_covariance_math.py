from __future__ import annotations

import copy
import math

import pytest

from src.core.math_utils import (
    correlation,
    correlation_matrix,
    covariance,
    covariance_matrix,
    portfolio_variance,
)
from src.core.portfolio import correlated_exposure
from src.core.risk import portfolio_risk


def test_pairwise_covariance_behavior_remains_unchanged() -> None:
    assert covariance([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) == pytest.approx(1.0, abs=1e-12)


def test_pairwise_correlation_behavior_remains_unchanged() -> None:
    assert correlation([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) == pytest.approx(1.0, abs=1e-12)


def test_correlation_matrix_behavior_remains_unchanged() -> None:
    matrix = correlation_matrix([[1.0, 2.0], [3.0, 4.0]])
    assert matrix[0] == pytest.approx([1.0, 1.0], abs=1e-12)
    assert matrix[1] == pytest.approx([1.0, 1.0], abs=1e-12)


def test_covariance_matrix_empty_input_returns_empty_list() -> None:
    assert covariance_matrix([]) == []


def test_covariance_matrix_one_series_and_two_observations() -> None:
    single = covariance_matrix([[1.0, 2.0]])
    pair = covariance_matrix([[1.0, 2.0], [3.0, 5.0]])

    assert single[0] == pytest.approx([0.5], abs=1e-12)
    assert pair[0] == pytest.approx([0.5, 1.0], abs=1e-12)
    assert pair[1] == pytest.approx([1.0, 2.0], abs=1e-12)


def test_covariance_matrix_is_deterministic_and_does_not_mutate_inputs() -> None:
    data = [[1.0, 2.0, 3.0], [3.0, 2.0, 1.0], [1.0, 1.0, 1.0]]
    original = copy.deepcopy(data)

    first = covariance_matrix(data)
    second = covariance_matrix(data)

    assert data == original
    assert first == second


def test_covariance_matrix_preserves_series_order_and_values() -> None:
    matrix = covariance_matrix([[1.0, 2.0, 3.0], [1.0, 1.0, 1.0], [3.0, 2.0, 1.0]])

    assert len(matrix) == 3
    assert all(len(row) == 3 for row in matrix)
    assert matrix[0][0] == pytest.approx(1.0, abs=1e-12)
    assert matrix[1][1] == pytest.approx(0.0, abs=1e-12)
    assert matrix[2][2] == pytest.approx(1.0, abs=1e-12)
    assert matrix[0][1] == pytest.approx(0.0, abs=1e-12)
    assert matrix[0][2] == pytest.approx(-1.0, abs=1e-12)
    assert matrix[1][2] == pytest.approx(0.0, abs=1e-12)
    assert matrix[0][2] == pytest.approx(matrix[2][0], abs=1e-12)
    assert matrix[0][1] == pytest.approx(matrix[1][0], abs=1e-12)


def test_covariance_matrix_constant_series_behavior() -> None:
    matrix = covariance_matrix([[1.0, 1.0, 1.0], [2.0, 4.0, 6.0]])
    assert matrix[0] == pytest.approx([0.0, 0.0], abs=1e-12)
    assert matrix[1] == pytest.approx([0.0, 4.0], abs=1e-12)


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ([[1.0], [2.0]], "Not enough data points."),
        ([[1.0, 2.0], [1.0, 2.0, 3.0]], "All series must have the same length."),
        ([[1.0, "bad"], [2.0, 3.0]], "data\\[0\\]\\[1\\] must be numeric."),
        ([[1.0, None], [2.0, 3.0]], "data\\[0\\]\\[1\\] must be numeric."),
        ([[1.0, math.nan], [2.0, 3.0]], "data\\[0\\]\\[1\\] must not be NaN."),
        ([[1.0, math.inf], [2.0, 3.0]], "data\\[0\\]\\[1\\] must be finite."),
        ([[1.0, -math.inf], [2.0, 3.0]], "data\\[0\\]\\[1\\] must be finite."),
    ],
)
def test_covariance_matrix_rejects_invalid_inputs(data: list[list[object]], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        covariance_matrix(data)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("series", "weights", "expected"),
    [
        ([[1.0, 2.0, 3.0]], [1.0], 1.0),
        ([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0]], [0.5, 0.5], 2.25),
        ([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]], [0.75, 0.25], 0.25),
        ([[1.0, 2.0, 3.0, 4.0], [1.0, -1.0, -1.0, 1.0]], [0.5, 0.5], 0.75),
        ([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0], [1.0, 1.0, 1.0]], [1 / 3, 1 / 3, 1 / 3], 0.0),
        ([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0]], [1.0, 0.0], 1.0),
    ],
)
def test_portfolio_variance_accepts_covariance_matrix_output(
    series: list[list[float]],
    weights: list[float],
    expected: float,
) -> None:
    result = portfolio_variance(weights, covariance_matrix(series))
    assert result == pytest.approx(expected, abs=1e-12)


def test_portfolio_risk_accepts_covariance_matrix_output() -> None:
    result = portfolio_risk([0.75, 0.25], covariance_matrix([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]]))
    assert result == pytest.approx(0.5, abs=1e-12)


def test_portfolio_consumer_accepts_covariance_matrix_output() -> None:
    result = correlated_exposure([0.75, 0.25], covariance_matrix([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]]))
    assert result == pytest.approx(0.25, abs=1e-6)
