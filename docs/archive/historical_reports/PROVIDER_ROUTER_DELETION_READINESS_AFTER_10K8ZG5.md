# PROVIDER_ROUTER_DELETION_READINESS_AFTER_10K8ZG5

## Deletion Readiness Summary
- `src.providers.provider_router`: ready and canonical
- `betting_providers.provider_router`: nearly ready, but still retained for compatibility
- `providers.odds_provider_router`: not ready yet

## Remaining Blockers
- Compatibility tests still import legacy router modules
- Odds bridge compatibility is still used by screenshot-enrichment tests
- Legacy docs still document wrapper paths

## Safe Next Batch
Redirect the last wrapper-only references and then delete the legacy router wrapper after proof.

## Unsafe Actions
- Deleting `betting_providers.provider_router` before downstream proof
- Deleting `providers.odds_provider_router` before enrichment compatibility proof

## No Deletion
No deletion occurs in this phase.
