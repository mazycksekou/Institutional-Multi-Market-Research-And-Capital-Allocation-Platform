# LEGACY_PROVIDER_ROUTER_IMPORT_SCAN_AFTER_10K8ZG6

## Import Scan Summary
- `main.py` imports `src.providers.provider_router.ProviderRouter`
- `src/api/model_card_service.py` imports `src.providers.provider_router.ProviderRouter`
- `src/api/market_metadata_routes.py` imports canonical provider router methods only
- `screenshot_intake.py` routes enrichment through `src.services.enrichment_service`
- `src/providers/provider_router.py` does not import the legacy router modules

## Legacy Imports Removed From Tests
- No test file currently uses `importlib.import_module("providers.odds_provider_router")`
- No test file currently uses `importlib.import_module("betting_providers.provider_router")`
- No test file currently uses `patch("providers.odds_provider_router...")`
- No test file currently uses `patch("betting_providers.provider_router...")`

## Remaining References
- Historical phase docs still mention the legacy modules as migration evidence
- Negative assertions in phase tests still mention the legacy module names as absence checks

## Delete-Readiness Evidence
- Runtime import proof: complete
- Test patch-target proof: complete
- Compatibility wrapper code: preserved on disk
- Deletion: not executed in this phase

No deletion occurs in this phase.
