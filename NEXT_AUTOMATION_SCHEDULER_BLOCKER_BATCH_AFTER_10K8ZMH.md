# Next Automation Scheduler Blocker Batch After 10K8ZMH

Next batch focus:
- Start with `tests/test_streamlit_dashboard_data.py`, because it is the largest remaining test blocker.
- Then migrate the sport-specific intelligence suites: baseball, golf, hockey, soccer, combat, tennis, and football.
- Then sweep the next high-volume families: advanced red-team, arbitrage, backtesting, calibration, historical line movement, market state manifold, security, and strategy tests.
- Leave the internal package graph for last; the test surface is still the gate to deletion.

Recommended order:
1. Redirect the largest test import clusters to canonical `src.*` modules.
2. Re-run the import census and confirm the test count drops from `524`.
3. When test imports reach `0`, re-check whether `automation_scheduler/` can be deleted cleanly.
