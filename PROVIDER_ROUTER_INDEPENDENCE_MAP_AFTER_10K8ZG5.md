# PROVIDER_ROUTER_INDEPENDENCE_MAP_AFTER_10K8ZG5

## Canonical Ownership Map

| Component | Canonical Owner | Status | Notes |
| --- | --- | --- | --- |
| `src.providers.provider_router` | Canonical router | Independent owner | Owns routing behavior directly |
| `betting_providers.provider_router` | Legacy compatibility wrapper | Compatibility only | Delegates to canonical router |
| `providers.odds_provider_router` | Legacy compatibility wrapper | Compatibility only | Still needed for enrichment patch compatibility |
| `main.py` | Runtime consumer | Canonical import path | Imports `src.providers.provider_router.ProviderRouter` |
| `src/api/model_card_service.py` | Runtime consumer | Canonical import path | Imports `src.providers.provider_router.ProviderRouter` |

## Behavior Ownership Summary
- Behavior moved into `src.providers.provider_router`
- Legacy router import dependency removed
- Compatibility import paths remain stable

## Remaining Compatibility
- Legacy router module import
- Legacy provider_category lookup
- Odds bridge compatibility module

## Deletion Readiness
- Canonical router: ready
- `betting_providers.provider_router`: blocked only by downstream compatibility proof
- `providers.odds_provider_router`: blocked by enrichment-test compatibility

## No Deletion
No file was deleted in this phase.

No deletion occurs in this phase.
