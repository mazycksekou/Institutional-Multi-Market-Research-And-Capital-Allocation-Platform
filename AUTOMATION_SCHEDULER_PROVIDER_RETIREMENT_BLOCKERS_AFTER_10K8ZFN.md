# AUTOMATION_SCHEDULER_PROVIDER_RETIREMENT_BLOCKERS_AFTER_10K8ZFN

## Executive Summary
`automation_scheduler` still owns provider contracts, health, registry, policy, and live adapter code. It is not ready for retirement because runtime code and the test suite still depend on those surfaces. The provider split must happen first.

## Required Statement
automation_scheduler remains a decommission target. Provider-related dependencies must be split out before automation_scheduler can be reduced to a minimal compatibility/orchestration shell or removed.

## Runtime Dependencies Still Tied to automation_scheduler
- `main.py`
  - imports `automation_scheduler`
  - uses `automation_scheduler.data_paths`
  - uses `automation_scheduler.response_compactor`
  - still composes runtime behavior from scheduler-owned provider surfaces
- `src/api/provider_status_routes.py`
  - imports `automation_scheduler`
  - serves provider health, registry, and provider-specific snapshot endpoints
- `src/api/automation_review_outcomes_routes.py`
  - imports scheduler review helpers that are provider-adjacent
- `src/api/automation_institutional_lab_routes.py`
  - imports scheduler helper code for institutional lab surfaces
- `scripts/ops_check.py`
  - imports `automation_scheduler.ops_workflow`
- `streamlit_app.py`
  - imports `automation_scheduler.streamlit_dashboard_data`
  - imports scheduler feature helpers that still overlap with provider-facing dashboards
- `screenshot_intake.py`
  - imports `providers.odds_provider_router`, which still points to the legacy provider shell that depends on scheduler-era behavior

## Provider-Related Scheduler Modules That Block Retirement
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `automation_scheduler/provider_allowlist.py`
- `automation_scheduler/provider_write_firewall.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `automation_scheduler/kalshi_scoring.py`
- `automation_scheduler/kalshi_monitor.py`
- `automation_scheduler/kalshi_readonly_readiness.py`
- `automation_scheduler/kalshi_adapter_contract.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `automation_scheduler/sportsbook_adapter_contract.py`
- `automation_scheduler/odds_math.py`
- `automation_scheduler/no_vig_pricing.py`
- `automation_scheduler/provider_contracts.py`

## Known Importers That Must Be Migrated First
1. `src/services/enrichment_service.py`
   - still imports `providers.kalshi_provider` and `providers.sharp_provider`
2. `screenshot_intake.py`
   - still imports `providers.odds_provider_router`
3. `src/api/provider_status_routes.py`
   - still relies on `automation_scheduler` provider health and registry helpers
4. `main.py`
   - still depends on `betting_providers.ProviderRouter` and `automation_scheduler` provider helpers
5. `src/api/model_card_service.py`
   - still depends on `betting_providers.ProviderRouter`

## Tests That Must Be Rewritten Before Retirement
- `tests/test_provider_*`
- `tests/test_kalshi_*`
- `tests/test_sharp_*`
- `tests/test_sportsbook_*`
- `tests/test_screenshot_analysis.py`
- `tests/test_provider_registry.py`
- `tests/test_provider_health.py`
- `tests/test_provider_contracts.py`
- `tests/test_provider_normalization_contract.py`
- `tests/test_provider_payload_validator.py`
- `tests/test_provider_secret_policy.py`
- `tests/test_provider_adapter_base.py`
- provider-related phase/report tests that lock in wrapper paths

## Which Files Can Later Become Shims
- `automation_scheduler/__init__.py`
- `automation_scheduler/provider_*`
- `automation_scheduler/kalshi_*`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `betting_providers/*`
- `providers/*`

## Which Files Are Unsafe To Delete
- `automation_scheduler/__init__.py`
- `automation_scheduler/provider_*`
- `automation_scheduler/kalshi_*`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `betting_providers/provider_router.py`
- `providers/odds_provider_router.py`
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`
- any provider route or service that still imports those surfaces

## Suggested Migration Order
1. Create `src/providers/` in a later phase.
2. Move contracts, registry, health, and normalization first.
3. Repoint `src/services/enrichment_service.py` to the canonical provider package.
4. Repoint `screenshot_intake.py` to the canonical provider package.
5. Repoint `src/api/provider_status_routes.py` to the canonical provider package.
6. Repoint `main.py` and `src/api/model_card_service.py` to the canonical provider package.
7. Add wrapper tests for all old import paths.
8. Only then consider shrinking `automation_scheduler` toward a minimal compatibility/orchestration shell.

## Non-Goals
- no deletion in this phase
- no file moves in this phase
- no source migration in this phase
- no runtime behavior changes in this phase
- no live connector expansion, no external API calls, no AI integration, no ML training, no backtest runner, no broker execution, no real trade execution, no scraper actions

## Recommended Next Phase
Proceed with provider canonicalization planning for `src/providers/` creation and wrapper-first migration batches.
