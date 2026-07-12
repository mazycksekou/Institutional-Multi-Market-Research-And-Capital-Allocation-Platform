"""Canonical read-only contracts for backtest reports.

This module defines the shape of backtest result summaries that future replay
and reporting phases can populate. It does not execute backtests, compute
metrics, write files, or call external services.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


BACKTEST_REPORT_SCHEMA_VERSION = "src.backtesting.backtest_report_contracts.v1"


def _normalize_text(value: Any, *, field_name: str, allow_empty: bool = False) -> str:
    text = str(value if value is not None else "").strip()
    if not text and not allow_empty:
        raise ValueError(f"{field_name} is required")
    return text


def _normalize_non_negative_int(value: Any, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be a non-negative integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _normalize_float(value: Any, *, field_name: str) -> float:
    if value is None:
        raise TypeError(f"{field_name} is required")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{field_name} must be numeric") from exc


def _normalize_finite_float(value: Any, *, field_name: str) -> float:
    normalized = _normalize_float(value, field_name=field_name)
    if not math.isfinite(normalized):
        raise ValueError(f"{field_name} must be finite")
    return normalized


def _normalize_probability(value: Any, *, field_name: str) -> float:
    normalized = _normalize_finite_float(value, field_name=field_name)
    if not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_non_negative_float(value: Any, *, field_name: str) -> float:
    normalized = _normalize_finite_float(value, field_name=field_name)
    if normalized < 0.0:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _is_repository_dataclass(value: Any) -> bool:
    return is_dataclass(value) and getattr(value.__class__, "__module__", "").startswith("src.")


def _parse_iso_datetime(value: str | None, *, field_name: str) -> datetime | None:
    if value in (None, ""):
        return None
    text = _normalize_text(value, field_name=field_name)
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        return datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601 formatted") from exc


def _json_ready(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if _is_repository_dataclass(value):
        return {str(key): _json_ready(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, set):
        return [_json_ready(item) for item in sorted(value, key=lambda item: repr(item))]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return str(value)


def _normalize_summary_mapping(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return MappingProxyType({})
    if isinstance(value, Mapping):
        payload = _json_ready(dict(value))
    elif _is_repository_dataclass(value):
        payload = _json_ready(asdict(value))
    else:
        raise TypeError(f"{field_name} must be a mapping or mapping-like contract")
    if not isinstance(payload, Mapping):
        raise TypeError(f"{field_name} must be a mapping or mapping-like contract")
    return MappingProxyType(payload)


def _normalize_reference(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, (str, Path)):
        text = str(value).strip()
        if not text:
            return {}
        return {"uri": text}
    raise TypeError(f"{field_name} must be a mapping or string reference")


def _normalize_text_summary(
    value: Any,
    *,
    field_name: str,
) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a string or iterable of strings, not a mapping")
    else:
        try:
            items = list(value)
        except TypeError as exc:
            raise TypeError(f"{field_name} must be a string or iterable of strings") from exc
    cleaned = []
    for item in items:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return tuple(sorted(dict.fromkeys(cleaned)))


def _normalize_count_summary(
    value: Any,
    *,
    field_name: str,
) -> tuple[tuple[str, int], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        items = list(value.items())
    else:
        if isinstance(value, (str, bytes)):
            raise TypeError(f"{field_name} must be a mapping or iterable of pairs")
        items = list(value)

    pairs: list[tuple[str, int]] = []
    seen: set[str] = set()
    for item in items:
        if isinstance(item, Mapping):
            if len(item) != 1:
                raise TypeError(f"{field_name} mapping items must be 2-tuples or single-item mappings")
            name, count = next(iter(item.items()))
        else:
            try:
                name, count = item
            except Exception as exc:
                raise TypeError(f"{field_name} must contain name/count pairs") from exc

        label = _normalize_text(name, field_name=field_name, allow_empty=False)
        if label in seen:
            raise ValueError(f"{field_name} contains duplicate label: {label}")
        seen.add(label)
        pairs.append((label, _normalize_non_negative_int(count, field_name=field_name)))

    return tuple(sorted(pairs, key=lambda pair: pair[0]))


def _normalize_bucket_collection(
    value: Any,
    *,
    field_name: str,
) -> tuple["BacktestPerformanceBucketContract", ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        items = list(value.items())
    else:
        if isinstance(value, (str, bytes)):
            raise TypeError(f"{field_name} must be a mapping or iterable of bucket contracts")
        items = list(value)

    buckets: list[BacktestPerformanceBucketContract] = []
    seen: set[str] = set()
    for item in items:
        if isinstance(item, BacktestPerformanceBucketContract):
            bucket = item
        elif isinstance(item, Mapping):
            bucket = BacktestPerformanceBucketContract.from_dict(item)
        else:
            try:
                label, payload = item
            except Exception as exc:
                raise TypeError(f"{field_name} must contain bucket contracts or name/payload pairs") from exc
            if isinstance(payload, BacktestPerformanceBucketContract):
                if payload.label != _normalize_text(label, field_name=field_name):
                    raise ValueError(f"{field_name} bucket label mismatch: {label}")
                bucket = payload
            elif isinstance(payload, Mapping):
                bucket_payload = dict(payload)
                bucket_payload.setdefault("label", label)
                bucket = BacktestPerformanceBucketContract.from_dict(bucket_payload)
            else:
                raise TypeError(f"{field_name} bucket payload must be a mapping or bucket contract")

        label = bucket.label
        if label in seen:
            raise ValueError(f"{field_name} contains duplicate label: {label}")
        seen.add(label)
        buckets.append(bucket)

    return tuple(sorted(buckets, key=lambda bucket: bucket.label))


@dataclass(slots=True, frozen=True)
class BacktestPerformanceBucketContract:
    label: str
    sample_size: int
    wins: int
    losses: int
    pushes: int
    roi_percent: float
    brier_score: float | None = None
    log_loss: float | None = None
    calibration_summary: Mapping[str, Any] = field(default_factory=dict)
    drawdown_summary: Mapping[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", _normalize_text(self.label, field_name="label"))
        sample_size = _normalize_non_negative_int(self.sample_size, field_name="sample_size")
        wins = _normalize_non_negative_int(self.wins, field_name="wins")
        losses = _normalize_non_negative_int(self.losses, field_name="losses")
        pushes = _normalize_non_negative_int(self.pushes, field_name="pushes")
        if wins + losses + pushes > sample_size:
            raise ValueError("wins + losses + pushes cannot exceed sample_size")
        object.__setattr__(self, "sample_size", sample_size)
        object.__setattr__(self, "wins", wins)
        object.__setattr__(self, "losses", losses)
        object.__setattr__(self, "pushes", pushes)
        object.__setattr__(self, "roi_percent", _normalize_finite_float(self.roi_percent, field_name="roi_percent"))
        object.__setattr__(self, "brier_score", None if self.brier_score in (None, "") else _normalize_probability(self.brier_score, field_name="brier_score"))
        object.__setattr__(self, "log_loss", None if self.log_loss in (None, "") else _normalize_non_negative_float(self.log_loss, field_name="log_loss"))
        object.__setattr__(self, "calibration_summary", _normalize_summary_mapping(self.calibration_summary, field_name="calibration_summary"))
        object.__setattr__(self, "drawdown_summary", _normalize_summary_mapping(self.drawdown_summary, field_name="drawdown_summary"))
        object.__setattr__(self, "warnings", _normalize_text_summary(self.warnings, field_name="warnings"))
        object.__setattr__(self, "metadata", _normalize_summary_mapping(self.metadata, field_name="metadata"))

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "sample_size": self.sample_size,
            "wins": self.wins,
            "losses": self.losses,
            "pushes": self.pushes,
            "roi_percent": self.roi_percent,
            "brier_score": self.brier_score,
            "log_loss": self.log_loss,
            "calibration_summary": _json_ready(self.calibration_summary),
            "drawdown_summary": _json_ready(self.drawdown_summary),
            "warnings": list(self.warnings),
            "metadata": _json_ready(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BacktestPerformanceBucketContract":
        data = dict(payload)
        return cls(
            label=data.get("label", ""),
            sample_size=data.get("sample_size", 0),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            pushes=data.get("pushes", 0),
            roi_percent=data.get("roi_percent", 0.0),
            brier_score=data.get("brier_score"),
            log_loss=data.get("log_loss"),
            calibration_summary=data.get("calibration_summary") or {},
            drawdown_summary=data.get("drawdown_summary") or {},
            warnings=data.get("warnings") or (),
            metadata=data.get("metadata") or {},
        )

    @classmethod
    def from_json(cls, text: str) -> "BacktestPerformanceBucketContract":
        return cls.from_dict(json.loads(text))


@dataclass(slots=True, frozen=True)
class BacktestReportContract:
    experiment_id: str
    report_version: str
    created_at: str
    total_decisions: int
    eligible_decisions: int
    rejected_decisions: int
    wins: int
    losses: int
    pushes: int
    sample_size: int
    roi_percent: float
    evaluation_start: str | None = None
    evaluation_end: str | None = None
    brier_score: float | None = None
    log_loss: float | None = None
    calibration_summary: Mapping[str, Any] = field(default_factory=dict)
    drawdown_summary: Mapping[str, Any] = field(default_factory=dict)
    performance_by_season: tuple[BacktestPerformanceBucketContract, ...] = ()
    performance_by_market: tuple[BacktestPerformanceBucketContract, ...] = ()
    performance_by_edge_bucket: tuple[BacktestPerformanceBucketContract, ...] = ()
    rejection_reasons: tuple[tuple[str, int], ...] = ()
    missingness_summary: tuple[tuple[str, int], ...] = ()
    warnings: tuple[str, ...] = ()
    metrics_reference: Mapping[str, Any] = field(default_factory=dict)
    artifact_reference: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "experiment_id", _normalize_text(self.experiment_id, field_name="experiment_id"))
        report_version = _normalize_text(self.report_version, field_name="report_version")
        # Keep the report schema pinned to the canonical version until a coordinated bump is required.
        if report_version != BACKTEST_REPORT_SCHEMA_VERSION:
            raise ValueError(f"report_version must be {BACKTEST_REPORT_SCHEMA_VERSION}")
        object.__setattr__(self, "report_version", report_version)
        object.__setattr__(self, "created_at", _normalize_text(self.created_at, field_name="created_at"))

        _parse_iso_datetime(self.created_at, field_name="created_at")
        start = _parse_iso_datetime(self.evaluation_start, field_name="evaluation_start")
        end = _parse_iso_datetime(self.evaluation_end, field_name="evaluation_end")
        if start is not None and end is not None and end < start:
            raise ValueError("evaluation_end must not be earlier than evaluation_start")
        object.__setattr__(self, "evaluation_start", self.evaluation_start.strip() if isinstance(self.evaluation_start, str) and self.evaluation_start.strip() else None)
        object.__setattr__(self, "evaluation_end", self.evaluation_end.strip() if isinstance(self.evaluation_end, str) and self.evaluation_end.strip() else None)

        total_decisions = _normalize_non_negative_int(self.total_decisions, field_name="total_decisions")
        eligible_decisions = _normalize_non_negative_int(self.eligible_decisions, field_name="eligible_decisions")
        rejected_decisions = _normalize_non_negative_int(self.rejected_decisions, field_name="rejected_decisions")
        wins = _normalize_non_negative_int(self.wins, field_name="wins")
        losses = _normalize_non_negative_int(self.losses, field_name="losses")
        pushes = _normalize_non_negative_int(self.pushes, field_name="pushes")
        sample_size = _normalize_non_negative_int(self.sample_size, field_name="sample_size")

        if eligible_decisions > total_decisions:
            raise ValueError("eligible_decisions cannot exceed total_decisions")
        if rejected_decisions > total_decisions:
            raise ValueError("rejected_decisions cannot exceed total_decisions")
        if eligible_decisions + rejected_decisions != total_decisions:
            raise ValueError("eligible_decisions + rejected_decisions must equal total_decisions")
        if sample_size > total_decisions:
            raise ValueError("sample_size cannot exceed total_decisions")
        if wins + losses + pushes > sample_size:
            raise ValueError("wins + losses + pushes cannot exceed sample_size")

        object.__setattr__(self, "total_decisions", total_decisions)
        object.__setattr__(self, "eligible_decisions", eligible_decisions)
        object.__setattr__(self, "rejected_decisions", rejected_decisions)
        object.__setattr__(self, "wins", wins)
        object.__setattr__(self, "losses", losses)
        object.__setattr__(self, "pushes", pushes)
        object.__setattr__(self, "sample_size", sample_size)
        object.__setattr__(self, "roi_percent", _normalize_finite_float(self.roi_percent, field_name="roi_percent"))
        object.__setattr__(self, "brier_score", None if self.brier_score in (None, "") else _normalize_probability(self.brier_score, field_name="brier_score"))
        object.__setattr__(self, "log_loss", None if self.log_loss in (None, "") else _normalize_non_negative_float(self.log_loss, field_name="log_loss"))
        object.__setattr__(self, "calibration_summary", _normalize_summary_mapping(self.calibration_summary, field_name="calibration_summary"))
        object.__setattr__(self, "drawdown_summary", _normalize_summary_mapping(self.drawdown_summary, field_name="drawdown_summary"))
        object.__setattr__(self, "performance_by_season", _normalize_bucket_collection(self.performance_by_season, field_name="performance_by_season"))
        object.__setattr__(self, "performance_by_market", _normalize_bucket_collection(self.performance_by_market, field_name="performance_by_market"))
        object.__setattr__(self, "performance_by_edge_bucket", _normalize_bucket_collection(self.performance_by_edge_bucket, field_name="performance_by_edge_bucket"))
        object.__setattr__(self, "rejection_reasons", _normalize_count_summary(self.rejection_reasons, field_name="rejection_reasons"))
        object.__setattr__(self, "missingness_summary", _normalize_count_summary(self.missingness_summary, field_name="missingness_summary"))
        object.__setattr__(self, "warnings", _normalize_text_summary(self.warnings, field_name="warnings"))
        object.__setattr__(self, "metrics_reference", _normalize_summary_mapping(_normalize_reference(self.metrics_reference, field_name="metrics_reference"), field_name="metrics_reference"))
        object.__setattr__(self, "artifact_reference", _normalize_summary_mapping(_normalize_reference(self.artifact_reference, field_name="artifact_reference"), field_name="artifact_reference"))

    def as_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "report_version": self.report_version,
            "created_at": self.created_at,
            "evaluation_start": self.evaluation_start,
            "evaluation_end": self.evaluation_end,
            "total_decisions": self.total_decisions,
            "eligible_decisions": self.eligible_decisions,
            "rejected_decisions": self.rejected_decisions,
            "wins": self.wins,
            "losses": self.losses,
            "pushes": self.pushes,
            "sample_size": self.sample_size,
            "roi_percent": self.roi_percent,
            "brier_score": self.brier_score,
            "log_loss": self.log_loss,
            "calibration_summary": _json_ready(self.calibration_summary),
            "drawdown_summary": _json_ready(self.drawdown_summary),
            "performance_by_season": {bucket.label: bucket.as_dict() for bucket in self.performance_by_season},
            "performance_by_market": {bucket.label: bucket.as_dict() for bucket in self.performance_by_market},
            "performance_by_edge_bucket": {bucket.label: bucket.as_dict() for bucket in self.performance_by_edge_bucket},
            "rejection_reasons": {label: count for label, count in self.rejection_reasons},
            "missingness_summary": {label: count for label, count in self.missingness_summary},
            "warnings": list(self.warnings),
            "metrics_reference": _json_ready(self.metrics_reference),
            "artifact_reference": _json_ready(self.artifact_reference),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BacktestReportContract":
        data = dict(payload)
        return cls(
            experiment_id=data.get("experiment_id", ""),
            report_version=data.get("report_version", BACKTEST_REPORT_SCHEMA_VERSION),
            created_at=data.get("created_at", ""),
            evaluation_start=data.get("evaluation_start"),
            evaluation_end=data.get("evaluation_end"),
            total_decisions=data.get("total_decisions", 0),
            eligible_decisions=data.get("eligible_decisions", 0),
            rejected_decisions=data.get("rejected_decisions", 0),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            pushes=data.get("pushes", 0),
            sample_size=data.get("sample_size", 0),
            roi_percent=data.get("roi_percent", 0.0),
            brier_score=data.get("brier_score"),
            log_loss=data.get("log_loss"),
            calibration_summary=data.get("calibration_summary") or {},
            drawdown_summary=data.get("drawdown_summary") or {},
            performance_by_season=data.get("performance_by_season") or (),
            performance_by_market=data.get("performance_by_market") or (),
            performance_by_edge_bucket=data.get("performance_by_edge_bucket") or (),
            rejection_reasons=data.get("rejection_reasons") or (),
            missingness_summary=data.get("missingness_summary") or (),
            warnings=data.get("warnings") or (),
            metrics_reference=data.get("metrics_reference") or {},
            artifact_reference=data.get("artifact_reference") or {},
        )

    @classmethod
    def from_json(cls, text: str) -> "BacktestReportContract":
        return cls.from_dict(json.loads(text))


__all__ = [
    "BACKTEST_REPORT_SCHEMA_VERSION",
    "BacktestPerformanceBucketContract",
    "BacktestReportContract",
]
