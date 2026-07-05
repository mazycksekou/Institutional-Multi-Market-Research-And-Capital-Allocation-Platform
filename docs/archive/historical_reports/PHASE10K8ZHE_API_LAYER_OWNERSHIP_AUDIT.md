# Phase 10K8ZHE - API Layer Ownership Audit

## Executive Summary
The API layer is mostly thin and is doing the right job: routing requests into services and provider bridges.

What still needs attention is the remaining `automation_scheduler` coupling, especially `src/api/provider_status_routes.py` and the automation-specific route bundles. Those modules are still route exposure, not math or provider ownership, but they are the clearest remaining API-layer blockers for future thinning.

## Route Ownership Summary

- `src/api/system_routes.py`: `API_LAYER_ONLY`
- `src/api/quant_routes.py`: `API_LAYER_ONLY`
- `src/api/betting_action_routes.py`: `API_LAYER_ONLY`
- `src/api/market_metadata_routes.py`: `API_LAYER_ONLY`
- `src/api/market_utility_routes.py`: `API_LAYER_ONLY`
- `src/api/model_card_service.py`: `API_LAYER_ONLY`
- `src/api/performance_routes.py`: `API_LAYER_ONLY`
- `src/api/debug_routes.py`: `API_LAYER_ONLY`
- `src/api/governance_routes.py`: `API_LAYER_ONLY`
- `src/api/bet_csv_routes.py`: `API_LAYER_ONLY`
- `src/api/betting_metadata_routes.py`: `API_LAYER_ONLY`
- `src/api/provider_status_routes.py`: `COMPATIBILITY_SHIM_CANDIDATE`
- `src/api/automation_*`: `COMPATIBILITY_SHIM_CANDIDATE`

## Misplaced Logic Findings

- Route modules should not own math, pricing, risk, or portfolio logic.
- `src/api/model_card_service.py` is already thin and delegates to canonical services and core helpers.
- `src/api/provider_status_routes.py` still reaches through `automation_scheduler`, so it remains a blocker for future thinning.
- The automation-specific route modules are still route shells over legacy orchestration and should move only when a safe service replacement exists.

## Cleanup Order

1. Keep the thin route modules as API-only shells.
2. Redirect `provider_status_routes.py` away from `automation_scheduler` only after a safe canonical replacement is proven.
3. Move automation route dependencies into `src.services` where they are dependency-free and local-only.
4. Leave dashboard/bootstrap shells out of this layer.

## Required Statement
API routes should call services, not own math/pricing/risk. `src/api/provider_status_routes.py` and the automation route bundles remain the main remaining API-layer blockers for future thinning.
