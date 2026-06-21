# Remaining Deletion Blockers After 10K8ZG4

## Current Blockers
- `providers.odds_provider_router`
  - still referenced by compatibility coverage
  - still required until the last patch site is retired or generalized
- Legacy provider router dependency behind `src.providers.provider_router`
  - kept as a canonical bridge dependency for now

## No-Deletion Confirmation
- `main.py` was redirected but not structurally rewritten.
- `src/api/model_card_service.py` was redirected but not structurally rewritten.
- No legacy runtime module was deleted.

## Next Deletion Batch
- Retire or generalize the remaining `providers.odds_provider_router` compatibility hook.
- Prove the canonical runtime bridge can survive without the legacy router before deleting any wrapper-only module.

## Required Statement
Runtime bridge imports are redirected in this phase, but legacy modules are not deleted. This phase produces deletion proof only.
