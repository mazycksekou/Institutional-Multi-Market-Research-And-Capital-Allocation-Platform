# Phase 10B Backtest Owner Slimming

Generated: 2026-06-12T19:50:03

Canonical owner: `automation_scheduler\backtesting_engine.py`

## Absorbed functions
- `automation_scheduler\backtesting.py:_group_counts`
- `automation_scheduler\backtesting.py:_reason_counts`
- `automation_scheduler\backtesting.py:run_backtesting_scaffold`
- `automation_scheduler\historical_replay.py:load_historical_rows`
- `automation_scheduler\historical_replay.py:replay_rows`
- `automation_scheduler\historical_replay.py:write_replay_result`
- `automation_scheduler\historical_replay.py:summarize_replay_result`

## Added imports
- `from .calibration import calculate_calibration_metrics, summarize_outcome_coverage`
- `from .data_paths import get_runtime_data_path`

## Deleted duplicate modules
- `automation_scheduler\backtesting.py`
- `automation_scheduler\historical_replay.py`

## Updated import files
- `tests\test_backtesting.py`
- `tests\test_historical_replay.py`

RESULT: `backtesting_engine.py is now the single visible backtesting owner`
