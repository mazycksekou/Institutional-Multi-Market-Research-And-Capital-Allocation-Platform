"""Canonical backtesting foundation.

This package owns local-only backtest dataset contracts, leakage checks,
replay planning, and simulation planning. It remains separate from the core
walk-forward engine so the ownership boundaries are explicit.
"""

from .backtest_report_contracts import (
    BACKTEST_REPORT_SCHEMA_VERSION,
    BacktestPerformanceBucketContract,
    BacktestReportContract,
)
from .baseline_backtesting import (
    BASELINE_BACKTEST_SCHEMA_VERSION,
    build_baseline_backtest_dashboard_snapshot,
    get_baseline_backtest_snapshot_for_dashboard,
    reconstruct_point_in_time_correlation,
    reconstruct_point_in_time_covariance,
    reconstruct_point_in_time_covariance_matrix,
    reconstruct_point_in_time_time_dependent_risk_state,
    run_baseline_backtest,
)
from .contracts import BacktestDatasetContract, ReplayPlanContract, SimulationPlanContract
from .datasets import build_backtest_dataset_contract, validate_backtest_dataset_order
from .leakage import assert_no_future_timestamps, detect_future_timestamps
from .decision_row_population import (
    build_decision_row_population,
    build_decision_row_population_dashboard_snapshot,
    build_decision_snapshot_context,
    build_decision_snapshot_context_id,
    build_decision_value_identity,
    get_decision_definition,
    get_decision_row_population_snapshot_for_dashboard,
    list_decision_definition_ids,
    list_decision_definitions,
    summarize_decision_registry,
    validate_decision_registry,
    validate_decision_rows,
)
from .pipeline_validation import (
    PIPELINE_VALIDATION_RUNTIME_VERSION,
    PIPELINE_VALIDATION_SCHEMA_VERSION,
    build_pipeline_validation_snapshot,
    get_pipeline_validation_snapshot_for_dashboard,
)
from .replay import build_replay_plan, plan_replay_rows
from .simulation import build_simulation_plan, run_simulation_plan

__all__ = [
    "BacktestDatasetContract",
    "BACKTEST_REPORT_SCHEMA_VERSION",
    "BASELINE_BACKTEST_SCHEMA_VERSION",
    "BacktestPerformanceBucketContract",
    "BacktestReportContract",
    "ReplayPlanContract",
    "SimulationPlanContract",
    "assert_no_future_timestamps",
    "build_baseline_backtest_dashboard_snapshot",
    "build_decision_row_population",
    "build_decision_row_population_dashboard_snapshot",
    "build_backtest_dataset_contract",
    "build_replay_plan",
    "build_simulation_plan",
    "detect_future_timestamps",
    "build_decision_snapshot_context",
    "build_decision_snapshot_context_id",
    "build_decision_value_identity",
    "build_pipeline_validation_snapshot",
    "get_decision_definition",
    "get_baseline_backtest_snapshot_for_dashboard",
    "get_decision_row_population_snapshot_for_dashboard",
    "get_pipeline_validation_snapshot_for_dashboard",
    "PIPELINE_VALIDATION_RUNTIME_VERSION",
    "PIPELINE_VALIDATION_SCHEMA_VERSION",
    "plan_replay_rows",
    "reconstruct_point_in_time_correlation",
    "reconstruct_point_in_time_covariance",
    "reconstruct_point_in_time_covariance_matrix",
    "reconstruct_point_in_time_time_dependent_risk_state",
    "run_baseline_backtest",
    "run_simulation_plan",
    "list_decision_definition_ids",
    "list_decision_definitions",
    "summarize_decision_registry",
    "validate_decision_registry",
    "validate_decision_rows",
    "validate_backtest_dataset_order",
]
