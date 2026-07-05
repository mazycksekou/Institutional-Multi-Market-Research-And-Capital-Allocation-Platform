# Automation Scheduler Exact Blocker Ledger After 10K8ZMH

Exact import-classification ledger:
- `ACTIVE_RUNTIME_IMPORT`: `0`
- `ACTIVE_TEST_IMPORT`: `105` direct import statements across `76` files
- `ACTIVE_MONKEYPATCH_TARGET`: `0` active patch targets; `6` historical-proof string hits remain in two tests
- `INTERNAL_SCHEDULER_IMPORT`: `745` internal import statements across `262` files
- `DOC_ONLY_REFERENCE`: not counted in this import census
- `HISTORICAL_PROOF_REFERENCE`: `6` proof-string hits in `tests/test_phase10k8zgz_post_provider_connector_cleanup_freeze.py` and `tests/test_phase10k8zgy_prediction_market_shell_deletion.py`
- `SAFE_TO_REDIRECT`: `0` runtime imports in this batch
- `BLOCKED_REQUIRES_MIGRATION`: `76` test files plus `262` internal package files
- `DELETE_READY_AFTER_PROOF`: `automation_scheduler/` already deleted; the remaining blockers are in `src.automation_scheduler_legacy`

Top active test blockers:
- `tests/test_nfl_coaching_adapters.py` -> `5`
- `tests/test_nfl_open_data_backfill.py` -> `4`
- `tests/test_basketball_player_impact.py` -> `3`
- `tests/test_data_intelligence_stack.py` -> `3`
- `tests/test_market_state_manifold.py` -> `3`
- `tests/test_strategy_framework.py` -> `3`
- `tests/test_football_impact_intelligence.py` -> `2`
- `tests/test_kelly_staking.py` -> `2`
- `tests/test_nfl_coaching_feature_builders.py` -> `2`
- `tests/test_phase10k5_core_arbitrage_engine.py` -> `2`

Top internal scheduler hubs:
- `src/automation_scheduler_legacy/__init__.py` -> `91`
- `src/automation_scheduler_legacy/scheduler_runner.py` -> `20`
- `src/automation_scheduler_legacy/soccer_impact_report.py` -> `16`
- `src/automation_scheduler_legacy/baseball_impact_report.py` -> `15`
- `src/automation_scheduler_legacy/combat_impact_report.py` -> `15`
- `src/automation_scheduler_legacy/golf_impact_report.py` -> `15`
- `src/automation_scheduler_legacy/hockey_impact_report.py` -> `15`
- `src/automation_scheduler_legacy/tennis_impact_report.py` -> `14`
- `src/automation_scheduler_legacy/backtesting_engine.py` -> `13`
- `src/automation_scheduler_legacy/deepseek_profit_lab.py` -> `11`

Exact blocker summary:
- Top-level package deletion is done.
- The next blockers live in the relocated legacy namespace and the test surface that still points at it.
