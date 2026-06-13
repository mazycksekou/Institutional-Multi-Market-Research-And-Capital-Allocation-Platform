# Phase 10E Unified Replay Strategy Bankroll

Generated: 2026-06-12T20:19:41

## Added
- `automation_scheduler/backtest_strategy_bankroll.py`
- `tests/test_backtest_strategy_bankroll.py`

## Wired
- `automation_scheduler/backtesting_engine.py` now includes `strategy_bankroll_summary` and `strategy_bankroll_report` in `run_backtest()` output.

## Output
- decisions
- bankroll curve
- ROI
- PnL
- max drawdown
- edge buckets
- CLV buckets

RESULT: `unified_replay_strategy_bankroll_added`
