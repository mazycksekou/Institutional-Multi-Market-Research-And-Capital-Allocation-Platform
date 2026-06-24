from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .contracts import AblationPlan


def build_ablation_plan(
    experiment_id: str,
    components: Iterable[Any],
    *,
    controls: Iterable[Any] | None = None,
    metrics: Iterable[Any] | None = None,
    status: str = "planned",
    metadata: dict[str, Any] | None = None,
) -> AblationPlan:
    component_names = tuple(str(item).strip() for item in components if str(item).strip())
    control_names = tuple(str(item).strip() for item in (controls or ()) if str(item).strip())
    metric_names = tuple(str(item).strip() for item in (metrics or ()) if str(item).strip())
    return AblationPlan(
        experiment_id=str(experiment_id).strip() or "experiment",
        components=component_names,
        controls=control_names,
        metrics=metric_names,
        status=str(status).strip() or "planned",
        metadata=dict(metadata or {}),
    )


def describe_ablation_plan(plan: AblationPlan) -> dict[str, Any]:
    return {
        "experiment_id": plan.experiment_id,
        "component_count": len(plan.components),
        "control_count": len(plan.controls),
        "metric_count": len(plan.metrics),
        "status": plan.status,
        "local_only": plan.local_only,
    }

