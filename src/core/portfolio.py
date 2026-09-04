"""Canonical portfolio helper functions."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from src.core.math_utils import portfolio_variance as _portfolio_variance


FLOAT_TOLERANCE = 1e-12


def _exposure_value(value: Any) -> float:
    if isinstance(value, Mapping):
        if "exposure" in value:
            try:
                return max(0.0, float(value["exposure"]))
            except (TypeError, ValueError):
                return 0.0
        if "stake" in value:
            try:
                return max(0.0, float(value["stake"]))
            except (TypeError, ValueError):
                return 0.0
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 0.0


def _finite_float(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric.")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if math.isnan(numeric):
        raise ValueError(f"{name} must not be NaN.")
    if math.isinf(numeric):
        raise ValueError(f"{name} must be finite.")
    return numeric


def _strict_exposure_value(value: Any, name: str) -> float:
    if isinstance(value, Mapping):
        if "exposure" in value:
            return _finite_float(value["exposure"], f"{name}.exposure")
        if "stake" in value:
            return _finite_float(value["stake"], f"{name}.stake")
        raise ValueError(f"{name} must contain exposure or stake.")
    return _finite_float(value, name)


def _ordered_exposure_items(positions: Mapping[str, Any]) -> list[tuple[str, float]]:
    items: list[tuple[str, float]] = []
    for key, value in positions.items():
        if not isinstance(key, str) or not key:
            raise ValueError("Position identifiers must be non-empty strings.")
        items.append((key, _strict_exposure_value(value, f"positions[{key!r}]")))
    return items


def _validated_weight_vector(weights: Sequence[float]) -> list[float]:
    values = [_finite_float(value, f"weights[{index}]") for index, value in enumerate(weights)]
    if not values:
        raise ValueError("weights must not be empty.")
    return values


def _validated_covariance_matrix(
    covariance_matrix: Sequence[Sequence[float]],
    *,
    expected_size: int,
) -> list[list[float]]:
    rows = [list(row) for row in covariance_matrix]
    if len(rows) != expected_size:
        raise ValueError("covariance_matrix dimension must match position count.")
    matrix: list[list[float]] = []
    for row_index, row in enumerate(rows):
        if len(row) != expected_size:
            raise ValueError("covariance_matrix must be square.")
        matrix.append(
            [
                _finite_float(value, f"covariance_matrix[{row_index}][{column_index}]")
                for column_index, value in enumerate(row)
            ]
        )
    for index in range(expected_size):
        if matrix[index][index] < -FLOAT_TOLERANCE:
            raise ValueError("covariance_matrix diagonal entries must be non-negative.")
        for column_index in range(index + 1, expected_size):
            if not math.isclose(
                matrix[index][column_index],
                matrix[column_index][index],
                rel_tol=0.0,
                abs_tol=FLOAT_TOLERANCE,
            ):
                raise ValueError("covariance_matrix must be symmetric.")
    return matrix


def position_exposure(position: Any, bankroll: float | None = None) -> float:
    exposure = _exposure_value(position)
    if bankroll is None or bankroll <= 0:
        return round(exposure, 6)
    return round(exposure / float(bankroll), 6)


def total_exposure(positions: Mapping[str, Any]) -> float:
    return sum(_exposure_value(value) for value in positions.values())


def exposure_weights(positions: Mapping[str, Any]) -> dict[str, float]:
    exposures = {key: _exposure_value(value) for key, value in positions.items()}
    total = sum(exposures.values())
    if total <= 0:
        return {key: 0.0 for key in positions}
    return {key: exposure / total for key, exposure in exposures.items()}


def concentration_score(positions: Mapping[str, Any]) -> float:
    weights = exposure_weights(positions)
    if not weights:
        return 0.0
    return max(weights.values())


def correlated_exposure(weights: Sequence[float], covariance_matrix: Sequence[Sequence[float]]) -> float:
    return round(_portfolio_variance(list(weights), [list(row) for row in covariance_matrix]), 6)


def portfolio_exposure(positions: Mapping[str, Any]) -> dict[str, Any]:
    """Strict ordered exposure summary for covariance-aware portfolio risk.

    Position order follows the supplied mapping order. Gross weights use
    absolute exposure, while risk weights use signed net exposure when the
    net exposure is non-zero.
    """
    ordered_items = _ordered_exposure_items(positions)
    gross_exposure = math.fsum(abs(amount) for _, amount in ordered_items)
    net_exposure = math.fsum(amount for _, amount in ordered_items)
    gross_weights = {
        key: abs(amount) / gross_exposure if gross_exposure > 0.0 else 0.0
        for key, amount in ordered_items
    }
    risk_weights: dict[str, float | None] = {
        key: amount / net_exposure if not math.isclose(net_exposure, 0.0, rel_tol=0.0, abs_tol=FLOAT_TOLERANCE) else None
        for key, amount in ordered_items
    }
    positions_summary = {
        key: {
            "exposure": amount,
            "gross_exposure": abs(amount),
            "net_exposure": amount,
            "weight": gross_weights[key],
            "gross_weight": gross_weights[key],
            "risk_weight": risk_weights[key],
            "concentration": gross_weights[key],
        }
        for key, amount in ordered_items
    }
    return {
        "ordered_position_ids": [key for key, _ in ordered_items],
        "position_count": len(ordered_items),
        "positions": positions_summary,
        "gross_exposure": gross_exposure,
        "net_exposure": net_exposure,
        "weights": dict(gross_weights),
        "gross_weights": dict(gross_weights),
        "risk_weights": dict(risk_weights),
        "concentration": dict(gross_weights),
        "concentration_score": max(gross_weights.values()) if gross_weights else 0.0,
        "weight_basis": "absolute_gross_exposure",
        "risk_weight_basis": "signed_net_exposure",
    }


def position_concentration(positions: Mapping[str, Any]) -> dict[str, float]:
    """Percentage of gross exposure owned by each position."""
    return dict(portfolio_exposure(positions)["concentration"])


def portfolio_volatility(weights: Sequence[float], covariance_matrix: Sequence[Sequence[float]]) -> float:
    """Portfolio volatility from canonical portfolio variance mathematics."""
    weight_values = _validated_weight_vector(weights)
    matrix = _validated_covariance_matrix(covariance_matrix, expected_size=len(weight_values))
    variance = _portfolio_variance(weight_values, matrix)
    if variance < -FLOAT_TOLERANCE:
        raise ValueError("portfolio variance must not be negative.")
    return math.sqrt(max(0.0, variance))


def marginal_contribution_to_risk(
    weights: Sequence[float],
    covariance_matrix: Sequence[Sequence[float]],
) -> list[float]:
    """Volatility sensitivity for each position per unit portfolio weight."""
    weight_values = _validated_weight_vector(weights)
    matrix = _validated_covariance_matrix(covariance_matrix, expected_size=len(weight_values))
    volatility = portfolio_volatility(weight_values, matrix)
    if math.isclose(volatility, 0.0, rel_tol=0.0, abs_tol=FLOAT_TOLERANCE):
        return [0.0 for _ in weight_values]

    covariance_times_weight = [
        math.fsum(row[column_index] * weight_values[column_index] for column_index in range(len(weight_values)))
        for row in matrix
    ]
    return [value / volatility for value in covariance_times_weight]


def component_contribution_to_risk(
    weights: Sequence[float],
    covariance_matrix: Sequence[Sequence[float]],
) -> list[float]:
    """Position volatility contributions that reconcile to total volatility."""
    weight_values = _validated_weight_vector(weights)
    marginal = marginal_contribution_to_risk(weight_values, covariance_matrix)
    return [weight * marginal_value for weight, marginal_value in zip(weight_values, marginal)]


def _risk_weight_vector(exposure: Mapping[str, Any]) -> list[float]:
    ordered_ids = list(exposure["ordered_position_ids"])
    if not ordered_ids:
        return []
    weights = exposure["risk_weights"]
    if any(weights[position_id] is None for position_id in ordered_ids):
        raise ValueError("Portfolio risk weights are undefined when net exposure is zero.")
    return [float(weights[position_id]) for position_id in ordered_ids]


def portfolio_risk_summary(
    positions: Mapping[str, Any],
    covariance_matrix: Sequence[Sequence[float]],
) -> dict[str, Any]:
    """Covariance-aware portfolio exposure, variance, and risk contribution summary."""
    exposure = portfolio_exposure(positions)
    ordered_ids = list(exposure["ordered_position_ids"])
    matrix = _validated_covariance_matrix(covariance_matrix, expected_size=len(ordered_ids))
    if not ordered_ids or math.isclose(float(exposure["gross_exposure"]), 0.0, rel_tol=0.0, abs_tol=FLOAT_TOLERANCE):
        return {
            **exposure,
            "covariance_matrix": matrix,
            "portfolio_variance": 0.0,
            "portfolio_volatility": 0.0,
            "marginal_contribution_to_risk": {},
            "component_contribution_to_risk": {},
            "component_contribution_pct": {},
            "component_contribution_sum": 0.0,
            "component_contribution_tolerance": FLOAT_TOLERANCE,
        }

    risk_weights = _risk_weight_vector(exposure)
    variance = _portfolio_variance(risk_weights, matrix)
    if variance < -FLOAT_TOLERANCE:
        raise ValueError("portfolio variance must not be negative.")
    volatility = math.sqrt(max(0.0, variance))
    marginal = marginal_contribution_to_risk(risk_weights, matrix)
    component = [weight * marginal_value for weight, marginal_value in zip(risk_weights, marginal)]
    component_sum = math.fsum(component)
    component_pct = {
        position_id: component[index] / volatility
        if not math.isclose(volatility, 0.0, rel_tol=0.0, abs_tol=FLOAT_TOLERANCE)
        else None
        for index, position_id in enumerate(ordered_ids)
    }
    return {
        **exposure,
        "risk_weight_vector": risk_weights,
        "covariance_matrix": matrix,
        "portfolio_variance": variance,
        "portfolio_volatility": volatility,
        "marginal_contribution_to_risk": {
            position_id: marginal[index] for index, position_id in enumerate(ordered_ids)
        },
        "component_contribution_to_risk": {
            position_id: component[index] for index, position_id in enumerate(ordered_ids)
        },
        "component_contribution_pct": component_pct,
        "component_contribution_sum": component_sum,
        "component_contribution_tolerance": FLOAT_TOLERANCE,
    }


def _leading_covariance_submatrix(
    covariance_matrix: Sequence[Sequence[float]],
    *,
    size: int,
) -> list[list[float]]:
    return [list(row[:size]) for row in list(covariance_matrix)[:size]]


def incremental_portfolio_risk(
    positions: Mapping[str, Any],
    proposed_position_id: str,
    proposed_position: Any,
    covariance_matrix: Sequence[Sequence[float]],
) -> dict[str, Any]:
    """Risk change from appending one proposed position to the ordered portfolio."""
    if not isinstance(proposed_position_id, str) or not proposed_position_id:
        raise ValueError("proposed_position_id must be a non-empty string.")
    if proposed_position_id in positions:
        raise ValueError("proposed_position_id must not already exist in positions.")

    current_ids = list(positions.keys())
    proposed_positions = dict(positions)
    proposed_positions[proposed_position_id] = proposed_position
    proposed_ids = list(proposed_positions.keys())

    full_matrix = _validated_covariance_matrix(covariance_matrix, expected_size=len(proposed_ids))
    current_matrix = _leading_covariance_submatrix(full_matrix, size=len(current_ids))
    current_summary = portfolio_risk_summary(positions, current_matrix)
    proposed_summary = portfolio_risk_summary(proposed_positions, full_matrix)

    current_risk = float(current_summary["portfolio_volatility"])
    proposed_risk = float(proposed_summary["portfolio_volatility"])
    absolute_change = proposed_risk - current_risk
    current_concentration = float(current_summary["concentration_score"])
    proposed_concentration = float(proposed_summary["concentration_score"])
    concentration_change = proposed_concentration - current_concentration
    relative_change = None
    if not math.isclose(current_risk, 0.0, rel_tol=0.0, abs_tol=FLOAT_TOLERANCE):
        relative_change = absolute_change / current_risk

    return {
        "ordered_position_ids": proposed_ids,
        "current": current_summary,
        "proposed": proposed_summary,
        "current_portfolio_risk": current_risk,
        "proposed_portfolio_risk": proposed_risk,
        "absolute_change": absolute_change,
        "relative_change": relative_change,
        "gross_exposure_change": float(proposed_summary["gross_exposure"]) - float(current_summary["gross_exposure"]),
        "net_exposure_change": float(proposed_summary["net_exposure"]) - float(current_summary["net_exposure"]),
        "current_concentration": current_concentration,
        "proposed_concentration": proposed_concentration,
        "concentration_change": concentration_change,
        "increases_concentration": proposed_concentration > current_concentration,
        "diversifies": proposed_risk < current_risk,
        "increases_risk": proposed_risk > current_risk,
        "result": "risk_reduced" if proposed_risk < current_risk else ("risk_increased" if proposed_risk > current_risk else "risk_unchanged"),
    }


def portfolio_summary(
    positions: Mapping[str, Any],
    covariance_matrix: Sequence[Sequence[float]] | None = None,
) -> dict[str, Any]:
    weights = exposure_weights(positions)
    summary = {
        "positions": {
            key: {
                "exposure": position_exposure(value),
                "exposure_pct": weights.get(key, 0.0),
            }
            for key, value in positions.items()
        },
        "total_exposure": total_exposure(positions),
        "concentration_score": concentration_score(positions),
    }
    if covariance_matrix is not None:
        summary["correlated_exposure"] = correlated_exposure(
            list(weights.values()),
            covariance_matrix,
        )
    else:
        summary["correlated_exposure"] = 0.0
    return summary


__all__ = [
    "concentration_score",
    "component_contribution_to_risk",
    "correlated_exposure",
    "exposure_weights",
    "incremental_portfolio_risk",
    "marginal_contribution_to_risk",
    "portfolio_exposure",
    "portfolio_risk_summary",
    "portfolio_summary",
    "portfolio_volatility",
    "position_concentration",
    "position_exposure",
    "total_exposure",
]
