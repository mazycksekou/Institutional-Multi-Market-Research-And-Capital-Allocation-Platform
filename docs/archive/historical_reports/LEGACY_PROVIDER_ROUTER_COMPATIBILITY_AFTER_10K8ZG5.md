# LEGACY_PROVIDER_ROUTER_COMPATIBILITY_AFTER_10K8ZG5

## Compatibility Status
`betting_providers.provider_router` is now a thin compatibility wrapper around the canonical `src.providers.provider_router` implementation.

## Remaining Compatibility Surface
- `ProviderRouter`
- `provider_category`

## Redirect Target
- `src.providers.provider_router.ProviderRouter`
- `src.providers.provider_router.provider_category`

## Why It Still Exists
- It preserves legacy import paths for older callers and tests.
- It keeps the migration low-risk while downstream references are still being redirected.

## What Remains Blocked
- Deletion is blocked until the remaining compatibility references are fully redirected and proven safe.

## Next Recommended Deletion Batch
Delete the wrapper-only legacy provider router after compatibility proof is complete.

No deletion occurs in this phase.
