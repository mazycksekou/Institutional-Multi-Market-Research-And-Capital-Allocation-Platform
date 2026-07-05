from __future__ import annotations

from typing import Any, Mapping, Sequence

from .contracts import BacktestDatasetContract, SimulationPlanContract
from .datasets import build_backtest_dataset_contract


def _coerce_dataset(
    dataset: BacktestDatasetContract | Sequence[Mapping[str, Any]],
    *,
    dataset_name: str | None = None,
    source_name: str | None = None,
) -> BacktestDatasetContract:
    if isinstance(dataset, BacktestDatasetContract):
        return dataset
    return build_backtest_dataset_contract(
        dataset,
        dataset_name=dataset_name or "anonymous_dataset",
        source_name=source_name or "anonymous_source",
    )


def build_simulation_plan(
    dataset: BacktestDatasetContract | Sequence[Mapping[str, Any]],
    *,
    strategy_name: str = "preview_only",
    dataset_name: str | None = None,
    source_name: str | None = None,
) -> SimulationPlanContract:
    contract = _coerce_dataset(dataset, dataset_name=dataset_name, source_name=source_name)
    return SimulationPlanContract(
        dataset_name=contract.dataset_name,
        source_name=contract.source_name,
        strategy_name=strategy_name,
        row_count=len(contract.rows),
        local_only=True,
        execution_enabled=False,
        trade_execution_enabled=False,
        notes=("local_only_simulation", "no_trade_execution"),
    )


def run_simulation_plan(plan: SimulationPlanContract | BacktestDatasetContract | Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if isinstance(plan, SimulationPlanContract):
        simulation_plan = plan
    else:
        simulation_plan = build_simulation_plan(plan)
    return {
        "ok": True,
        "status": "simulation_planned",
        "execution_enabled": simulation_plan.execution_enabled,
        "trade_execution_enabled": simulation_plan.trade_execution_enabled,
        "trades_executed": 0,
        "local_only": simulation_plan.local_only,
        "plan": simulation_plan.as_dict(),
    }
