# Automation Scheduler Internal Import Scan After 10K8ZMH

Internal scheduler import statements:
- Count: `745`
- Unique files: `262`

Top internal hubs:
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
- `src/automation_scheduler_legacy/football_impact_report.py` -> `11`
- `src/automation_scheduler_legacy/advanced_shape_diagnostics.py` -> `10`
- `src/automation_scheduler_legacy/basketball_player_impact.py` -> `10`
- `src/automation_scheduler_legacy/calibration_collector.py` -> `8`
- `src/automation_scheduler_legacy/cross_asset_manifold_router.py` -> `8`
- `src/automation_scheduler_legacy/middles/__init__.py` -> `8`

Result:
- The relocated legacy namespace still has a dense internal dependency graph.
- These imports are now internal to `src/automation_scheduler_legacy`, not the deleted top-level package.
