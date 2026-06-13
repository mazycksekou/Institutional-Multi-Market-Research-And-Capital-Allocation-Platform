# Phase 10D Sharp-Style No-Leakage Gate

Generated: 2026-06-12T20:13:09

## Policy
- Hard-fail only when future/result/settlement/CLV fields appear inside pre-decision model features.
- Allow top-level result, PnL, closing line, and CLV fields for backtest grading.
- Warn, do not fail, when timing is ambiguous.

## Added
- `automation_scheduler/backtest_leakage.py`
- `tests/test_backtest_leakage.py`

## Wired
- `automation_scheduler/backtesting_engine.py` now emits a leakage report in `run_backtest()`.
- Backtest paper-row conversion uses the sharp-style hard-leakage gate.

RESULT: `sharp_style_no_leakage_gate_added`
