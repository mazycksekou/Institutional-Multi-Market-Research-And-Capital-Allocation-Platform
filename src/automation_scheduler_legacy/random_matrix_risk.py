from __future__ import annotations

import math
from typing import Any

from .security_policy import locked_safety_flags


def _num(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _matrix(payload: Any) -> list[list[float]] | None:
    if not isinstance(payload, list) or not payload:
        return None
    matrix: list[list[float]] = []
    width = None
    for row in payload:
        if not isinstance(row, list) or not row:
            return None
        values = [_num(value) for value in row]
        if any(value is None for value in values):
            return None
        numeric = [float(value) for value in values if value is not None]
        width = width if width is not None else len(numeric)
        if len(numeric) != width:
            return None
        matrix.append(numeric)
    return matrix


def _transpose(matrix: list[list[float]]) -> list[list[float]]:
    return [list(col) for col in zip(*matrix)]


def _covariance_from_returns(matrix: list[list[float]]) -> list[list[float]]:
    rows = matrix
    n = len(rows)
    d = len(rows[0]) if rows else 0
    means = [sum(row[j] for row in rows) / n for j in range(d)]
    out = [[0.0 for _ in range(d)] for _ in range(d)]
    denom = max(1, n - 1)
    for i in range(d):
        for j in range(d):
            out[i][j] = sum((row[i] - means[i]) * (row[j] - means[j]) for row in rows) / denom
    return out


def _correlation_from_returns(matrix: list[list[float]]) -> list[list[float]]:
    cov = _covariance_from_returns(matrix)
    d = len(cov)
    std = [math.sqrt(max(cov[i][i], 0.0)) for i in range(d)]
    corr = [[0.0 for _ in range(d)] for _ in range(d)]
    for i in range(d):
        for j in range(d):
            corr[i][j] = cov[i][j] / (std[i] * std[j]) if std[i] > 0 and std[j] > 0 else (1.0 if i == j else 0.0)
    return corr


def _symmetric_square(matrix: list[list[float]]) -> bool:
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        return False
    for i in range(n):
        for j in range(i + 1, n):
            if abs(matrix[i][j] - matrix[j][i]) > 1e-6:
                return False
    return True


def _mat_vec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(row[j] * vector[j] for j in range(len(vector))) for row in matrix]


def _norm(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def largest_eigenvalue_power_iteration(matrix: list[list[float]], *, iterations: int = 80) -> float | None:
    if not _symmetric_square(matrix):
        return None
    n = len(matrix)
    vector = [1.0 / math.sqrt(n) for _ in range(n)]
    for _ in range(max(1, iterations)):
        next_vector = _mat_vec(matrix, vector)
        norm = _norm(next_vector)
        if norm <= 0:
            return 0.0
        vector = [value / norm for value in next_vector]
    mv = _mat_vec(matrix, vector)
    return round(sum(vector[i] * mv[i] for i in range(n)), 6)


def _bulk_edge(sample_size: int, dimension_count: int, variance_scale: float = 1.0) -> float | None:
    if sample_size <= 0 or dimension_count <= 0:
        return None
    q = dimension_count / sample_size
    return round(float(variance_scale) * (1.0 + math.sqrt(q)) ** 2, 6)


def _condition_status(matrix: list[list[float]], sample_size: int, dimension_count: int) -> str:
    if sample_size < dimension_count:
        return "underdetermined"
    diag = [abs(matrix[i][i]) for i in range(min(len(matrix), len(matrix[0])))]
    if diag and min(diag) <= 1e-12:
        return "singular_or_near_singular"
    if sample_size < dimension_count * 3:
        return "thin_sample"
    return "usable"


def evaluate_random_matrix_risk(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    row = dict(payload or {})
    matrix = None
    matrix_kind = "none"
    if _matrix(row.get("correlation_matrix")) is not None:
        matrix = _matrix(row.get("correlation_matrix"))
        matrix_kind = "correlation_matrix"
    elif _matrix(row.get("covariance_matrix")) is not None:
        matrix = _matrix(row.get("covariance_matrix"))
        matrix_kind = "covariance_matrix"
    elif _matrix(row.get("asset_return_matrix")) is not None:
        returns = _matrix(row.get("asset_return_matrix")) or []
        matrix = _correlation_from_returns(returns)
        matrix_kind = "asset_return_matrix_correlation"
    elif _matrix(row.get("feature_matrix")) is not None:
        features = _matrix(row.get("feature_matrix")) or []
        matrix = _correlation_from_returns(features)
        matrix_kind = "feature_matrix_correlation"

    sample_size = int(_num(row.get("sample_size")) or (len(row.get("asset_return_matrix") or []) if isinstance(row.get("asset_return_matrix"), list) else 0))
    dimension_count = int(_num(row.get("dimension_count")) or (len(matrix) if matrix else 0))
    if matrix is None or not _symmetric_square(matrix) or sample_size <= 1 or dimension_count <= 1:
        result = {
            "rmt_status": "insufficient_matrix_data",
            "dimension_count": dimension_count,
            "sample_size": sample_size,
            "matrix_condition_status": "missing_or_invalid",
            "largest_eigenvalue": None,
            "bulk_edge_estimate": None,
            "largest_eigenvalue_exceeds_random_bulk": False,
            "correlation_shock_score": 0.0,
            "systemwide_noise_risk": "unknown",
            "market_mode_detected": False,
            "idiosyncratic_signal_risk": "unknown",
            "insufficient_matrix_data": True,
            "matrix_kind": matrix_kind,
            "blocked_reason": "missing_or_invalid_matrix_sample_dimension",
        }
        result.update(locked_safety_flags())
        result["provider_write"] = False
        result["execution_allowed"] = False
        result["live_execution_enabled"] = False
        return result

    avg_diag = sum(matrix[i][i] for i in range(dimension_count)) / dimension_count
    variance_scale = 1.0 if matrix_kind.startswith("correlation") or "correlation" in matrix_kind else max(avg_diag, 1e-9)
    largest = largest_eigenvalue_power_iteration(matrix)
    bulk = _bulk_edge(sample_size, dimension_count, variance_scale=variance_scale)
    exceeds = bool(largest is not None and bulk is not None and largest > bulk)
    excess_ratio = 0.0 if not exceeds or not bulk else max(0.0, (float(largest) - bulk) / max(bulk, 1e-9))
    shock_score = round(min(100.0, excess_ratio * 100.0), 2)
    if shock_score >= 50:
        systemwide_noise_risk = "extreme"
    elif shock_score >= 25:
        systemwide_noise_risk = "high"
    elif shock_score >= 10:
        systemwide_noise_risk = "moderate"
    else:
        systemwide_noise_risk = "low"
    result = {
        "rmt_status": "ready",
        "dimension_count": dimension_count,
        "sample_size": sample_size,
        "matrix_condition_status": _condition_status(matrix, sample_size, dimension_count),
        "largest_eigenvalue": largest,
        "bulk_edge_estimate": bulk,
        "largest_eigenvalue_exceeds_random_bulk": exceeds,
        "correlation_shock_score": shock_score,
        "systemwide_noise_risk": systemwide_noise_risk,
        "market_mode_detected": bool(exceeds and shock_score >= 10.0),
        "idiosyncratic_signal_risk": "downgrade_if_claimed_idiosyncratic" if exceeds else "not_elevated",
        "insufficient_matrix_data": False,
        "matrix_kind": matrix_kind,
        "red_team_note": "large_top_eigenvalue_can_indicate_systemwide_noise_not_asset_specific_edge" if exceeds else "top_eigenvalue_within_estimated_random_bulk",
    }
    result.update(locked_safety_flags())
    result["provider_write"] = False
    result["execution_allowed"] = False
    result["live_execution_enabled"] = False
    return result
