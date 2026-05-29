from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def run_calibration_scaffold(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = [row for row in (rows or []) if isinstance(row, dict)]
    labeled: list[tuple[float, float]] = []
    for row in rows:
        pred = _to_float(row.get("implied_probability"))
        actual = _to_float(row.get("final_outcome"))
        if pred is None or actual is None:
            continue
        labeled.append((pred, actual))
    if not labeled:
        return {
            "ok": True,
            "status": "insufficient_data",
            "sample_size": len(rows),
            "settled_count": 0,
            "insufficient_data": True,
            "metrics": {},
        }
    brier = sum((pred - actual) ** 2 for pred, actual in labeled) / len(labeled)
    return {
        "ok": True,
        "status": "computed",
        "sample_size": len(rows),
        "settled_count": len(labeled),
        "insufficient_data": False,
        "metrics": {
            "brier_score": round(brier, 6),
            "calibration_buckets": {},
            "confidence_bucket_performance": {},
            "liquidity_grouping": {},
            "provider_reliability_summary": {},
        },
    }
