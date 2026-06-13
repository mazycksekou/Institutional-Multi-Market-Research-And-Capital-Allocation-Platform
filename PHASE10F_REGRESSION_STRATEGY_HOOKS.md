# Phase 10F Regression Strategy Hooks

Generated: 2026-06-12T20:33:27

## Added
- Regression-style probability hook inside `automation_scheduler/backtest_strategy_bankroll.py`.
- Tests in `tests/test_backtest_regression_strategy.py`.

## Wired
- `automation_scheduler/backtesting_engine.py` accepts optional `strategy_config`.
- `run_backtest()` can apply transparent feature weights before leakage, replay, and bankroll simulation.

## Important
- This is not a trained model yet.
- It is a transparent strategy hook for testing candidate feature weights.
- Full model training comes after canonical dataset/report coverage is stronger.

RESULT: `regression_strategy_hooks_added`
