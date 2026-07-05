from __future__ import annotations

from typing import Any, Mapping, Sequence

from .contracts import BacktestDatasetContract, ReplayPlanContract


def _row_count(dataset: BacktestDatasetContract | Sequence[Mapping[str, Any]]) -> int:
    if isinstance(dataset, BacktestDatasetContract):
        return len(dataset.rows)
    return len(list(dataset))


def build_replay_plan(
    dataset: BacktestDatasetContract | Sequence[Mapping[str, Any]],
    *,
    dataset_name: str | None = None,
    source_name: str | None = None,
    start_index: int = 0,
    limit: int | None = None,
) -> ReplayPlanContract:
    if isinstance(dataset, BacktestDatasetContract):
        ds_name = dataset.dataset_name
        src_name = dataset.source_name
        count = len(dataset.rows)
    else:
        ds_name = dataset_name or "anonymous_dataset"
        src_name = source_name or "anonymous_source"
        count = len(list(dataset))
    if limit is not None:
        count = min(count, max(0, int(limit)))
    return ReplayPlanContract(
        dataset_name=ds_name,
        source_name=src_name,
        row_count=count,
        start_index=max(0, int(start_index)),
        local_only=True,
        execution_enabled=False,
        notes=("local_only_replay_plan", "no_live_execution"),
    )


def plan_replay_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    start_index: int = 0,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    selected = [dict(row) for row in rows[max(0, int(start_index)) :]]
    if limit is not None:
        selected = selected[: max(0, int(limit))]
    return selected
