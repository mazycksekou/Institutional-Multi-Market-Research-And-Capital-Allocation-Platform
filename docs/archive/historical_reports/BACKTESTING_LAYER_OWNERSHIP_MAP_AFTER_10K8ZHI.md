# Backtesting Layer Ownership Map After 10K8ZHI

## Target Canonical Owner
`src.backtesting`

## Current Ownership Map

### Core Backtest Orchestration
- `automation_scheduler/backtesting_engine.py`
- `src/core/backtester.py`
- `src/services/model_backtest_service.py`
- `src/api/model_backtest_routes.py`
- `src/api/performance_routes.py` backtest endpoint

### Dataset Construction and Schema
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/backtest_schema.py`
- `automation_scheduler/backtest_leakage.py`

### Strategy and Bankroll Simulation
- `automation_scheduler/backtest_strategy_bankroll.py`
- `automation_scheduler/backtest_strategy_profiles.py`

### Backtest-adjacent Gates
- `model_governance/backtest_gate.py`
- `model_governance/calibration_gate.py`
- `model_governance/walk_forward_gate.py`

## Why These Belong in `src.backtesting`
- They create, validate, replay, or score historical simulations.
- They are not raw data ingestion.
- They are not core math primitives.
- They are not API routes.

## Thin Canonical Boundary Today
- `src.core.backtester` already provides the reusable backtesting math/orchestration kernel.
- `src.services.model_backtest_service` and `src.api.model_backtest_routes` are thin wrappers over that kernel.

## Migration Order
1. Move schema, leakage, and dataset builder concerns into `src.backtesting`.
2. Move backtesting engine orchestration next.
3. Keep the `src.core.backtester` kernel thin and pure.
4. Reduce `automation_scheduler` to compatibility-only wrappers or delete-ready shims after proof.

