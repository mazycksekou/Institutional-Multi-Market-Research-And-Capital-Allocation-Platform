# PHASE10K8ZFO Source Providers Skeleton

## Executive Summary
`src/providers/` now exists as the future canonical provider landing zone. This phase does not migrate runtime provider logic, does not delete legacy provider modules, and does not change production behavior.

The package is intentionally scaffold-only. It provides import-safe contracts, registry, health, normalization, and error placeholders so future provider migration batches can land in a stable target without depending on `automation_scheduler` ownership.

src/providers/ now exists as the future canonical provider landing zone. This phase does not migrate runtime provider logic, does not delete legacy provider modules, and does not change production behavior.

## Files Created
- `src/providers/__init__.py`
- `src/providers/base.py`
- `src/providers/contracts.py`
- `src/providers/errors.py`
- `src/providers/registry.py`
- `src/providers/health.py`
- `src/providers/normalization.py`
- `src/providers/adapters/__init__.py`
- `src/providers/kalshi/__init__.py`
- `src/providers/sportsbooks/__init__.py`
- `src/providers/prediction_markets/__init__.py`
- `tests/test_phase10k8zfo_src_providers_skeleton.py`

## Why `src/providers/` Now Exists
- The provider canonicalization phase determined that provider ownership must eventually move into a dedicated canonical package.
- The repo previously had provider behavior split across `betting_providers/*`, `providers/*`, `automation_scheduler/provider_*`, and root-level helpers.
- This skeleton creates the landing zone before runtime logic is migrated.

## What This Phase Does Not Migrate
- no provider runtime migration
- no file moves
- no deletion
- no behavior changes
- no live adapter wiring
- no automation_scheduler retirement
- no source-code consolidation of existing provider implementations

## Import Safety Guarantees
- `src.providers` imports only local scaffold modules.
- `src.providers` does not import `automation_scheduler`.
- `src.providers` does not import `betting_providers`.
- `src.providers` does not import legacy top-level `providers`.
- `src.providers` does not import live connector libraries at import time.

## No-Network Guarantee
- The skeleton is local-only.
- No import-time requests, httpx, yfinance, broker, or scraper calls are made.
- Registry and health surfaces are in-memory or scaffold-only.

## Credential Safety Guarantee
- No credentials are read at import time.
- No environment secrets are required for import.
- No secret values are committed or printed.

## Compatibility Policy
- Legacy provider packages remain untouched in this phase.
- Existing runtime behavior stays in place.
- The new package is additive and can be adopted by later wrapper-first migrations.

## Future Migration Order
1. Migrate pure contracts and normalization behavior.
2. Repoint wrapper tests to the canonical package.
3. Move registry and health consumers.
4. Add provider family adapters one at a time.
5. Retire legacy shells only after direct importers are gone.

## automation_scheduler Retirement Relationship
- `automation_scheduler` remains a decommission target.
- This skeleton reduces future dependence on `automation_scheduler` by giving provider migration a canonical destination.
- No retirement work happens yet; this phase only creates the target.

## Test Summary
- The new skeleton test verifies import safety, empty registry behavior, scaffold-only health, and the absence of legacy provider dependencies.
- Existing provider contract and adapter tests still pass in the local slice used for validation.

## Next Recommended Phase
- Begin wrapper-first provider migration batches into `src/providers/` with fake-client coverage and no runtime behavior changes.
