from __future__ import annotations

import copy
import math

import pytest

from src.backtesting import reconstruct_point_in_time_covariance_matrix
from src.core.math_utils import (
    correlation,
    correlation_matrix,
    covariance,
    covariance_matrix,
    portfolio_variance,
)
from src.core.portfolio import (
    component_contribution_to_risk,
    concentration_score,
    correlated_exposure,
    exposure_weights,
    incremental_portfolio_risk,
    marginal_contribution_to_risk,
    portfolio_exposure,
    portfolio_risk_summary,
    portfolio_summary,
    portfolio_volatility,
    position_concentration,
)
from src.core.risk import portfolio_risk


def test_static_covariance_and_portfolio_regressions_remain_unchanged() -> None:
    matrix = covariance_matrix([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]])

    assert covariance([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) == pytest.approx(1.0, abs=1e-12)
    assert correlation([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) == pytest.approx(1.0, abs=1e-12)
    assert matrix[0] == pytest.approx([1.0, -1.0], abs=1e-12)
    assert matrix[1] == pytest.approx([-1.0, 1.0], abs=1e-12)
    assert correlation_matrix([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]])[0][1] == pytest.approx(-1.0, abs=1e-12)
    assert portfolio_variance([0.75, 0.25], matrix) == pytest.approx(0.25, abs=1e-12)
    assert portfolio_risk([0.75, 0.25], matrix) == pytest.approx(0.5, abs=1e-12)
    assert correlated_exposure([0.75, 0.25], matrix) == pytest.approx(0.25, abs=1e-6)


def test_portfolio_exposure_tracks_gross_net_weights_concentration_and_order() -> None:
    positions = {"A": 100.0, "B": {"exposure": -50.0}, "C": {"stake": 50.0}}
    original = copy.deepcopy(positions)

    result = portfolio_exposure(positions)

    assert positions == original
    assert result["ordered_position_ids"] == ["A", "B", "C"]
    assert result["gross_exposure"] == pytest.approx(200.0, abs=1e-12)
    assert result["net_exposure"] == pytest.approx(100.0, abs=1e-12)
    assert result["weights"] == pytest.approx({"A": 0.5, "B": 0.25, "C": 0.25}, abs=1e-12)
    assert result["risk_weights"] == pytest.approx({"A": 1.0, "B": -0.5, "C": 0.5}, abs=1e-12)
    assert result["concentration_score"] == pytest.approx(0.5, abs=1e-12)
    assert position_concentration(positions) == pytest.approx({"A": 0.5, "B": 0.25, "C": 0.25}, abs=1e-12)


@pytest.mark.parametrize(
    ("positions", "expected_score"),
    [
        ({"A": 100.0}, 1.0),
        ({"A": 100.0, "B": 100.0}, 0.5),
        ({"A": 900.0, "B": 100.0}, 0.9),
        ({"A": 0.0, "B": 0.0}, 0.0),
        ({"A": -100.0, "B": 50.0}, 2.0 / 3.0),
    ],
)
def test_concentration_uses_maximum_gross_exposure_weight(
    positions: dict[str, float],
    expected_score: float,
) -> None:
    assert portfolio_exposure(positions)["concentration_score"] == pytest.approx(expected_score, abs=1e-12)


def test_legacy_portfolio_summary_and_weight_helpers_remain_compatible() -> None:
    positions = {"A": 100.0, "B": {"exposure": 200.0}}

    assert exposure_weights(positions) == pytest.approx({"A": 1.0 / 3.0, "B": 2.0 / 3.0}, abs=1e-12)
    assert concentration_score(positions) == pytest.approx(2.0 / 3.0, abs=1e-12)
    assert portfolio_summary(positions)["total_exposure"] == pytest.approx(300.0, abs=1e-12)


@pytest.mark.parametrize(
    ("positions", "message"),
    [
        ({"A": math.nan}, "positions\\['A'\\] must not be NaN."),
        ({"A": math.inf}, "positions\\['A'\\] must be finite."),
        ({"A": "bad"}, "positions\\['A'\\] must be numeric."),
        ({"A": None}, "positions\\['A'\\] must be numeric."),
        ({"A": {"foo": 1.0}}, "positions\\['A'\\] must contain exposure or stake."),
        ({"": 1.0}, "Position identifiers must be non-empty strings."),
    ],
)
def test_portfolio_exposure_rejects_invalid_inputs(positions: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        portfolio_exposure(positions)


@pytest.mark.parametrize(
    ("positions", "matrix", "expected_volatility"),
    [
        ({"A": 100.0}, [[0.04]], 0.2),
        ({"A": 100.0, "B": 100.0}, [[0.04, 0.0], [0.0, 0.09]], math.sqrt(0.0325)),
        ({"A": 100.0, "B": 100.0}, [[0.04, 0.03], [0.03, 0.09]], math.sqrt(0.0475)),
        ({"A": 100.0, "B": 100.0}, [[0.04, -0.03], [-0.03, 0.09]], math.sqrt(0.0175)),
        ({"A": 100.0, "B": 100.0}, [[0.04, 0.06], [0.06, 0.09]], 0.25),
        ({"A": 100.0, "B": 100.0}, [[0.0, 0.0], [0.0, 0.09]], 0.15),
    ],
)
def test_portfolio_risk_summary_handles_covariance_relationships(
    positions: dict[str, float],
    matrix: list[list[float]],
    expected_volatility: float,
) -> None:
    result = portfolio_risk_summary(positions, matrix)

    assert result["portfolio_volatility"] == pytest.approx(expected_volatility, abs=1e-12)
    assert result["portfolio_variance"] == pytest.approx(expected_volatility**2, abs=1e-12)


def test_portfolio_risk_summary_is_deterministic_and_uses_stable_ordering() -> None:
    positions = {"B": 200.0, "A": 100.0}
    matrix = [[0.09, 0.0], [0.0, 0.04]]

    first = portfolio_risk_summary(positions, matrix)
    second = portfolio_risk_summary(positions, matrix)

    assert first == second
    assert first["ordered_position_ids"] == ["B", "A"]
    assert first["risk_weight_vector"] == pytest.approx([2.0 / 3.0, 1.0 / 3.0], abs=1e-12)


def test_portfolio_risk_summary_handles_zero_exposure_explicitly() -> None:
    result = portfolio_risk_summary({"A": 0.0, "B": 0.0}, [[0.04, 0.0], [0.0, 0.09]])

    assert result["gross_exposure"] == 0.0
    assert result["net_exposure"] == 0.0
    assert result["portfolio_variance"] == 0.0
    assert result["portfolio_volatility"] == 0.0
    assert result["component_contribution_to_risk"] == {}


def test_portfolio_risk_summary_rejects_nonzero_gross_with_zero_net_exposure() -> None:
    with pytest.raises(ValueError, match="Portfolio risk weights are undefined when net exposure is zero."):
        portfolio_risk_summary({"A": 100.0, "B": -100.0}, [[0.04, 0.0], [0.0, 0.09]])


@pytest.mark.parametrize(
    ("matrix", "message"),
    [
        ([[0.04]], "covariance_matrix dimension must match position count."),
        ([[0.04, 0.01], [0.01]], "covariance_matrix must be square."),
        ([[0.04, 0.01], [0.02, 0.09]], "covariance_matrix must be symmetric."),
        ([[-0.04, 0.0], [0.0, 0.09]], "covariance_matrix diagonal entries must be non-negative."),
        ([[0.04, math.nan], [math.nan, 0.09]], "covariance_matrix\\[0\\]\\[1\\] must not be NaN."),
        ([[0.04, math.inf], [math.inf, 0.09]], "covariance_matrix\\[0\\]\\[1\\] must be finite."),
    ],
)
def test_portfolio_risk_summary_rejects_invalid_covariance_matrix(
    matrix: list[list[float]],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        portfolio_risk_summary({"A": 100.0, "B": 100.0}, matrix)


def test_portfolio_volatility_uses_canonical_portfolio_variance() -> None:
    matrix = [[0.04, 0.0], [0.0, 0.09]]

    assert portfolio_volatility([0.5, 0.5], matrix) == pytest.approx(
        math.sqrt(portfolio_variance([0.5, 0.5], matrix)),
        abs=1e-12,
    )


def test_marginal_contribution_to_risk_matches_hand_calculation() -> None:
    weights = [0.5, 0.5]
    matrix = [[0.04, 0.0], [0.0, 0.09]]
    volatility = math.sqrt(0.0325)

    result = marginal_contribution_to_risk(weights, matrix)

    assert result == pytest.approx([0.02 / volatility, 0.045 / volatility], abs=1e-12)


def test_marginal_contribution_to_risk_handles_zero_volatility() -> None:
    assert marginal_contribution_to_risk([1.0], [[0.0]]) == [0.0]


def test_component_contribution_to_risk_reconciles_to_total_risk() -> None:
    weights = [0.5, 0.5]
    matrix = [[0.04, 0.0], [0.0, 0.09]]
    expected_volatility = portfolio_volatility(weights, matrix)

    components = component_contribution_to_risk(weights, matrix)
    summary = portfolio_risk_summary({"A": 100.0, "B": 100.0}, matrix)

    assert math.fsum(components) == pytest.approx(expected_volatility, abs=1e-12)
    assert summary["component_contribution_sum"] == pytest.approx(summary["portfolio_volatility"], abs=1e-12)
    assert summary["component_contribution_tolerance"] == 1e-12


def test_component_contribution_to_risk_preserves_position_order() -> None:
    summary = portfolio_risk_summary({"B": 200.0, "A": 100.0}, [[0.09, 0.0], [0.0, 0.04]])

    assert list(summary["component_contribution_to_risk"].keys()) == ["B", "A"]
    assert list(summary["marginal_contribution_to_risk"].keys()) == ["B", "A"]


def test_incremental_risk_increases_for_highly_positive_addition() -> None:
    result = incremental_portfolio_risk(
        {"A": 100.0},
        "B",
        100.0,
        [[0.04, 0.08], [0.08, 0.25]],
    )

    assert result["current_portfolio_risk"] == pytest.approx(0.2, abs=1e-12)
    assert result["proposed_portfolio_risk"] == pytest.approx(math.sqrt(0.1125), abs=1e-12)
    assert result["absolute_change"] > 0.0
    assert result["relative_change"] == pytest.approx((math.sqrt(0.1125) - 0.2) / 0.2, abs=1e-12)
    assert result["concentration_change"] == pytest.approx(-0.5, abs=1e-12)
    assert result["increases_concentration"] is False
    assert result["result"] == "risk_increased"


def test_incremental_risk_detects_covariance_driven_diversification() -> None:
    result = incremental_portfolio_risk(
        {"A": 100.0},
        "B",
        100.0,
        [[0.04, -0.04], [-0.04, 0.04]],
    )

    assert result["current"]["gross_exposure"] == pytest.approx(100.0, abs=1e-12)
    assert result["proposed"]["gross_exposure"] == pytest.approx(200.0, abs=1e-12)
    assert result["current_portfolio_risk"] == pytest.approx(0.2, abs=1e-12)
    assert result["proposed_portfolio_risk"] == pytest.approx(0.0, abs=1e-12)
    assert result["absolute_change"] == pytest.approx(-0.2, abs=1e-12)
    assert result["concentration_change"] == pytest.approx(-0.5, abs=1e-12)
    assert result["diversifies"] is True
    assert result["result"] == "risk_reduced"


def test_incremental_risk_handles_independent_addition() -> None:
    result = incremental_portfolio_risk(
        {"A": 100.0},
        "B",
        100.0,
        [[0.04, 0.0], [0.0, 0.04]],
    )

    assert result["proposed_portfolio_risk"] == pytest.approx(math.sqrt(0.02), abs=1e-12)
    assert result["result"] == "risk_reduced"


def test_incremental_risk_handles_zero_risk_addition() -> None:
    result = incremental_portfolio_risk(
        {"A": 100.0},
        "B",
        100.0,
        [[0.04, 0.0], [0.0, 0.0]],
    )

    assert result["proposed_portfolio_risk"] == pytest.approx(0.1, abs=1e-12)
    assert result["absolute_change"] == pytest.approx(-0.1, abs=1e-12)


def test_incremental_risk_handles_zero_size_addition_without_changing_risk() -> None:
    result = incremental_portfolio_risk(
        {"A": 100.0, "B": 100.0},
        "C",
        0.0,
        [[0.04, 0.0, 0.0], [0.0, 0.04, 0.0], [0.0, 0.0, 0.25]],
    )

    assert result["gross_exposure_change"] == pytest.approx(0.0, abs=1e-12)
    assert result["net_exposure_change"] == pytest.approx(0.0, abs=1e-12)
    assert result["absolute_change"] == pytest.approx(0.0, abs=1e-12)
    assert result["relative_change"] == pytest.approx(0.0, abs=1e-12)
    assert result["concentration_change"] == pytest.approx(0.0, abs=1e-12)
    assert result["result"] == "risk_unchanged"


def test_incremental_risk_reports_concentration_increase() -> None:
    result = incremental_portfolio_risk(
        {"A": 100.0, "B": 100.0},
        "C",
        300.0,
        [[0.04, 0.0, 0.0], [0.0, 0.04, 0.0], [0.0, 0.0, 0.04]],
    )

    assert result["current_concentration"] == pytest.approx(0.5, abs=1e-12)
    assert result["proposed_concentration"] == pytest.approx(0.6, abs=1e-12)
    assert result["concentration_change"] == pytest.approx(0.1, abs=1e-12)
    assert result["increases_concentration"] is True


def test_incremental_risk_supports_first_position_in_empty_portfolio() -> None:
    result = incremental_portfolio_risk({}, "A", 100.0, [[0.04]])

    assert result["current_portfolio_risk"] == 0.0
    assert result["proposed_portfolio_risk"] == pytest.approx(0.2, abs=1e-12)
    assert result["relative_change"] is None
    assert result["result"] == "risk_increased"


def test_incremental_risk_is_deterministic() -> None:
    kwargs = {
        "positions": {"A": 100.0},
        "proposed_position_id": "B",
        "proposed_position": 100.0,
        "covariance_matrix": [[0.04, -0.04], [-0.04, 0.04]],
    }

    assert incremental_portfolio_risk(**kwargs) == incremental_portfolio_risk(**kwargs)


def test_incremental_risk_rejects_duplicate_proposed_position() -> None:
    with pytest.raises(ValueError, match="proposed_position_id must not already exist in positions."):
        incremental_portfolio_risk({"A": 100.0}, "A", 50.0, [[0.04, 0.0], [0.0, 0.09]])


def test_point_in_time_covariance_matrix_composes_with_portfolio_risk() -> None:
    result = reconstruct_point_in_time_covariance_matrix(
        {
            "A": [1.0, 2.0, 3.0, 1000.0],
            "B": [1.0, 2.0, 3.0, -1000.0],
        },
        [
            "2026-01-01T00:00:00Z",
            "2026-01-02T00:00:00Z",
            "2026-01-03T00:00:00Z",
            "2026-01-04T00:00:00Z",
        ],
        cutoff_time="2026-01-03T00:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )

    assert result["ok"] is True
    assert result["ordered_position_ids"] == ["A", "B"]
    assert result["included_observation_count"] == 3
    assert result["excluded_future_observation_count"] == 1
    assert result["matrix"][0] == pytest.approx([1.0, 1.0], abs=1e-12)
    assert result["matrix"][1] == pytest.approx([1.0, 1.0], abs=1e-12)

    risk = portfolio_risk_summary({"A": 100.0, "B": 100.0}, result["matrix"])
    assert risk["portfolio_volatility"] == pytest.approx(1.0, abs=1e-12)


def test_point_in_time_portfolio_risk_is_invariant_to_future_mutation() -> None:
    timestamps = [
        "2026-01-01T00:00:00Z",
        "2026-01-02T00:00:00Z",
        "2026-01-03T00:00:00Z",
        "2026-01-04T00:00:00Z",
    ]
    series = {
        "A": [1.0, 2.0, 3.0, 1000.0],
        "B": [1.0, 2.0, 3.0, -1000.0],
    }
    mutated = {
        "A": [1.0, 2.0, 3.0, -9999.0],
        "B": [1.0, 2.0, 3.0, 9999.0],
    }

    first_matrix = reconstruct_point_in_time_covariance_matrix(
        series,
        timestamps,
        cutoff_time="2026-01-03T00:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )
    second_matrix = reconstruct_point_in_time_covariance_matrix(
        mutated,
        timestamps,
        cutoff_time="2026-01-03T00:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )

    first_risk = portfolio_risk_summary({"A": 100.0, "B": 100.0}, first_matrix["matrix"])
    second_risk = portfolio_risk_summary({"A": 100.0, "B": 100.0}, second_matrix["matrix"])

    assert first_matrix == second_matrix
    assert first_risk["portfolio_volatility"] == second_risk["portfolio_volatility"]


def test_point_in_time_covariance_matrix_supports_exponentially_weighted_estimator() -> None:
    result = reconstruct_point_in_time_covariance_matrix(
        {
            "A": [1.0, 2.0, 3.0, 1000.0],
            "B": [1.0, 2.0, 3.0, -1000.0],
        },
        [
            "2026-01-01T00:00:00Z",
            "2026-01-02T00:00:00Z",
            "2026-01-03T00:00:00Z",
            "2026-01-04T00:00:00Z",
        ],
        cutoff_time="2026-01-03T12:00:00Z",
        estimator="ewma",
        alpha=0.5,
        min_periods=2,
    )

    assert result["ok"] is True
    assert result["ordered_position_ids"] == ["A", "B"]
    assert result["matrix"][0] == pytest.approx([0.5306122448979591, 0.5306122448979591], abs=1e-12)
    assert result["matrix"][1] == pytest.approx([0.5306122448979591, 0.5306122448979591], abs=1e-12)


def test_point_in_time_covariance_matrix_reports_insufficient_history() -> None:
    result = reconstruct_point_in_time_covariance_matrix(
        {"A": [1.0, 2.0, 3.0], "B": [1.0, 2.0, 3.0]},
        [
            "2026-01-01T00:00:00Z",
            "2026-01-02T00:00:00Z",
            "2026-01-03T00:00:00Z",
        ],
        cutoff_time="2026-01-01T12:00:00Z",
        estimator="rolling",
        window=3,
        min_periods=2,
        ddof=1,
    )

    assert result["ok"] is False
    assert result["status"] == "insufficient_history"
    assert result["matrix"] is None
    assert result["included_observation_count"] == 1


def test_point_in_time_covariance_matrix_rejects_unordered_timestamps() -> None:
    with pytest.raises(ValueError, match="observation_timestamps must be ordered ascending without internal resorting."):
        reconstruct_point_in_time_covariance_matrix(
            {"A": [1.0, 2.0], "B": [1.0, 2.0]},
            ["2026-01-02T00:00:00Z", "2026-01-01T00:00:00Z"],
            cutoff_time="2026-01-02T00:00:00Z",
            estimator="rolling",
            window=2,
            min_periods=2,
        )
