# Phase 10C Backtest Schema / Alias Registry

Generated: 2026-06-12T19:58:43

## Added
- `automation_scheduler/backtest_schema.py`
- `tests/test_backtest_schema.py`

## Wired
- `automation_scheduler/backtesting_engine.py` imports canonical schema helpers.
- Replay rows are normalized before engine processing.
- Paper-row conversion validates no leakage inside model feature snapshots.

## Registry covers
- event_id / contract_id
- sport / league / market
- decision_time
- odds at decision time
- features known at decision time
- model probability
- market implied probability
- edge
- stake
- final result
- profit/loss
- closing line
- CLV

RESULT: `canonical_backtest_schema_registry_added`
