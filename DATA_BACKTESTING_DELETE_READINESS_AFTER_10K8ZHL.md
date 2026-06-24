# Data / Backtesting Delete Readiness After 10K8ZHL

## No Deletions Occurred

This phase is audit-only. No file deletions are authorized.
No deletions occurred.

## Not Yet Delete-Ready

- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/backtest_schema.py`
- `automation_scheduler/backtest_leakage.py`
- `automation_scheduler/backtest_strategy_bankroll.py`
- `automation_scheduler/backtest_strategy_profiles.py`
- `automation_scheduler/historical_data_sources.py`
- `automation_scheduler/historical_odds_importers.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `automation_scheduler/historical_backtest_bridge.py`
- `src/core/backtester.py`
- `src/services/model_backtest_service.py`
- `src/api/model_backtest_routes.py`
- `src/api/performance_routes.py`

## Why

- runtime consumers still exist
- ownership has not been migrated yet
- compatibility proof has not been established for retirement

## Next Step

Complete migration planning for `src.analytics` and `src.research` before any
legacy cleanup is attempted.
