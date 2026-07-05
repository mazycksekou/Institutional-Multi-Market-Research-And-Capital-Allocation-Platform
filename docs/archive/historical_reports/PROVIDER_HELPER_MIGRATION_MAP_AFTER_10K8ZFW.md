# PROVIDER_HELPER_MIGRATION_MAP_AFTER_10K8ZFW

## Summary
Pure helper logic that used to live in legacy compatibility files now lives in `src.providers.compat`, `src.providers.categories`, and `src.providers.routing`.

## Helpers Moved
- `env_bool`
- `clean_error`
- `unknown_provider`
- `provider_disabled`
- `provider_not_configured`
- `method_not_implemented`
- `available`
- `unavailable`
- `provider_error`
- `ProviderAdapter`
- category normalization helpers
- provider-type to category mapping helpers
- provider-id to category mapping helpers
- category route summary helpers

## Legacy Files Retained as Wrappers
- `betting_providers/base.py`
- `providers/base_provider.py`
- `betting_providers/provider_router.py`

## Compatibility Policy
Legacy import paths remain valid until the next migration batches redirect callers.
Compatibility wrappers preserved.

## Safety
No live behavior was introduced and no network clients were migrated.
