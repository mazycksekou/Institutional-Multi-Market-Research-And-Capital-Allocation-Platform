"""Canonical backtesting foundation.

This package owns local-only backtest dataset contracts, leakage checks,
replay planning, and simulation planning. It remains separate from the core
walk-forward engine so the ownership boundaries are explicit.
"""

from .contracts import BacktestDatasetContract, ReplayPlanContract, SimulationPlanContract
from .datasets import build_backtest_dataset_contract, validate_backtest_dataset_order
from .leakage import assert_no_future_timestamps, detect_future_timestamps
from .replay import build_replay_plan, plan_replay_rows
from .simulation import build_simulation_plan, run_simulation_plan

__all__ = [
    "BacktestDatasetContract",
    "ReplayPlanContract",
    "SimulationPlanContract",
    "assert_no_future_timestamps",
    "build_backtest_dataset_contract",
    "build_replay_plan",
    "build_simulation_plan",
    "detect_future_timestamps",
    "plan_replay_rows",
    "run_simulation_plan",
    "validate_backtest_dataset_order",
]
