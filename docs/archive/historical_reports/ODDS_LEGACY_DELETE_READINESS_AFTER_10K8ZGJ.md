# ODDS Legacy Delete Readiness After 10K8ZGJ

## Status
The legacy odds modules are now disabled compatibility shells, but they are **not** delete-ready yet.

## Current Blockers
- `src/api/market_utility_routes.py` still references the legacy odds module names in audit/navigation logic
- `src/services/enrichment_service.py` still imports `providers.sharp_provider`
- `automation_scheduler` still consumes sportsbook snapshot bridges
- Existing runtime and regression tests still import the legacy module names directly

## Compatibility Shells That Must Stay for Now
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`

## Why No Deletion Occurred
- The goal of this phase is proof and retirement of live behavior, not file removal
- The compatibility surface must remain importable until downstream callers are redirected and proven safe
- Scheduler and screenshot flows still rely on the legacy names even though the live bodies are disabled

## What Would Need to Happen Before Deletion
- Downstream import redirection proof
- Test redirection proof
- Runtime dependency proof that no production path still requires the legacy names
- A delete-proof phase for the remaining compatibility shells

## Next Recommended Phase
Prove that the remaining odds compatibility shells are no longer required by runtime/import paths, then delete them in a later batch if the proof holds.

