# Phase 10G Canonical Historical Dataset Builder

Generated: 2026-06-12T20:37:26

## Added
- `automation_scheduler/backtest_dataset_builder.py`
- `tests/test_backtest_dataset_builder.py`

## Purpose
- Discover paper/backtest artifacts.
- Extract candidate row lists.
- Normalize rows through the canonical backtest schema.
- Run sharp-style leakage summary.
- Write canonical JSONL dataset and schema report.

## Important
- This is not a new backtesting engine.
- It produces clean input rows for `automation_scheduler.backtesting_engine.run_backtest()`.
- It can keep incomplete rows for coverage analysis or drop core-incomplete rows when strict mode is enabled.

RESULT: `canonical_historical_dataset_builder_added`
