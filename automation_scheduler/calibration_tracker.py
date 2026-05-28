from __future__ import annotations

import math
from typing import Any


CALIBRATION_BUCKETS: tuple[tuple[float, float, str], ...] = (
    (0.50, 0.55, "0.50-0.55"),
    (0.55, 0.60, "0.55-0.60"),
    (0.60, 0.65, "0.60-0.65"),
    (0.65, 0.70, "0.65-0.70"),
    (0.70, 0.75, "0.70-0.75"),
    (0.75, 1.01, "0.75+"),
)


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_outcome(value: Any) -> float | None:
    status = str(value).lower()
    if status == "win":
        return 1.0
    if status == "loss":
        return 0.0
    return None


def _bucket_label(probability: float) -> str | None:
    for lower, upper, label in CALIBRATION_BUCKETS:
        if lower <= probability < upper:
            return label
    return None


def bucket_predictions(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, float]]]:
    buckets: dict[str, list[dict[str, float]]] = {label: [] for _, _, label in CALIBRATION_BUCKETS}
    for row in rows:
        p = _to_float(row.get("model_probability"))
        y = _to_outcome(row.get("result_status"))
        if y is None:
            continue
        label = _bucket_label(p)
        if label is None:
            continue
        buckets[label].append({"p": p, "y": y})
    return buckets


def calculate_brier_score(rows: list[dict[str, Any]]) -> float:
    points = []
    for row in rows:
        p = _to_float(row.get("model_probability"))
        y = _to_outcome(row.get("result_status"))
        if y is None:
            continue
        points.append((p - y) ** 2)
    if not points:
        return 0.0
    return round(sum(points) / len(points), 6)


def calculate_log_loss(rows: list[dict[str, Any]], epsilon: float = 1e-15) -> float:
    losses = []
    for row in rows:
        p = _to_float(row.get("model_probability"))
        p = max(epsilon, min(1.0 - epsilon, p))
        y = _to_outcome(row.get("result_status"))
        if y is None:
            continue
        losses.append(-(y * math.log(p) + (1.0 - y) * math.log(1.0 - p)))
    if not losses:
        return 0.0
    return round(sum(losses) / len(losses), 6)


def summarize_calibration_by_bucket(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets = bucket_predictions(rows)
    summary = []
    for _, _, label in CALIBRATION_BUCKETS:
        points = buckets[label]
        count = len(points)
        if count == 0:
            summary.append({"bucket": label, "count": 0, "avg_pred": 0.0, "actual_rate": 0.0, "gap": 0.0})
            continue
        avg_pred = sum(x["p"] for x in points) / count
        actual = sum(x["y"] for x in points) / count
        summary.append(
            {
                "bucket": label,
                "count": count,
                "avg_pred": round(avg_pred, 4),
                "actual_rate": round(actual, 4),
                "gap": round(avg_pred - actual, 4),
            }
        )
    return summary


def calculate_expected_calibration_error(rows: list[dict[str, Any]]) -> float:
    summary = summarize_calibration_by_bucket(rows)
    total = sum(item["count"] for item in summary)
    if total == 0:
        return 0.0
    error = 0.0
    for item in summary:
        if item["count"] == 0:
            continue
        error += (item["count"] / total) * abs(item["avg_pred"] - item["actual_rate"])
    return round(error, 6)


def detect_overconfidence(rows: list[dict[str, Any]], threshold: float = 0.05) -> bool:
    summary = summarize_calibration_by_bucket(rows)
    weighted_gap = 0.0
    weighted_count = 0
    for item in summary:
        if item["count"] == 0:
            continue
        if item["bucket"] in {"0.65-0.70", "0.70-0.75", "0.75+"}:
            gap = item["avg_pred"] - item["actual_rate"]
            weighted_gap += gap * item["count"]
            weighted_count += item["count"]
    if weighted_count == 0:
        return False
    return (weighted_gap / weighted_count) > _to_float(threshold, default=0.05)

