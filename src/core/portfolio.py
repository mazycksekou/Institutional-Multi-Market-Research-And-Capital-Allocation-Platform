"""Canonical portfolio helper functions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.core.math_utils import portfolio_variance as _portfolio_variance


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
    "correlated_exposure",
    "exposure_weights",
    "portfolio_summary",
    "position_exposure",
    "total_exposure",
]
