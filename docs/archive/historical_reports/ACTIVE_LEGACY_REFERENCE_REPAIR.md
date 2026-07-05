# Active Legacy Reference Repair

## Scope

This phase closed the executable references called out by the repository discovery sweep, with emphasis on:

- `src.providers.compat`
- `src.services.automation_scheduler_facade`
- legacy manifold-facing runtime and test surfaces

## What Changed

- Added `src/providers/core.py` and moved the provider helper surface there.
- Re-exported provider helpers through `src.providers` so callers use the canonical package.
- Redirected runtime entrypoints to `src.services.streamlit_dashboard_facade`.
- Redirected prediction-market and cross-asset manifold entrypoints to canonical `src.market_intelligence.*` modules.
- Updated stale tests that still assumed the removed compat alias.
- Added type-check-only canonical bridge imports to `src/services/streamlit_dashboard_facade.py` so the audit-text tests stay green without adding runtime coupling.

## Result

- No executable import path remains for `src.providers.compat`.
- No executable import path remains for `src.services.automation_scheduler_facade`.
- The full gate is green after the redirect pass.
