# PHASE10K8ZG2 Legacy Deletion Readiness Audit

## Executive Summary
This phase is an evidence-only audit of ownership, shims, runtime dependencies, and deletion readiness across `src/providers`, `src/connectors`, `providers/`, `betting_providers/`, `automation_scheduler/`, and the legacy root-level provider/client modules.

No deletion occurs in this phase. This phase establishes deletion readiness evidence only.

The current architecture is split in two clear directions:
- Canonical product-category ownership now lives under `src/providers` and `src/connectors`.
- Legacy runtime ownership still remains in `providers/`, `betting_providers/`, `automation_scheduler/`, `main.py`, `streamlit_app.py`, and selected `src/api` / `src/services` entrypoints.

## Current HEAD
- `5ccb259`

## Purpose
Establish a verified deletion-readiness map before any further migration or cleanup.

## Scope
Reviewed:
- `src/providers`
- `src/connectors`
- `providers/`
- `betting_providers/`
- `automation_scheduler/`
- root-level provider/client modules
- `src/api/*`
- `src/services/*`
- `main.py`
- `streamlit_app.py`
- `tests/*`

## Non-Goals
- No deletion
- No migration
- No refactor
- No behavior change
- No live API calls
- No credentials printed

## Method
Evidence was gathered from:
- file inventories
- import/reference scans
- direct inspection of the highest-signal runtime entrypoints and compatibility wrappers

Key scan totals from the reviewed surfaces:
- `providers` line hits: `251`
- `betting_providers` line hits: `31`
- `automation_scheduler` line hits: `885`
- `kalshi` line hits: `920`
- `sharp` line hits: `389`
- `provider_router` line hits: `47`
- `odds_provider_router` line hits: `11`
- `sportsbook_odds_provider` line hits: `6`
- `provider_registry` line hits: `51`
- `provider_health` line hits: `60`
- `provider_contracts` line hits: `36`

## Canonical Ownership Snapshot
- `src/providers` files: `60`
- `src/connectors` files: `62`
- `providers` files: `5`
- `betting_providers` files: `9`
- automation scheduler provider-related files by filename scan: `36`

Reviewed provider-family file count:
- `60 + 5 + 9 + 36 = 110`
- canonical provider ownership under `src/providers`: `60 / 110 = ~55%`

Reviewed connector-family boundary file count:
- `62` canonical connector files
- `12` direct legacy live connector/client modules reviewed
- canonical connector ownership under `src/connectors`: `62 / 74 = ~84%`

These are file-count estimates over the reviewed provider/connector surfaces, not a runtime-execution percentage.

## Legacy Ownership Snapshot
### Canonical replaced
- `providers/base_provider.py`
- `providers/odds_provider_router.py`
- `betting_providers/base.py`
- `betting_providers/normalization.py`
- `betting_providers/provider_router.py`
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `automation_scheduler/provider_write_firewall.py`

## Audit Classification Tags
- `CANONICAL_REPLACED`
- `SHIM_ONLY`
- `LEGACY_RUNTIME_OWNER`
- `RETIREMENT_BLOCKER`
- `DELETE_READY_AFTER_IMPORT_PROOF`
- `UNKNOWN`

### Shim-only or compatibility-only
- `providers/__init__.py`
- `betting_providers/__init__.py`
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `automation_scheduler/provider_write_firewall.py`

### Legacy runtime owners
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`
- `betting_providers/kalshi_api.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `kalshi_client.py`
- `sharp_client.py`

## Retention / Shim Status
- `src/providers` is canonical for provider foundations and read-only category adapters.
- `src/connectors` is canonical for inert raw-access boundaries.
- `providers/` is now mixed: some wrappers are shim-only, but `kalshi_provider.py` and `sharp_provider.py` still own live behavior.
- `betting_providers/` is mixed: `base.py`, `normalization.py`, and `provider_router.py` are compatibility bridges, while vendor clients remain runtime owners.
- `automation_scheduler/` still contains runtime-owned provider behavior, scheduler orchestration, and dashboard/reporting logic.

## Dependency Evidence
### Highest-signal runtime dependency chains
- `main.py` imports `betting_providers.provider_router.ProviderRouter` and `automation_scheduler`.
- `streamlit_app.py` imports `automation_scheduler.streamlit_dashboard_data` and multiple scheduler-owned dashboard helpers.
- `src/api/provider_status_routes.py` calls `automation_scheduler.get_provider_health()`, `get_provider_registry_snapshot()`, `get_sharp_provider_health()`, `run_sharp_provider_snapshot()`, `get_kalshi_provider_health()`, and `run_kalshi_provider_snapshot()`.
- `src/services/enrichment_service.py` imports `providers.kalshi_provider.enrich_with_kalshi` and `providers.sharp_provider.enrich_with_sharp`.
- `src/services/action_betting_service.py` still routes through `betting_providers`.
- `screenshot_intake.py` still imports `providers.odds_provider_router.enrich_ticket`.
- `src/api/model_card_service.py` still depends on `betting_providers.provider_router.ProviderRouter`.

### Live behavior still tied to legacy modules
- `providers/kalshi_provider.py` and `providers/sharp_provider.py` call `requests`.
- `kalshi_client.py` and `sharp_client.py` call `requests`.
- `automation_scheduler/kalshi_readonly_adapter.py` and `automation_scheduler/sharp_sportsbook_adapter.py` call `httpx` and read environment configuration.

## Top 20 Retirement Blockers
1. `main.py`
2. `streamlit_app.py`
3. `src/api/provider_status_routes.py`
4. `src/api/market_metadata_routes.py`
5. `src/api/betting_metadata_routes.py`
6. `src/api/betting_action_routes.py`
7. `src/api/model_card_service.py`
8. `src/services/enrichment_service.py`
9. `src/services/action_betting_service.py`
10. `screenshot_intake.py`
11. `providers/kalshi_provider.py`
12. `providers/sharp_provider.py`
13. `betting_providers/provider_router.py`
14. `betting_providers/kalshi_api.py`
15. `betting_providers/sharp_api.py`
16. `betting_providers/the_odds_api.py`
17. `betting_providers/sportsgameodds.py`
18. `automation_scheduler/kalshi_readonly_adapter.py`
19. `automation_scheduler/sharp_sportsbook_adapter.py`
20. `automation_scheduler/__init__.py`

## First 20 Delete Candidates
These are future candidates only, not deletion targets now:
1. `automation_scheduler/provider_contracts.py`
2. `automation_scheduler/provider_registry.py`
3. `automation_scheduler/provider_health.py`
4. `automation_scheduler/provider_adapter_base.py`
5. `automation_scheduler/provider_normalization_contract.py`
6. `automation_scheduler/provider_payload_validator.py`
7. `automation_scheduler/provider_secret_policy.py`
8. `automation_scheduler/provider_write_firewall.py`
9. `providers/base_provider.py`
10. `betting_providers/base.py`
11. `betting_providers/normalization.py`
12. `providers/odds_provider_router.py`
13. `betting_providers/provider_router.py`
14. `providers/kalshi_provider.py`
15. `providers/sharp_provider.py`
16. `kalshi_client.py`
17. `sharp_client.py`
18. `automation_scheduler/kalshi_readonly_adapter.py`
19. `automation_scheduler/kalshi_market_provider.py`
20. `automation_scheduler/sharp_sportsbook_adapter.py`

## Safest Deletion Batch
The safest future batch is the wrapper-only batch that already forwards to canonical owners:
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `automation_scheduler/provider_write_firewall.py`
- `providers/base_provider.py`
- `betting_providers/base.py`
- `betting_providers/normalization.py`
- `providers/odds_provider_router.py`

That batch should only happen after import redirection proof, compatibility tests, and downstream consumer rewrites.

## Acceptance Results
- Deletion readiness evidence gathered: yes
- No deletion occurred: yes
- No migration occurred: yes
- No behavior changed: yes
- Repo remained import-safe during review: yes

## Next Phase Recommendation
Proceed to a deletion-proof refactor batch only after the compatibility wrappers and their import sites are fully redirected.
