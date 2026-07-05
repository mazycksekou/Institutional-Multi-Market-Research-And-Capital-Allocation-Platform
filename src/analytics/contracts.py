from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


def _clean_text(value: Any, fallback: str = "") -> str:
    return str(value).strip() or fallback


def _clean_pairs(values: Mapping[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    if not values:
        return ()
    return tuple((str(key).strip(), value) for key, value in values.items() if str(key).strip())


@dataclass(slots=True, frozen=True)
class PerformanceSummaryContract:
    label: str
    sample_count: int
    total_return: float
    average_return: float
    win_count: int
    loss_count: int
    win_rate: float
    best_return: float
    worst_return: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "sample_count": self.sample_count,
            "total_return": self.total_return,
            "average_return": self.average_return,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "win_rate": self.win_rate,
            "best_return": self.best_return,
            "worst_return": self.worst_return,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class AttributionSummaryContract:
    label: str
    components: tuple[tuple[str, float], ...]
    total: float
    residual: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def component_names(self) -> tuple[str, ...]:
        return tuple(name for name, _ in self.components)

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "components": {name: value for name, value in self.components},
            "total": self.total,
            "residual": self.residual,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class CalibrationSummaryContract:
    label: str
    sample_count: int
    calibration_error: float
    calibration_score: float
    buckets: tuple[tuple[str, float], ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "sample_count": self.sample_count,
            "calibration_error": self.calibration_error,
            "calibration_score": self.calibration_score,
            "buckets": {name: value for name, value in self.buckets},
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class GovernanceSummaryContract:
    label: str
    status: str
    blockers: tuple[str, ...] = ()
    checks: tuple[tuple[str, bool], ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def passing_checks(self) -> tuple[str, ...]:
        return tuple(name for name, ok in self.checks if ok)

    @property
    def failing_checks(self) -> tuple[str, ...]:
        return tuple(name for name, ok in self.checks if not ok)

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "status": self.status,
            "blockers": list(self.blockers),
            "checks": {name: ok for name, ok in self.checks},
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class ModelEvaluationSummaryContract:
    model_id: str
    status: str
    metrics: tuple[tuple[str, float], ...] = ()
    notes: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "status": self.status,
            "metrics": {name: value for name, value in self.metrics},
            "notes": list(self.notes),
            "metadata": dict(self.metadata),
        }

