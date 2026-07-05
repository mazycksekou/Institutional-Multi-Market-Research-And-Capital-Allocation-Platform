# PHASE 10K8ZGT Prediction-Market Runtime Scheduler Redirection

## Executive Summary
Prediction-market runtime scheduler consumers are redirected away from the legacy Kalshi shell layer and onto the canonical bridge/connector/provider surfaces.

The canonical flow is now:

`src.services.prediction_market_runtime_bridge` -> `src.connectors.prediction_market_data` -> `src.providers.prediction_markets`

Legacy prediction-market shells remain on disk for compatibility and historical evidence, but they are no longer the runtime import target for the scheduler path.

## Big-Picture Architecture
- `src.services.prediction_market_runtime_bridge` owns the scheduler-facing prediction-market bridge.
- `src.connectors.prediction_market_data` owns the inert connector boundary.
- `src.providers.prediction_markets` owns provider normalization and validation.
- `automation_scheduler` consumes the bridge, not the legacy shell layer.

## Runtime Scheduler Imports Before Redirection
The scheduler runtime previously imported directly from:

- `automation_scheduler.kalshi_readonly_adapter`
- `automation_scheduler.kalshi_market_provider`

Those imports also appeared indirectly through readiness helpers.

## Runtime Imports Redirected
The following modules now import the canonical bridge surface:

- `automation_scheduler/__init__.py`
- `automation_scheduler/scheduler_runner.py`
- `automation_scheduler/settlement_discovery.py`
- `automation_scheduler/calibration_collector.py`
- `automation_scheduler/prediction_market_outcome_candidates.py`
- `automation_scheduler/kalshi_readonly_readiness.py`

## Canonical Prediction-Market Flow After Redirection
The scheduler uses the canonical bridge for disabled adapter behavior and snapshot helpers. The bridge then relies on canonical connector and provider surfaces rather than legacy shell ownership.

## Legacy Modules Preserved
The following legacy modules remain importable for compatibility and evidence:

- `kalshi_client.py`
- `providers/kalshi_provider.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`

They are preserved, but they are no longer the scheduler runtime import target.

## Remaining Blockers
The remaining blockers are compatibility and test references, not runtime scheduler ownership.

- Historical tests still import legacy shells.
- Compatibility shells remain on disk.

## Delete-Readiness Status
Runtime blockers for the scheduler path have been removed by redirection.

The legacy shells are still not delete-ready because historical compatibility tests and compatibility proof files still touch them.

## Why No Deletion Occurred
No deletion occurred because the compatibility/test surface still exists and must be cleaned up before any shell removal.

## Next Recommended Phase
The next safe phase is a delete-readiness recheck for the legacy prediction-market shells after the remaining historical compatibility references are redirected or reclassified.
