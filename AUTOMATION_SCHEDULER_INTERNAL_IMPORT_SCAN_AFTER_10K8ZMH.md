# Automation Scheduler Internal Import Scan After 10K8ZMH

Internal scheduler import statements:
- Count: `745`
- Unique files: `262`

Top internal hubs:
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
- `automation_scheduler/football_impact_report.py` -> `11`
- `automation_scheduler/advanced_shape_diagnostics.py` -> `10`
- `automation_scheduler/basketball_player_impact.py` -> `10`
- `automation_scheduler/calibration_collector.py` -> `8`
- `automation_scheduler/cross_asset_manifold_router.py` -> `8`
- `automation_scheduler/middles/__init__.py` -> `8`

Result:
- The package still has a dense internal dependency graph.
- These imports are package-internal only; they do not imply external runtime use, but they do show the package is still cohesive and not yet a trivial delete.
