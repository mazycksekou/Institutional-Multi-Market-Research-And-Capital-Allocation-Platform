# Next Automation Scheduler Blocker Batch After 10K8ZMH

Next batch focus:
- Start with `tests/test_nfl_coaching_adapters.py`, `tests/test_nfl_open_data_backfill.py`, `tests/test_basketball_player_impact.py`, `tests/test_data_intelligence_stack.py`, `tests/test_market_state_manifold.py`, and `tests/test_strategy_framework.py`.
- Then sweep the remaining 2-hit test files.
- Leave `src/automation_scheduler_legacy/__init__.py` and `src/automation_scheduler_legacy/scheduler_runner.py` for last; they are the largest internal hubs.

Recommended order:
1. Redirect the highest-count legacy test imports to canonical `src.*` modules.
2. Re-run the import census and confirm the test count drops from `105`.
3. Re-check whether the relocated legacy namespace can be collapsed further.
