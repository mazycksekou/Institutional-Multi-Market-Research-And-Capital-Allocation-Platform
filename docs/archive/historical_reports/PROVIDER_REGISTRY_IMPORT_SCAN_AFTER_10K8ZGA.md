# Provider Registry Import Scan After 10K8ZGA

## Scan Summary
The runtime import surface for provider registry ownership has been redirected to `src.providers.registry`.

## Runtime Imports Redirected
- `automation_scheduler/__init__.py` -> `src.providers.registry`
- `automation_scheduler/scheduler_config.py` -> `src.providers.registry`
- `automation_scheduler/kalshi_readonly_readiness.py` -> `src.providers.registry`
- `automation_scheduler/cadence_controller.py` -> `src.providers.registry`

## Compatibility Shim Left In Place
- `automation_scheduler/provider_registry.py` remains importable and forwards to canonical registry helpers.

## Before-Change Dependency Evidence
The remaining runtime dependency set before this phase was:
- `automation_scheduler/__init__.py`
- `automation_scheduler/scheduler_config.py`
- `automation_scheduler/kalshi_readonly_readiness.py`
- `automation_scheduler/cadence_controller.py`

## After-Change Dependency Evidence
- No tracked runtime file imports `automation_scheduler.provider_registry` directly.
- Runtime consumers now import canonical registry surfaces from `src.providers.registry`.

## Compatibility Notes
- Legacy provider IDs are preserved through `include_legacy_aliases=True`.
- Canonical registry behavior remains local-only and import-safe.

## Safety Notes
- No live API calls were introduced.
- No credential reads were added at import time.
- No behavior rewrite was performed.
