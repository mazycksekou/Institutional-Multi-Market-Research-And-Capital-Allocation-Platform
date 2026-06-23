# Phase 10K8ZHH - Service / API / Dashboard Checkpoint

## Executive Summary
The architecture is in the expected mid-thin state:

- service layer: canonical orchestration and bridge ownership exists under `src/services`
- screenshot workflow: still a compatibility shell awaiting service extraction
- decision/bet log: decision orchestration is canonical, bet logging remains root-level storage shell
- API layer: mostly thin, with `provider_status_routes.py` and automation route bundles still scheduler-coupled
- dashboard/entrypoints: remain shell boundaries and are not deletion candidates
- automation scheduler: remains a decommission target

## Status Summary

- Service layer status: thin and canonical in the bridge/orchestration path
- Screenshot workflow status: compatibility shell, next service extraction target
- Decision/bet log status: decision service canonical, bet log still a storage shell
- API layer status: thin but still has scheduler-coupled blockers
- Dashboard/entrypoint status: bootstrap/display shells only
- Automation scheduler status: decommission target with remaining compatibility/orchestration shells

## Remaining Legacy Owners

- `screenshot_intake.py`
- `bet_log.py`
- `bet_decision_engine.py`
- `src/api/provider_status_routes.py`
- `src/api/automation_*`
- `automation_scheduler/*` shells noted in the decommission audit

## Next Layer

The next recommended work is the data/backtesting layer:

- keep `src/core` as the math/risk/pricing/probability/portfolio/execution/game-theory home
- keep `src.services` thin
- keep AI/LLM deferred
- keep brokerage deferred
- keep live production deferred

## Validation Note

The targeted phase slice and local ops smoke pass, but the full local gate currently exposes unrelated legacy order-sensitivity in older odds/prediction-market proof tests and one scheduler flow regression. Those failures are outside this phase's new audit bundle and should be handled in a separate stabilization pass if a clean full gate is required.
