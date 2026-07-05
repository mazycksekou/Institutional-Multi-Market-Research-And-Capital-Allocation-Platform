# PHASE10K8ZG4 Runtime Bridge Import Redirection

## Executive Summary
Runtime bridge imports were redirected away from direct legacy router consumption. `main.py` and `src/api/model_card_service.py` now import the canonical bridge surface under `src.providers`, while legacy modules remain in place for compatibility.

## Big Picture
- `src.providers` is the canonical provider owner.
- `src.connectors` remains the inert external-data boundary.
- Runtime bridge consumers should import canonical bridge surfaces, not legacy router paths.

## Imports Redirected
- `main.py` now imports `ProviderRouter` from `src.providers.provider_router`.
- `src/api/model_card_service.py` now imports `ProviderRouter` from `src.providers.provider_router`.
- Compatibility tests that patch screenshot enrichment now use `screenshot_intake.enrich_ticket` where possible.

## Behavior Preserved
- The runtime router contract remains the same.
- `main.py` still exposes `PROVIDER_ROUTER` and `MODEL_CARD_SERVICE`.
- API/model-card behavior is unchanged.
- Legacy routers remain importable for compatibility.

## Legacy Bridge Imports That Remain
- `src.providers.provider_router` dynamically bridges to the legacy provider router at instantiation time.
- `providers.odds_provider_router` remains as a compatibility hook for downstream tests.
- Legacy router modules are still importable and are not deleted.

## Deletion Readiness
- Deletion-ready later:
  - direct consumer imports in `main.py`
  - direct consumer imports in `src/api/model_card_service.py`
- Still blocked:
  - `providers.odds_provider_router`
  - the underlying legacy runtime router that the canonical bridge still delegates to

## Why No Deletion Occurred
This phase redirects runtime bridge imports only. It produces deletion proof only.

## Next Recommended Deletion Batch
- Retire the remaining compatibility hook around `providers.odds_provider_router`.
- Prove the canonical runtime bridge no longer needs the legacy provider router before any deletion.

## Required Statement
Runtime bridge imports are redirected in this phase, but legacy modules are not deleted. This phase produces deletion proof only.
