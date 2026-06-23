# Phase 10K8ZHG - Automation Scheduler Decommission Audit

## Executive Summary
`automation_scheduler` remains a decommission target, but it is now in a much smaller role than before. Canonical prediction-market and odds bridge flow already routes through `src.services`, `src.providers`, and `src.connectors`.

automation_scheduler remains a decommission target.

What remains in `automation_scheduler` is a mix of:

- runtime orchestration that still needs decomposition,
- dashboard/display support,
- compatibility shells,
- and historical tooling that should be moved only when a safe home exists.

## Ownership Summary

- `scheduler_runner.py`: `UNSAFE_TO_TOUCH`
- `calibration_collector.py`: `SERVICE_ORCHESTRATION_OWNER`
- `settlement_discovery.py`: `MIGRATE_TO_SRC_SERVICES`
- `prediction_market_outcome_candidates.py`: `MIGRATE_TO_SRC_SERVICES`
- `streamlit_dashboard_data.py`: `DASHBOARD_LAYER_ONLY`
- `provider_allowlist.py`: `COMPATIBILITY_SHIM_CANDIDATE`
- `data_source_registry.py`: `COMPATIBILITY_SHIM_CANDIDATE`
- `kalshi_monitor.py`: `COMPATIBILITY_SHIM_CANDIDATE`
- `kalshi_scoring.py`: `COMPATIBILITY_SHIM_CANDIDATE`
- `kalshi_readonly_readiness.py`: `COMPATIBILITY_SHIM_CANDIDATE`
- `collector_scheduled_runner.py`: `SERVICE_ORCHESTRATION_OWNER`
- `kalshi_adapter_contract.py`: `COMPATIBILITY_SHIM_CANDIDATE`
- `sportsbook_adapter_contract.py`: `COMPATIBILITY_SHIM_CANDIDATE`

## Decommission Notes

- `automation_scheduler` stays a decommission target.
- The canonical bridge path already exists under `src.services`.
- `streamlit_dashboard_data.py` is dashboard-layer support, not core logic.
- Any remaining runtime orchestration should move to `src.services` only when a local-only replacement is proven.

## Required Statement
`automation_scheduler` remains a decommission target. Its remaining ownership must be mapped to `src.services`, `src.core`, `src.connectors`, or compatibility shells before any deletion is considered.
