"""Sharp-style backtest leakage checks.

The rule is intentionally practical:

- Top-level settlement, PnL, CLV, and closing line fields are allowed because
  backtests need them for grading and learning.
- Those same fields are NOT allowed inside pre-decision model features.
- Ambiguous timing produces warnings, not automatic failure.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .backtest_schema import (
    LEAKAGE_FIELD_ALIASES,
    get_backtest_feature_snapshot,
    missing_required_backtest_fields,
    normalize_backtest_row,
    validate_no_leakage_features,
)


AMBIGUOUS_TIMING_FIELDS: tuple[str, ...] = (
    "closing_line",
    "closing_odds",
    "closing_price",
    "close_price",
    "clv",
    "clv_percent",
    "closing_line_value",
)


REASONABLE_TOP_LEVEL_EVALUATION_FIELDS: tuple[str, ...] = (
    "final_result",
    "result",
    "result_status",
    "outcome",
    "final_outcome",
    "settlement_result",
    "paper_result",
    "profit_loss",
    "pnl",
    "paper_profit_loss",
    "closed_pnl",
    "closing_line",
    "closing_odds",
    "closing_price",
    "clv",
    "clv_percent",
    "closing_line_value",
)


def _present(row: Mapping[str, Any], names: tuple[str, ...]) -> list[str]:
    return [name for name in names if row.get(name) not in (None, "")]


def evaluate_backtest_row_leakage(row: Mapping[str, Any] | None) -> dict[str, Any]:
    """Evaluate one row with a sharp-style no-leakage policy."""

    normalized = normalize_backtest_row(row)
    feature_result = validate_no_leakage_features(normalized)
    missing = missing_required_backtest_fields(normalized)

    warnings: list[str] = []

    top_level_eval_fields = _present(normalized, REASONABLE_TOP_LEVEL_EVALUATION_FIELDS)
    ambiguous_timing_fields = _present(normalized, AMBIGUOUS_TIMING_FIELDS)

    if top_level_eval_fields:
        warnings.append(
            "top_level_evaluation_fields_present_allowed_for_grading"
        )

    if ambiguous_timing_fields and normalized.get("decision_time") in (None, ""):
        warnings.append(
            "closing_or_clv_fields_present_without_decision_time_timing_should_be_verified"
        )

    if normalized.get("features_known_at_decision_time") in (None, ""):
        warnings.append("missing_pre_decision_feature_snapshot")

    if normalized.get("odds_at_decision_time") in (None, "") and normalized.get("recommended_odds") in (None, ""):
        warnings.append("missing_odds_at_decision_time")

    hard_fail_reasons: list[str] = []
    if not feature_result.get("ok"):
        hard_fail_reasons.append("future_or_settlement_fields_inside_pre_decision_features")

    return {
        "ok": not hard_fail_reasons,
        "hard_fail_reasons": hard_fail_reasons,
        "warnings": sorted(set(warnings)),
        "leakage_fields": feature_result.get("leakage_fields", []),
        "missing_required_fields": missing,
        "top_level_evaluation_fields": top_level_eval_fields,
        "ambiguous_timing_fields": ambiguous_timing_fields,
    }


def evaluate_backtest_rows_leakage(rows: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None) -> dict[str, Any]:
    row_results = [evaluate_backtest_row_leakage(row) for row in (rows or [])]

    hard_failed = [idx for idx, result in enumerate(row_results) if not result.get("ok")]
    warning_rows = [idx for idx, result in enumerate(row_results) if result.get("warnings")]

    warning_counts: dict[str, int] = {}
    hard_fail_counts: dict[str, int] = {}

    for result in row_results:
        for warning in result.get("warnings", []):
            warning_counts[warning] = warning_counts.get(warning, 0) + 1
        for reason in result.get("hard_fail_reasons", []):
            hard_fail_counts[reason] = hard_fail_counts.get(reason, 0) + 1

    return {
        "ok": not hard_failed,
        "policy": "sharp_style_reasonable_no_leakage",
        "row_count": len(row_results),
        "hard_failed_rows": hard_failed,
        "warning_rows": warning_rows,
        "hard_fail_counts": hard_fail_counts,
        "warning_counts": warning_counts,
        "row_results": row_results,
    }


def assert_backtest_rows_no_hard_leakage(rows: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None) -> dict[str, Any]:
    report = evaluate_backtest_rows_leakage(rows)
    if not report.get("ok"):
        raise ValueError(f"Backtest leakage hard failure: {report.get('hard_fail_counts')}")
    return report


def summarize_backtest_leakage_report(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(report.get("ok")),
        "policy": report.get("policy"),
        "row_count": report.get("row_count", 0),
        "hard_failed_count": len(report.get("hard_failed_rows", [])),
        "warning_count": len(report.get("warning_rows", [])),
        "hard_fail_counts": dict(report.get("hard_fail_counts", {})),
        "warning_counts": dict(report.get("warning_counts", {})),
    }
