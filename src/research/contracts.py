from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


def _clean_text(value: Any, fallback: str = "") -> str:
    return str(value).strip() or fallback


def _clean_texts(values: tuple[Any, ...] | list[Any] | None) -> tuple[str, ...]:
    if not values:
        return ()
    cleaned = []
    for value in values:
        text = str(value).strip()
        if text:
            cleaned.append(text)
    return tuple(cleaned)


@dataclass(slots=True, frozen=True)
class ResearchLaneDescriptor:
    lane_id: str
    name: str
    topic: str = ""
    owner: str = "research"
    status: str = "planned"
    local_only: bool = True
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "lane_id": self.lane_id,
            "name": self.name,
            "topic": self.topic,
            "owner": self.owner,
            "status": self.status,
            "local_only": self.local_only,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class HypothesisRecord:
    hypothesis_id: str
    lane_id: str
    statement: str
    expected_direction: str = "unknown"
    status: str = "open"
    evidence: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "lane_id": self.lane_id,
            "statement": self.statement,
            "expected_direction": self.expected_direction,
            "status": self.status,
            "evidence": list(self.evidence),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class ExperimentMetadata:
    experiment_id: str
    lane_id: str
    objective: str
    hypothesis_id: str | None = None
    status: str = "planned"
    local_only: bool = True
    parameters: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "lane_id": self.lane_id,
            "objective": self.objective,
            "hypothesis_id": self.hypothesis_id,
            "status": self.status,
            "local_only": self.local_only,
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class AblationPlan:
    experiment_id: str
    components: tuple[str, ...]
    controls: tuple[str, ...] = ()
    metrics: tuple[str, ...] = ()
    status: str = "planned"
    local_only: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "components": list(self.components),
            "controls": list(self.controls),
            "metrics": list(self.metrics),
            "status": self.status,
            "local_only": self.local_only,
            "metadata": dict(self.metadata),
        }

