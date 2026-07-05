# PHASE10K8ZFN Provider Canonicalization Plan

## Executive Summary
Provider ownership is still fragmented across active adapters, legacy compatibility shells, scheduler plumbing, and top-level math helpers. The repo is not ready to migrate provider code yet, but it is ready to define a canonical destination and a safe migration order.

The current provider surface is split across:
- `betting_providers/*`
- `providers/*`
- `automation_scheduler/provider_*`
- `automation_scheduler/kalshi_*`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `automation_scheduler/sportsbook_adapter_contract.py`
- `market_pricing.py`
- `quant_engine.py`
- provider-facing route and service surfaces in `main.py`, `src/api/*`, `src/services/*`, `screenshot_intake.py`, and `streamlit_app.py`

## Current Provider Ownership State
### What exists today
- `betting_providers/` is the active provider adapter home.
- `providers/` is a thin legacy compatibility/enrichment shell.
- `automation_scheduler/` still owns provider contracts, registry, health, policy, payload validation, and live adapter code.
- `src/api/provider_status_routes.py` still exposes provider health and snapshot endpoints from `automation_scheduler`.
- `src/services/enrichment_service.py` still bridges to the legacy `providers/` shell.
- `src/providers/` does not exist yet.

### What is runtime-critical
- `main.py` imports `betting_providers.ProviderRouter`, `automation_scheduler`, `market_pricing`, `quant_engine`, and `src/api/provider_status_routes.py`.
- `src/api/model_card_service.py` uses `betting_providers.ProviderRouter`.
- `src/services/enrichment_service.py` uses `providers.kalshi_provider` and `providers.sharp_provider`.
- `screenshot_intake.py` uses `providers.odds_provider_router`.
- `automation_scheduler/kalshi_readonly_adapter.py` and `automation_scheduler/sharp_sportsbook_adapter.py` contain live adapter code with `httpx`.
- `betting_providers/kalshi_api.py`, `betting_providers/sharp_api.py`, `betting_providers/the_odds_api.py`, and `betting_providers/sportsgameodds.py` are live-call-capable adapters.

### What is compatibility-only
- `providers/odds_provider_router.py` is a legacy wrapper around `src/services/enrichment_service.py`.
- `providers/base_provider.py` is a legacy provider status helper surface.
- `providers/kalshi_provider.py` and `providers/sharp_provider.py` are legacy enrichment shells.
- `betting_providers/__init__.py` and `automation_scheduler/__init__.py` are broad export surfaces that still preserve old import paths.

## Required Statement
`src/providers/ is the selected future canonical provider owner, but it does not currently exist in the repository. This phase authorizes planning only and does not authorize source migration.`

## Future Canonical Provider Owner Recommendation
The long-term provider owner should be `src/providers/`, not `betting_providers/`, `providers/`, or `automation_scheduler/`.

That destination should own:
- provider interfaces
- provider registry and selection
- provider contracts and normalization
- provider health/status reporting
- live adapters split by provider family
- provider errors and policy helpers

It should not own:
- dashboard rendering
- scheduler orchestration
- backtest execution
- archive/hygiene workflows
- API route registration
- report generation
- UI copy or language policy

## Proposed `src/providers/` Structure
```text
src/providers/
  __init__.py
  base.py
  errors.py
  contracts.py
  registry.py
  health.py
  normalization.py
  policy.py
  adapters/
    __init__.py
    base.py
    http.py
  sportsbooks/
    __init__.py
    sharp.py
    odds_api.py
    sportsgameodds.py
  prediction_markets/
    __init__.py
    kalshi.py
  data_sources/
    __init__.py
    ncaaf_collegefootballdata.py
    nfl_coaching.py
    nfl_open_data.py
    news_events.py
    injury_weather.py
    stock_price.py
    stock_fundamentals.py
    player_props.py
  compat/
    __init__.py
```

### What belongs there
- provider adapters
- provider registration and capability lookup
- provider health and registry snapshots
- provider payload contracts and normalization
- provider-specific error and policy helpers
- adapter base classes and shared transport helpers

### What must not belong there
- FastAPI route registration
- dashboard shell logic
- scheduling logic
- archive bundle / cleanup logic
- backtest execution and evaluation
- model training or AI orchestration
- report generation for scheduler or hygiene jobs

### What should remain outside providers
- `main.py` app assembly
- `src/api/*` route wiring
- `streamlit_app.py` UI shell
- `scripts/*` operational jobs
- `automation_scheduler/*` only as temporary orchestration and compatibility glue

### What should be compatibility-only during migration
- `betting_providers/*`
- `providers/*`
- `automation_scheduler/provider_*` modules until the canonical package exists and wrapper tests pass

### What should never call external APIs during tests
- provider adapters
- provider registry tests
- provider health tests
- API route tests for provider status
- dashboard tests that read provider state
- any compatibility wrapper tests

## Migration Principles
1. Preserve old import paths until behavior-equivalence is proven.
2. Move ownership by responsibility, not by file count.
3. Separate contracts, registry, health, and adapters before deleting any wrapper.
4. Do not move provider math into the provider package if the canonical owner is already `src/core/`.
5. Do not let provider migration pull in scheduler, dashboard, backtest, or archive behavior.
6. Use fake clients and static payload fixtures in tests.

## Compatibility Policy
- Keep `betting_providers/` as the active compatibility/adapters layer until `src/providers/` exists.
- Keep `providers/` as a legacy enrichment shell until `src/services/enrichment_service.py` and `screenshot_intake.py` are repointed.
- Keep `automation_scheduler/provider_*` and `automation_scheduler/kalshi_*` alive until wrapper coverage proves the canonical package is equivalent.
- Do not remove or rename public functions during the migration window.

## Testing Policy
- Provider tests must use fake clients or fixed fixtures.
- Provider tests must not rely on live network access.
- Provider tests must not require real credentials.
- Contract tests should prove normalization and selection behavior.
- Wrapper tests should prove the old import path still delegates to the canonical owner.
- Route tests should verify the API wiring without turning into live connector tests.

## Rollback Policy
- Preserve the current wrapper layer until the new canonical package is proven.
- Keep feature flags and env-gated live calls intact during the transition.
- If a migration step changes output shape, stop and wrap instead of deleting the old path.
- Do not retire a compatibility module until its direct importers have been repointed and the test suite proves the new owner is stable.

## Risks
- live adapter modules can hit external APIs if accidentally enabled
- secret policy is spread across scheduler and adapter layers today
- provider math is duplicated across legacy helpers
- API routes still depend on scheduler provider health
- legacy enrichment and screenshot intake still depend on `providers/`
- the test suite still validates many old paths directly

## Non-Goals
- no source migration in this phase
- no deletion in this phase
- no file moves in this phase
- no runtime behavior change in this phase
- no AI integration, LLM integration, ML training, backtest runner, controlled data loader, broker execution, real trade execution, scraper actions, or live connector expansion

## Recommended Next Phase
Proceed to a provider wrapper/scaffold batch that creates `src/providers/` in a later approved phase and begins moving only the safest contracts first, starting with interfaces, normalization, and registry/health plumbing.
