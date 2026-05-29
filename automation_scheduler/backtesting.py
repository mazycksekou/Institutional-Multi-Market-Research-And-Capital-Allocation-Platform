from __future__ import annotations

from typing import Any

from .calibration import calculate_calibration_metrics, summarize_outcome_coverage


def _group_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _reason_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        reason_codes = row.get("reason_codes") if isinstance(row.get("reason_codes"), list) else []
        if not reason_codes:
            reason_codes = [row.get("reason") or "unknown"]
        for reason in reason_codes:
            key = str(reason or "unknown")
            counts[key] = counts.get(key, 0) + 1
    return counts


def run_backtesting_scaffold(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = [row for row in (rows or []) if isinstance(row, dict)]
    coverage = summarize_outcome_coverage(rows)
    if not rows or coverage["settled_count"] == 0:
        return {
            "ok": True,
            "status": "insufficient_data",
            "sample_size": len(rows),
            "settled_count": 0,
            "pending_count": coverage["pending_count"],
            "void_count": coverage["void_count"],
            "coverage_rate": coverage["coverage_rate"],
            "insufficient_data": True,
            "metrics": {},
            "group_counts": {
                "provider": _group_counts(rows, "provider"),
                "market_type": _group_counts(rows, "market_type"),
                "reason": _reason_counts(rows),
            },
            "next_required_data": ["settlement_results"],
        }

    status = "metrics_ready" if coverage["settled_count"] >= len(rows) else "partial_calibration"
    return {
        "ok": True,
        "status": status,
        "sample_size": len(rows),
        "settled_count": coverage["settled_count"],
        "pending_count": coverage["pending_count"],
        "void_count": coverage["void_count"],
        "coverage_rate": coverage["coverage_rate"],
        "insufficient_data": False,
        "metrics": calculate_calibration_metrics(rows),
        "group_counts": {
            "provider": _group_counts(rows, "provider"),
            "market_type": _group_counts(rows, "market_type"),
            "reason": _reason_counts(rows),
        },
        "next_required_data": [] if status == "metrics_ready" else ["additional_settlement_results"],
    }
