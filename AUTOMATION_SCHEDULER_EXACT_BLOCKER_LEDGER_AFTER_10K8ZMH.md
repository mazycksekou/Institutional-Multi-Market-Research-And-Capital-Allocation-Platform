# Automation Scheduler Exact Blocker Ledger After 10K8ZMH

Exact import-classification ledger:
- `ACTIVE_RUNTIME_IMPORT`: `0`
- `ACTIVE_TEST_IMPORT`: `387` direct import statements across `191` files
- `ACTIVE_MONKEYPATCH_TARGET`: `0` active patch targets; `6` historical-proof string hits remain in two tests
- `INTERNAL_SCHEDULER_IMPORT`: `745` internal import statements across `262` files
- `DOC_ONLY_REFERENCE`: not counted in this import census
- `HISTORICAL_PROOF_REFERENCE`: `6` proof-string hits in `tests/test_phase10k8zgz_post_provider_connector_cleanup_freeze.py` and `tests/test_phase10k8zgy_prediction_market_shell_deletion.py`
- `SAFE_TO_REDIRECT`: `0` runtime imports in this batch
- `BLOCKED_REQUIRES_MIGRATION`: `198` test files plus `262` internal package files
- `DELETE_READY_AFTER_PROOF`: `0`

Top active test blockers:
- `tests/test_football_impact_intelligence.py` -> `11`
- `tests/test_phase10k5_core_arbitrage_engine.py` -> `10`
- `tests/test_advanced_red_team.py` -> `10`
- `tests/test_security_framework.py` -> `8`
- `tests/test_market_state_manifold.py` -> `8`
- `tests/test_historical_line_movement.py` -> `8`
- `tests/test_extreme_randomness_diagnostics.py` -> `8`
- `tests/test_basketball_player_impact.py` -> `8`
- `tests/test_strategy_framework.py` -> `7`
- `tests/test_nfl_coaching_adapters.py` -> `7`

Top internal scheduler hubs:
- `automation_scheduler/__init__.py` -> `91`
- `automation_scheduler/scheduler_runner.py` -> `20`
- `automation_scheduler/soccer_impact_report.py` -> `16`
- `automation_scheduler/baseball_impact_report.py` -> `15`
- `automation_scheduler/combat_impact_report.py` -> `15`
- `automation_scheduler/golf_impact_report.py` -> `15`
- `automation_scheduler/hockey_impact_report.py` -> `15`
- `automation_scheduler/tennis_impact_report.py` -> `14`
- `automation_scheduler/backtesting_engine.py` -> `13`
- `automation_scheduler/deepseek_profit_lab.py` -> `11`

Exact blocker summary:
- The package is still blocked by the test surface, not by runtime imports.
- Internal package coupling remains dense enough that a delete-only batch would not be honest proof.
