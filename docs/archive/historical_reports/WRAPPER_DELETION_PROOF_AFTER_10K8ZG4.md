# Wrapper Deletion Proof After 10K8ZG4

## Proof Summary
The remaining runtime bridge consumers were redirected to canonical `src.providers` surfaces, and the legacy modules were left intact.

## Proof Points
- `main.py` no longer imports `betting_providers.provider_router.ProviderRouter` directly.
- `src/api/model_card_service.py` no longer imports `betting_providers.provider_router.ProviderRouter` directly.
- `src.providers.provider_router` resolves as the canonical bridge surface.
- `providers.odds_provider_router` is still importable for compatibility.
- No wrapper-only or legacy runtime files were deleted.

## Behavior Preservation
- The provider router runtime contract remains intact.
- The model card service still receives a router with the same callable surface.
- Existing provider and connector tests remain the safety net.

## Deletion Readiness
- `main.py` and `src/api/model_card_service.py` are no longer deletion blockers for the runtime bridge import itself.
- `providers.odds_provider_router` remains blocked by compatibility coverage.
- The underlying legacy provider router remains blocked until the bridge dependency is retired.

## Required Statement
Runtime bridge imports are redirected in this phase, but legacy modules are not deleted. This phase produces deletion proof only.
