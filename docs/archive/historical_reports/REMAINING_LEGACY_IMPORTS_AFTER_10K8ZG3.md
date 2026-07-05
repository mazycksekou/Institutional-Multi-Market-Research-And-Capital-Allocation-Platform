# REMAINING_LEGACY_IMPORTS_AFTER_10K8ZG3

## Executive Summary
Some legacy imports remain intentionally, but the wrapper-only legacy surface is significantly reduced.

Wrapper-only modules are not deleted in this phase. This phase redirects downstream imports and produces deletion proof only.

## Remaining Legacy Imports
- `main.py` -> `betting_providers.provider_router.ProviderRouter`
- `src/api/model_card_service.py` -> `betting_providers.provider_router.ProviderRouter`
- compatibility tests for provider foundation transport and legacy deletion readiness
- legacy wrapper reference tests that still patch `providers.odds_provider_router.enrich_ticket`

## Why They Remain
- `betting_providers.provider_router` is a runtime bridge, not a wrapper-only module.
- compatibility tests are still proving legacy resolution on purpose.
- `providers.odds_provider_router` remains as a compatibility hook until its last downstream test is retired or redirected.

## Import Reduction Achieved
- General provider tests now use canonical `src.providers` imports.
- sportsbook and Kalshi registry-based tests now use canonical `src.providers.registry`.
- `main.py` no longer imports `betting_providers.base`.
- `screenshot_intake.py` no longer imports `providers.odds_provider_router`.

## Wrapper Deletion Status
- wrapper-only foundation modules: near deletion-ready
- odds router wrapper: still blocked
- compatibility-test-driven legacy imports: still intentionally present

## Next Phase Recommendation
Proceed to wrapper-only deletion proof after the compatibility test surface shrinks further.
