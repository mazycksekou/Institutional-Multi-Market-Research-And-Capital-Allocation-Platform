from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .contracts import CalibrationSummaryContract, GovernanceSummaryContract, ModelEvaluationSummaryContract


def _coerce_texts(values: Iterable[Any] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    cleaned = []
    for value in values:
        text = str(value).strip()
        if text:
            cleaned.append(text)
    return tuple(cleaned)


def _coerce_checks(checks: Mapping[str, Any] | Iterable[tuple[str, Any]] | None) -> tuple[tuple[str, bool], ...]:
    if checks is None:
        return ()
    if isinstance(checks, Mapping):
        items = checks.items()
    else:
        items = checks
    cleaned: list[tuple[str, bool]] = []
    for name, value in items:
        name_text = str(name).strip()
        if not name_text:
            continue
        cleaned.append((name_text, bool(value)))
    return tuple(cleaned)


def summarize_governance(
    *,
    label: str = "governance",
    status: str = "review_required",
    blockers: Iterable[Any] | None = None,
    checks: Mapping[str, Any] | Iterable[tuple[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> GovernanceSummaryContract:
    return GovernanceSummaryContract(
        label=str(label).strip() or "governance",
        status=str(status).strip() or "review_required",
        blockers=_coerce_texts(blockers),
        checks=_coerce_checks(checks),
        metadata=dict(metadata or {}),
    )


def build_calibration_summary(
    *,
    label: str = "calibration",
    sample_count: int = 0,
    calibration_error: float = 0.0,
    calibration_score: float = 1.0,
    buckets: Mapping[str, Any] | Iterable[tuple[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> CalibrationSummaryContract:
    if buckets is None:
        bucket_pairs: tuple[tuple[str, float], ...] = ()
    elif isinstance(buckets, Mapping):
        bucket_pairs = tuple((str(name).strip(), float(value)) for name, value in buckets.items() if str(name).strip())
    else:
        bucket_pairs = tuple((str(name).strip(), float(value)) for name, value in buckets if str(name).strip())

    return CalibrationSummaryContract(
        label=str(label).strip() or "calibration",
        sample_count=max(0, int(sample_count)),
        calibration_error=float(calibration_error),
        calibration_score=float(calibration_score),
        buckets=bucket_pairs,
        metadata=dict(metadata or {}),
    )


def build_model_evaluation_summary(
    model_id: str,
    metrics: Mapping[str, Any] | Iterable[tuple[str, Any]],
    *,
    status: str = "review_required",
    notes: Iterable[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ModelEvaluationSummaryContract:
    if isinstance(metrics, Mapping):
        metric_pairs = tuple((str(name).strip(), float(value)) for name, value in metrics.items() if str(name).strip())
    else:
        metric_pairs = tuple((str(name).strip(), float(value)) for name, value in metrics if str(name).strip())
    return ModelEvaluationSummaryContract(
        model_id=str(model_id).strip() or "unknown_model",
        status=str(status).strip() or "review_required",
        metrics=metric_pairs,
        notes=_coerce_texts(notes),
        metadata=dict(metadata or {}),
    )


def build_governance_health(
    counts: Mapping[str, Any],
    report: Mapping[str, Any],
    *,
    config: Mapping[str, Any] | None = None,
    reports_dir: str | Path = Path("data/performance_reports"),
    audit_dir: str | Path = Path("data/governance_audit"),
    last_governance_report_id: str = "governance_report_v1",
) -> dict[str, Any]:
    count_map = dict(counts)
    report_map = dict(report)
    config_map = dict(config or {})
    reports_path = Path(reports_dir)
    backtest_ready_count = 0
    blocked_by_performance_count = 0
    blocked_by_calibration_count = 0
    if reports_path.exists():
        for report_path in reports_path.glob("*.json"):
            try:
                payload = json.loads(report_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if str(payload.get("performance_status")) == "backtest_complete":
                backtest_ready_count += 1
            blocked_reasons = set(payload.get("blocked_reasons", []))
            if "blocked_by_performance" in blocked_reasons:
                blocked_by_performance_count += 1
            if "blocked_by_calibration" in blocked_reasons:
                blocked_by_calibration_count += 1
    return {
        "governance_status": "ok",
        "inventory_count": int(count_map.get("model_inventory_count", 0)),
        "tier_counts": count_map,
        "audit_log_writable": Path(audit_dir).exists() or Path("data").exists(),
        "blocked_models_count": int(report_map.get("blocked_model_count", 0)),
        "active_scoring_ready_count": int(count_map.get("active_scoring_ready_count", 0)),
        "production_candidate_count": int(count_map.get("production_candidate_count", 0)),
        "human_approval_required": bool(config_map.get("human_approval_required", True)),
        "auto_execution_enabled": bool(config_map.get("auto_execution_enabled", False)),
        "kelly_risk_status_counts": {
            "full_kelly_auto_execution_allowed": 0,
            "review_only": int(count_map.get("model_inventory_count", 0)),
        },
        "last_governance_report_id": str(last_governance_report_id).strip() or "governance_report_v1",
        "backtest_ready_count": backtest_ready_count,
        "blocked_by_performance_count": blocked_by_performance_count,
        "blocked_by_calibration_count": blocked_by_calibration_count,
    }
