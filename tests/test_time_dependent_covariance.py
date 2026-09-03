from __future__ import annotations

import copy
import math

import pytest

from src.backtesting import (
    reconstruct_point_in_time_correlation,
    reconstruct_point_in_time_covariance,
)
from src.core.math_utils import (
    correlation,
    correlation_matrix,
    covariance,
    covariance_matrix,
    ewma_correlation,
    ewma_covariance,
    portfolio_variance,
    rolling_correlation,
    rolling_covariance,
)


def test_static_covariance_regression_surfaces_remain_unchanged() -> None:
    assert covariance([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) == pytest.approx(1.0, abs=1e-12)
    assert correlation([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) == pytest.approx(1.0, abs=1e-12)
    covariance_result = covariance_matrix([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]])
    correlation_result = correlation_matrix([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]])
    assert covariance_result[0] == pytest.approx([1.0, -1.0], abs=1e-12)
    assert covariance_result[1] == pytest.approx([-1.0, 1.0], abs=1e-12)
    assert correlation_result[0] == pytest.approx([1.0, -1.0], abs=1e-12)
    assert correlation_result[1] == pytest.approx([-1.0, 1.0], abs=1e-12)
    assert portfolio_variance([0.75, 0.25], [[1.0, -1.0], [-1.0, 1.0]]) == pytest.approx(0.25, abs=1e-12)


def test_rolling_covariance_warmup_window_and_sliding_behavior() -> None:
    result = rolling_covariance(
        [1.0, 2.0, 3.0, 10.0],
        [1.0, 2.0, 3.0, 10.0],
        window=3,
        min_periods=2,
        ddof=1,
    )

    assert result[0] is None
    assert result[1:] == pytest.approx([0.5, 1.0, 19.0], abs=1e-12)


@pytest.mark.parametrize(
    ("x_values", "y_values", "expected"),
    [
        ([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], 1.0),
        ([1.0, 2.0, 3.0], [3.0, 2.0, 1.0], -1.0),
        ([-1.0, 0.0, 1.0], [1.0, -2.0, 1.0], 0.0),
        ([5.0, 5.0, 5.0], [1.0, 2.0, 3.0], 0.0),
    ],
)
def test_rolling_covariance_handles_positive_negative_zero_and_constant_relationships(
    x_values: list[float],
    y_values: list[float],
    expected: float,
) -> None:
    result = rolling_covariance(x_values, y_values, window=3, min_periods=2, ddof=1)
    assert result[-1] == pytest.approx(expected, abs=1e-12)


def test_rolling_covariance_respects_ddof() -> None:
    population = rolling_covariance([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], window=2, min_periods=2, ddof=0)
    sample = rolling_covariance([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], window=2, min_periods=2, ddof=1)

    assert population == pytest.approx([None, 0.25, 0.25], abs=1e-12)
    assert sample == pytest.approx([None, 0.5, 0.5], abs=1e-12)


def test_rolling_covariance_empty_and_single_observation_behavior_is_explicit() -> None:
    assert rolling_covariance([], [], window=2, min_periods=1, ddof=1) == []
    assert rolling_covariance([1.0], [2.0], window=2, min_periods=1, ddof=1) == [None]


def test_rolling_covariance_is_deterministic_and_does_not_mutate_inputs() -> None:
    x_values = [1.0, 2.0, 3.0, 10.0]
    y_values = [1.0, 2.0, 3.0, 10.0]
    original_x = copy.deepcopy(x_values)
    original_y = copy.deepcopy(y_values)

    first = rolling_covariance(x_values, y_values, window=3, min_periods=2, ddof=1)
    second = rolling_covariance(x_values, y_values, window=3, min_periods=2, ddof=1)

    assert x_values == original_x
    assert y_values == original_y
    assert first == second


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"window": 0, "min_periods": 1, "ddof": 1}, "window must be a positive integer."),
        ({"window": 2, "min_periods": 0, "ddof": 1}, "min_periods must be a positive integer."),
        ({"window": 2, "min_periods": 3, "ddof": 1}, "min_periods must be less than or equal to window."),
        ({"window": 2, "min_periods": 1, "ddof": -1}, "ddof must be a non-negative integer."),
        ({"window": 2, "min_periods": 1, "ddof": 2}, "ddof must be smaller than window."),
    ],
)
def test_rolling_covariance_rejects_invalid_configuration(kwargs: dict[str, int], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        rolling_covariance([1.0, 2.0], [1.0, 2.0], **kwargs)


@pytest.mark.parametrize(
    ("x_values", "y_values", "message"),
    [
        ([1.0, 2.0], [1.0], "Series must have the same length."),
        ([1.0, math.nan], [1.0, 2.0], "x\\[1\\] must not be NaN."),
        ([1.0, math.inf], [1.0, 2.0], "x\\[1\\] must be finite."),
        ([1.0, "bad"], [1.0, 2.0], "x\\[1\\] must be numeric."),
        ([1.0, None], [1.0, 2.0], "x\\[1\\] must be numeric."),
    ],
)
def test_rolling_covariance_rejects_invalid_series_values(
    x_values: list[object],
    y_values: list[object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        rolling_covariance(x_values, y_values, window=2, min_periods=1, ddof=1)  # type: ignore[arg-type]


def test_rolling_correlation_warmup_sliding_and_constant_window_behavior() -> None:
    positive = rolling_correlation([1.0, 2.0, 3.0, 10.0], [1.0, 2.0, 3.0, 10.0], window=3, min_periods=2)
    constant = rolling_correlation([1.0, 1.0, 1.0], [2.0, 4.0, 6.0], window=3, min_periods=2)

    assert positive == pytest.approx([None, 1.0, 1.0, 1.0], abs=1e-12)
    assert constant == [None, None, None]


@pytest.mark.parametrize(
    ("x_values", "y_values", "expected"),
    [
        ([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], 1.0),
        ([1.0, 2.0, 3.0], [3.0, 2.0, 1.0], -1.0),
        ([-1.0, 0.0, 1.0], [1.0, -2.0, 1.0], 0.0),
    ],
)
def test_rolling_correlation_handles_positive_negative_and_zero_relationships(
    x_values: list[float],
    y_values: list[float],
    expected: float,
) -> None:
    result = rolling_correlation(x_values, y_values, window=3, min_periods=2)
    assert result[-1] == pytest.approx(expected, abs=1e-12)


def test_rolling_correlation_empty_and_single_observation_behavior_is_explicit() -> None:
    assert rolling_correlation([], [], window=2, min_periods=1) == []
    assert rolling_correlation([1.0], [2.0], window=2, min_periods=1) == [None]


def test_rolling_correlation_is_deterministic_and_does_not_mutate_inputs() -> None:
    x_values = [1.0, 2.0, 3.0, 10.0]
    y_values = [1.0, 2.0, 3.0, 10.0]
    original_x = copy.deepcopy(x_values)
    original_y = copy.deepcopy(y_values)

    first = rolling_correlation(x_values, y_values, window=3, min_periods=2)
    second = rolling_correlation(x_values, y_values, window=3, min_periods=2)

    assert x_values == original_x
    assert y_values == original_y
    assert first == second


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"window": 0, "min_periods": 1}, "window must be a positive integer."),
        ({"window": 2, "min_periods": 0}, "min_periods must be a positive integer."),
        ({"window": 2, "min_periods": 3}, "min_periods must be less than or equal to window."),
    ],
)
def test_rolling_correlation_rejects_invalid_configuration(kwargs: dict[str, int], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        rolling_correlation([1.0, 2.0], [1.0, 2.0], **kwargs)


@pytest.mark.parametrize(
    ("x_values", "y_values", "message"),
    [
        ([1.0, 2.0], [1.0], "Series must have the same length."),
        ([1.0, math.nan], [1.0, 2.0], "x\\[1\\] must not be NaN."),
        ([1.0, math.inf], [1.0, 2.0], "x\\[1\\] must be finite."),
        ([1.0, "bad"], [1.0, 2.0], "x\\[1\\] must be numeric."),
    ],
)
def test_rolling_correlation_rejects_invalid_series_values(
    x_values: list[object],
    y_values: list[object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        rolling_correlation(x_values, y_values, window=2, min_periods=1)  # type: ignore[arg-type]


def test_ewma_covariance_returns_hand_verifiable_values() -> None:
    result = ewma_covariance([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], alpha=0.5, min_periods=2)

    assert result[0] is None
    assert result[1] == pytest.approx(2.0 / 9.0, abs=1e-12)
    assert result[2] == pytest.approx(182.0 / 343.0, abs=1e-12)


def test_ewma_covariance_favors_recent_observations() -> None:
    higher_alpha = ewma_covariance([10.0, 0.0, 0.0], [10.0, 0.0, 0.0], alpha=0.8, min_periods=2)
    lower_alpha = ewma_covariance([10.0, 0.0, 0.0], [10.0, 0.0, 0.0], alpha=0.2, min_periods=2)

    assert higher_alpha[-1] is not None
    assert lower_alpha[-1] is not None
    assert higher_alpha[-1] < lower_alpha[-1]


@pytest.mark.parametrize(
    ("x_values", "y_values", "expected"),
    [
        ([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], 182.0 / 343.0),
        ([1.0, 2.0, 3.0], [3.0, 2.0, 1.0], -(182.0 / 343.0)),
        ([5.0, 5.0, 5.0], [1.0, 2.0, 3.0], 0.0),
    ],
)
def test_ewma_covariance_handles_positive_negative_and_constant_relationships(
    x_values: list[float],
    y_values: list[float],
    expected: float,
) -> None:
    result = ewma_covariance(x_values, y_values, alpha=0.5, min_periods=2)
    assert result[-1] == pytest.approx(expected, abs=1e-12)


def test_ewma_covariance_empty_and_single_observation_behavior_is_explicit() -> None:
    assert ewma_covariance([], [], alpha=0.5, min_periods=1) == []
    assert ewma_covariance([1.0], [2.0], alpha=0.5, min_periods=1) == [None]


def test_ewma_covariance_is_deterministic_and_does_not_mutate_inputs() -> None:
    x_values = [1.0, 2.0, 3.0]
    y_values = [1.0, 2.0, 3.0]
    original_x = copy.deepcopy(x_values)
    original_y = copy.deepcopy(y_values)

    first = ewma_covariance(x_values, y_values, alpha=0.5, min_periods=2)
    second = ewma_covariance(x_values, y_values, alpha=0.5, min_periods=2)

    assert x_values == original_x
    assert y_values == original_y
    assert first == second


@pytest.mark.parametrize(
    ("alpha", "message"),
    [
        (0.0, "alpha must be greater than 0 and less than or equal to 1."),
        (-0.1, "alpha must be greater than 0 and less than or equal to 1."),
        (1.1, "alpha must be greater than 0 and less than or equal to 1."),
        (math.nan, "alpha must not be NaN."),
        (math.inf, "alpha must be finite."),
    ],
)
def test_ewma_covariance_rejects_invalid_alpha(alpha: float, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        ewma_covariance([1.0, 2.0], [1.0, 2.0], alpha=alpha, min_periods=1)


def test_ewma_covariance_rejects_invalid_minimum_periods() -> None:
    with pytest.raises(ValueError, match="min_periods must be a positive integer."):
        ewma_covariance([1.0, 2.0], [1.0, 2.0], alpha=0.5, min_periods=0)


@pytest.mark.parametrize(
    ("x_values", "y_values", "message"),
    [
        ([1.0, 2.0], [1.0], "Series must have the same length."),
        ([1.0, math.nan], [1.0, 2.0], "x\\[1\\] must not be NaN."),
        ([1.0, math.inf], [1.0, 2.0], "x\\[1\\] must be finite."),
        ([1.0, "bad"], [1.0, 2.0], "x\\[1\\] must be numeric."),
    ],
)
def test_ewma_covariance_rejects_invalid_series_values(
    x_values: list[object],
    y_values: list[object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        ewma_covariance(x_values, y_values, alpha=0.5, min_periods=1)  # type: ignore[arg-type]


def test_ewma_correlation_derives_cleanly_from_ewma_covariance() -> None:
    positive = ewma_correlation([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], alpha=0.5, min_periods=2)
    negative = ewma_correlation([1.0, 2.0, 3.0], [3.0, 2.0, 1.0], alpha=0.5, min_periods=2)
    constant = ewma_correlation([1.0, 1.0, 1.0], [2.0, 4.0, 6.0], alpha=0.5, min_periods=2)

    assert positive == pytest.approx([None, 1.0, 1.0], abs=1e-12)
    assert negative == pytest.approx([None, -1.0, -1.0], abs=1e-12)
    assert constant == [None, None, None]


@pytest.mark.parametrize(
    ("alpha", "message"),
    [
        (0.0, "alpha must be greater than 0 and less than or equal to 1."),
        (math.nan, "alpha must not be NaN."),
    ],
)
def test_ewma_correlation_rejects_invalid_alpha(alpha: float, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        ewma_correlation([1.0, 2.0], [1.0, 2.0], alpha=alpha, min_periods=1)


def test_point_in_time_covariance_excludes_post_cutoff_mutations() -> None:
    timestamps = [
        "2024-01-01T00:00:00Z",
        "2024-01-02T00:00:00Z",
        "2024-01-03T00:00:00Z",
        "2024-01-04T00:00:00Z",
    ]
    first = reconstruct_point_in_time_covariance(
        [1.0, 2.0, 3.0, 10.0],
        [1.0, 2.0, 3.0, 10.0],
        timestamps,
        cutoff_time="2024-01-03T00:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )
    second = reconstruct_point_in_time_covariance(
        [1.0, 2.0, 3.0, -999.0],
        [1.0, 2.0, 3.0, 999.0],
        timestamps,
        cutoff_time="2024-01-03T00:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )

    assert first["status"] == "ready"
    assert first["value"] == pytest.approx(1.0, abs=1e-12)
    assert second["value"] == pytest.approx(first["value"], abs=1e-12)


def test_point_in_time_covariance_excludes_future_additions() -> None:
    baseline = reconstruct_point_in_time_covariance(
        [1.0, 2.0, 3.0, 10.0],
        [1.0, 2.0, 3.0, 10.0],
        [
            "2024-01-01T00:00:00Z",
            "2024-01-02T00:00:00Z",
            "2024-01-03T00:00:00Z",
            "2024-01-04T00:00:00Z",
        ],
        cutoff_time="2024-01-03T00:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )
    extended = reconstruct_point_in_time_covariance(
        [1.0, 2.0, 3.0, 10.0, 200.0],
        [1.0, 2.0, 3.0, 10.0, 200.0],
        [
            "2024-01-01T00:00:00Z",
            "2024-01-02T00:00:00Z",
            "2024-01-03T00:00:00Z",
            "2024-01-04T00:00:00Z",
            "2024-01-05T00:00:00Z",
        ],
        cutoff_time="2024-01-03T00:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )

    assert extended["value"] == pytest.approx(baseline["value"], abs=1e-12)
    assert extended["excluded_future_observation_count"] == 2


def test_point_in_time_covariance_reports_insufficient_history_before_minimum_observations() -> None:
    result = reconstruct_point_in_time_covariance(
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0],
        [
            "2024-01-01T00:00:00Z",
            "2024-01-02T00:00:00Z",
            "2024-01-03T00:00:00Z",
        ],
        cutoff_time="2024-01-01T00:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )

    assert result["ok"] is False
    assert result["status"] == "insufficient_history"
    assert result["value"] is None
    assert result["included_observation_count"] == 1


def test_point_in_time_covariance_reports_insufficient_history_before_first_observation() -> None:
    result = reconstruct_point_in_time_covariance(
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0],
        [
            "2024-01-01T00:00:00Z",
            "2024-01-02T00:00:00Z",
            "2024-01-03T00:00:00Z",
        ],
        cutoff_time="2023-12-31T23:59:59Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )

    assert result["ok"] is False
    assert result["status"] == "insufficient_history"
    assert result["value"] is None
    assert result["included_observation_count"] == 0
    assert result["excluded_future_observation_count"] == 3


def test_point_in_time_covariance_reconstruction_is_repeatedly_deterministic() -> None:
    kwargs = {
        "x": [1.0, 2.0, 3.0, 10.0],
        "y": [1.0, 2.0, 3.0, 10.0],
        "observation_timestamps": [
            "2024-01-01T00:00:00Z",
            "2024-01-02T00:00:00Z",
            "2024-01-03T00:00:00Z",
            "2024-01-04T00:00:00Z",
        ],
        "cutoff_time": "2024-01-03T00:00:00Z",
        "estimator": "ewma",
        "alpha": 0.5,
        "min_periods": 2,
    }

    assert reconstruct_point_in_time_covariance(**kwargs) == reconstruct_point_in_time_covariance(**kwargs)


def test_point_in_time_covariance_includes_cutoff_observation_and_excludes_later_observation() -> None:
    exact_cutoff = reconstruct_point_in_time_covariance(
        [1.0, 2.0, 3.0, 10.0],
        [1.0, 2.0, 3.0, 10.0],
        [
            "2024-01-01T00:00:00Z",
            "2024-01-02T00:00:00Z",
            "2024-01-03T00:00:00Z",
            "2024-01-04T00:00:00Z",
        ],
        cutoff_time="2024-01-03T00:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )
    between_observations = reconstruct_point_in_time_covariance(
        [1.0, 2.0, 3.0, 10.0],
        [1.0, 2.0, 3.0, 10.0],
        [
            "2024-01-01T00:00:00Z",
            "2024-01-02T00:00:00Z",
            "2024-01-03T00:00:00Z",
            "2024-01-04T00:00:00Z",
        ],
        cutoff_time="2024-01-03T12:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )

    assert exact_cutoff["included_observation_count"] == 3
    assert exact_cutoff["value"] == pytest.approx(1.0, abs=1e-12)
    assert between_observations["included_observation_count"] == 3
    assert between_observations["value"] == pytest.approx(1.0, abs=1e-12)


def test_point_in_time_rolling_and_ewma_reconstruction_match_filtered_series() -> None:
    timestamps = [
        "2024-01-01T00:00:00Z",
        "2024-01-02T00:00:00Z",
        "2024-01-03T00:00:00Z",
        "2024-01-04T00:00:00Z",
    ]
    rolling_result = reconstruct_point_in_time_covariance(
        [1.0, 2.0, 3.0, 10.0],
        [1.0, 2.0, 3.0, 10.0],
        timestamps,
        cutoff_time="2024-01-03T00:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )
    ewma_result = reconstruct_point_in_time_covariance(
        [1.0, 2.0, 3.0, 10.0],
        [1.0, 2.0, 3.0, 10.0],
        timestamps,
        cutoff_time="2024-01-03T00:00:00Z",
        estimator="ewma",
        alpha=0.5,
        min_periods=2,
    )

    assert rolling_result["value"] == pytest.approx(
        rolling_covariance([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], window=3, min_periods=2, ddof=1)[-1],
        abs=1e-12,
    )
    assert ewma_result["value"] == pytest.approx(
        ewma_covariance([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], alpha=0.5, min_periods=2)[-1],
        abs=1e-12,
    )


def test_point_in_time_correlation_supports_rolling_and_ewma_without_look_ahead() -> None:
    timestamps = [
        "2024-01-01T00:00:00Z",
        "2024-01-02T00:00:00Z",
        "2024-01-03T00:00:00Z",
        "2024-01-04T00:00:00Z",
    ]
    rolling_result = reconstruct_point_in_time_correlation(
        [1.0, 2.0, 3.0, 10.0],
        [1.0, 2.0, 3.0, 10.0],
        timestamps,
        cutoff_time="2024-01-03T12:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
    )
    ewma_result = reconstruct_point_in_time_correlation(
        [1.0, 2.0, 3.0, -10.0],
        [1.0, 2.0, 3.0, -10.0],
        timestamps,
        cutoff_time="2024-01-03T12:00:00Z",
        estimator="ewma",
        alpha=0.5,
        min_periods=2,
    )

    assert rolling_result["value"] == pytest.approx(1.0, abs=1e-12)
    assert ewma_result["value"] == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {
                "x": [1.0, 2.0],
                "y": [1.0],
                "observation_timestamps": ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"],
                "cutoff_time": "2024-01-02T00:00:00Z",
                "estimator": "rolling",
                "window": 2,
                "min_periods": 1,
                "ddof": 1,
            },
            "Series must have the same length.",
        ),
        (
            {
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
                "observation_timestamps": ["2024-01-02T00:00:00Z", "2024-01-01T00:00:00Z"],
                "cutoff_time": "2024-01-02T00:00:00Z",
                "estimator": "rolling",
                "window": 2,
                "min_periods": 1,
                "ddof": 1,
            },
            "observation_timestamps must be ordered ascending without internal resorting.",
        ),
        (
            {
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
                "observation_timestamps": ["2024-01-01T00:00:00Z"],
                "cutoff_time": "2024-01-02T00:00:00Z",
                "estimator": "rolling",
                "window": 2,
                "min_periods": 1,
                "ddof": 1,
            },
            "observation_timestamps must have the same length as the observation series.",
        ),
        (
            {
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
                "observation_timestamps": ["not-a-time", "2024-01-02T00:00:00Z"],
                "cutoff_time": "2024-01-02T00:00:00Z",
                "estimator": "rolling",
                "window": 2,
                "min_periods": 1,
                "ddof": 1,
            },
            "observation_timestamps\\[0\\] must be a valid ISO-8601 timestamp.",
        ),
        (
            {
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
                "observation_timestamps": ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"],
                "cutoff_time": "not-a-time",
                "estimator": "rolling",
                "window": 2,
                "min_periods": 1,
                "ddof": 1,
            },
            "cutoff_time must be a valid ISO-8601 timestamp.",
        ),
        (
            {
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
                "observation_timestamps": ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"],
                "cutoff_time": "2024-01-02T00:00:00Z",
                "estimator": "invalid",
                "window": 2,
                "min_periods": 1,
                "ddof": 1,
            },
            "estimator must be 'rolling' or 'ewma'.",
        ),
        (
            {
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
                "observation_timestamps": ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"],
                "cutoff_time": "2024-01-02T00:00:00Z",
                "estimator": "rolling",
                "window": None,
                "min_periods": 1,
                "ddof": 1,
            },
            "window is required for rolling point-in-time covariance.",
        ),
        (
            {
                "x": [1.0, 2.0],
                "y": [1.0, 2.0],
                "observation_timestamps": ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"],
                "cutoff_time": "2024-01-02T00:00:00Z",
                "estimator": "ewma",
                "window": None,
                "min_periods": 1,
                "ddof": 1,
                "alpha": None,
            },
            "alpha is required for EWMA point-in-time covariance.",
        ),
    ],
)
def test_point_in_time_covariance_rejects_invalid_inputs(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        reconstruct_point_in_time_covariance(**kwargs)
