# Phase 10G2 Sport Regression Profile Wiring

Generated: 2026-06-12T21:21:06

## Decision
- `data_availability_tiers.py` remains the data readiness owner.
- `backtest_strategy_profiles.py` is the focused regression profile selection owner.
- `backtesting_engine.py` remains the canonical public runner.

## Added
- all_sports regression profile support.
- sport_specific regression profile support.
- profile routing mode in `run_backtest(strategy_config={mode: sport_profiles, ...})`.
- dataset field coverage reporting for sport/league/model fields.

## Why
- Avoids overloading data availability tiers with betting math.
- Avoids duplicate public backtest engines.
- Keeps real-time execution path understandable.

RESULT: `sport_regression_profile_wiring_added`
