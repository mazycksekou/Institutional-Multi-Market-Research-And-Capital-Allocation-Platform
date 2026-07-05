# PREDICTION_MARKET_RUNTIME_SCHEDULER_REDIRECTION_MAP_AFTER_10K8ZGT

| File | Previous Import Target | New Import Target | Notes |
| --- | --- | --- | --- |
| `automation_scheduler/__init__.py` | legacy Kalshi shell modules | `src.services.prediction_market_runtime_bridge` | Scheduler entrypoint now uses the bridge for adapter and snapshot helpers. |
| `automation_scheduler/scheduler_runner.py` | legacy Kalshi shell modules | `src.services.prediction_market_runtime_bridge` | Runtime scheduler path now uses bridge-owned adapter and snapshot helpers. |
| `automation_scheduler/settlement_discovery.py` | legacy Kalshi shell module | `src.services.prediction_market_runtime_bridge` | Settlement discovery now consumes the canonical bridge adapter. |
| `automation_scheduler/calibration_collector.py` | legacy Kalshi shell module | `src.services.prediction_market_runtime_bridge` | Calibration collection now uses the canonical bridge adapter. |
| `automation_scheduler/prediction_market_outcome_candidates.py` | readiness helper built on legacy shell | `src.services.prediction_market_runtime_bridge` via readiness helper | Readiness helper now instantiates the canonical bridge adapter. |
| `automation_scheduler/kalshi_readonly_readiness.py` | legacy Kalshi shell module | `src.services.prediction_market_runtime_bridge` | Readiness builder no longer imports the legacy shell directly. |

## Result
Scheduler/runtime consumers now route through the canonical bridge surface instead of the legacy shell layer.
