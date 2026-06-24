from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .contracts import ExperimentMetadata, HypothesisRecord


def build_hypothesis_record(
    hypothesis_id: str,
    lane_id: str,
    statement: str,
    *,
    expected_direction: str = "unknown",
    status: str = "open",
    evidence: Iterable[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> HypothesisRecord:
    cleaned_evidence = tuple(str(item).strip() for item in (evidence or ()) if str(item).strip())
    return HypothesisRecord(
        hypothesis_id=str(hypothesis_id).strip() or "hypothesis",
        lane_id=str(lane_id).strip() or "lane",
        statement=str(statement).strip() or "research hypothesis",
        expected_direction=str(expected_direction).strip() or "unknown",
        status=str(status).strip() or "open",
        evidence=cleaned_evidence,
        metadata=dict(metadata or {}),
    )


def build_experiment_metadata(
    experiment_id: str,
    lane_id: str,
    objective: str,
    *,
    hypothesis_id: str | None = None,
    status: str = "planned",
    parameters: Mapping[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ExperimentMetadata:
    return ExperimentMetadata(
        experiment_id=str(experiment_id).strip() or "experiment",
        lane_id=str(lane_id).strip() or "lane",
        objective=str(objective).strip() or "research objective",
        hypothesis_id=str(hypothesis_id).strip() if hypothesis_id is not None and str(hypothesis_id).strip() else None,
        status=str(status).strip() or "planned",
        parameters=dict(parameters or {}),
        metadata=dict(metadata or {}),
    )

