from __future__ import annotations

from collections.abc import Iterable, Mapping
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

