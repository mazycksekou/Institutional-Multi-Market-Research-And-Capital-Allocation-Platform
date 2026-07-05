# PREDICTION_MARKET_RUNTIME_IMPORT_SCAN_AFTER_10K8ZGT

## Scan Summary
Direct runtime imports of the legacy prediction-market shells were removed from the scheduler-facing modules.

## Runtime Files Now Import the Canonical Bridge
- `automation_scheduler/__init__.py`
- `automation_scheduler/scheduler_runner.py`
- `automation_scheduler/settlement_discovery.py`
- `automation_scheduler/calibration_collector.py`
- `automation_scheduler/prediction_market_outcome_candidates.py`
- `automation_scheduler/kalshi_readonly_readiness.py`

## Remaining Direct Legacy References
The legacy shells still appear in the legacy shell files themselves and in historical tests, but not in the scheduler runtime import edges above.

## Canonical Runtime Chain
`src.services.prediction_market_runtime_bridge` -> `src.connectors.prediction_market_data` -> `src.providers.prediction_markets`

## Interpretation
The runtime scan confirms the scheduler path has been redirected away from the legacy prediction-market shell layer and onto the canonical bridge surface.
