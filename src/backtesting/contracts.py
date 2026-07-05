from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(slots=True)
class BacktestDatasetContract:
    dataset_name: str
    source_name: str
    rows: list[Mapping[str, Any]] = field(default_factory=list)
    timestamp_field: str = "timestamp"
    local_only: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "source_name": self.source_name,
            "rows": [dict(row) for row in self.rows],
            "timestamp_field": self.timestamp_field,
            "local_only": self.local_only,
            "metadata": dict(self.metadata),
        }

    def validate(self) -> dict[str, Any]:
        from .datasets import validate_backtest_dataset_order

        return validate_backtest_dataset_order(self.rows, timestamp_field=self.timestamp_field)


@dataclass(slots=True, frozen=True)
class ReplayPlanContract:
    dataset_name: str
    source_name: str
    row_count: int
    start_index: int = 0
    local_only: bool = True
    execution_enabled: bool = False
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "source_name": self.source_name,
            "row_count": self.row_count,
            "start_index": self.start_index,
            "local_only": self.local_only,
            "execution_enabled": self.execution_enabled,
            "notes": list(self.notes),
        }


@dataclass(slots=True, frozen=True)
class SimulationPlanContract:
    dataset_name: str
    source_name: str
    strategy_name: str
    row_count: int
    local_only: bool = True
    execution_enabled: bool = False
    trade_execution_enabled: bool = False
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "source_name": self.source_name,
            "strategy_name": self.strategy_name,
            "row_count": self.row_count,
            "local_only": self.local_only,
            "execution_enabled": self.execution_enabled,
            "trade_execution_enabled": self.trade_execution_enabled,
            "notes": list(self.notes),
        }
