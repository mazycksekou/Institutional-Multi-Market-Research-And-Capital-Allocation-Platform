# PHASE10K8ZG5 CANONICAL PROVIDER ROUTER INDEPENDENCE

## Executive Summary
10K8ZG5 makes `src.providers.provider_router` the canonical provider router owner. The router now owns its routing behavior directly instead of delegating to `betting_providers.provider_router`.

This phase preserves public behavior for `main.py` and `src/api/model_card_service.py`, keeps legacy router modules importable for compatibility, and does not delete anything.

## Current HEAD
`f9f31935d1ceba181febfc8c2b06c9e5bb85e236`

## Purpose
Remove the hidden legacy router dependency from the canonical runtime bridge while keeping the runtime contract stable.

## Scope
- Canonical router behavior copied into `src.providers.provider_router`
- Legacy router reduced to compatibility-only wrapper behavior
- Import redirection proof and deletion-readiness evidence

## Non-Goals
- No deletions
- No live API calls
- No credential reads
- No scraping
- No broker execution
- No AI/LLM calls
- No dashboard rewrite
- No main.py logic rewrite

## Relationship to 10K8ZG4
10K8ZG4 redirected runtime bridge imports to the canonical router path. 10K8ZG5 removes the remaining hidden legacy dependency inside that canonical path.

## Behavior Moved
- Provider routing selection logic
- Default sportsbook / prediction-market provider selection
- Provider capability dispatch
- Provider lookup and provider-type validation
- Prediction market helper methods
- Sportsbook odds helper methods

## Legacy Dependency Removed
`src.providers.provider_router` no longer imports `betting_providers.provider_router`.

## Compatibility Remaining
- `betting_providers.provider_router` remains importable
- `providers.odds_provider_router` remains importable
- Legacy `provider_category` lookup remains available for compatibility

## Remaining Blockers
- Legacy adapters still exist and are used until the adapter migration batches finish
- Legacy compatibility tests still reference wrapper modules
- `providers.odds_provider_router` is still needed by the screenshot-enrichment compatibility path

## Deletion Readiness
The canonical router itself is now ready. Legacy wrappers are not deleted in this phase because downstream compatibility proof is still in progress.

## Next Recommended Deletion Batch
Delete the wrapper-only legacy router module after the remaining compatibility references are redirected and verified.

## Required Statement
src.providers.provider_router is the canonical provider router owner after this phase. Legacy provider routers remain only for compatibility and are not deleted in this phase.

No deletion occurs in this phase.
