# FUTURE_SRC_PROVIDERS_STRUCTURE_AFTER_10K8ZFN

## Executive Summary
`src/providers/` is the selected future canonical provider owner, but it does not currently exist in the repository. This document proposes the structure that should exist before provider migration begins so that adapters, contracts, health checks, and compatibility wrappers can be split cleanly.

## Proposed Structure
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
    odds_api.py
    sportsgameodds.py
    sharp.py
  prediction_markets/
    __init__.py
    kalshi.py
  data_sources/
    __init__.py
    ncaaf_collegefootballdata.py
    nfl_coaching.py
    nfl_open_data.py
  compat/
    __init__.py
```

## What Belongs There
- Provider base interfaces and adapter contracts.
- Provider registry and provider selection logic.
- Provider health/status summarization.
- Provider payload normalization and schema contracts.
- Provider policy helpers and error types.
- Provider-family adapters such as sportsbook and prediction-market adapters.
- Non-UI provider data-source adapters if they are truly provider-facing.

## What Must Not Belong There
- FastAPI route registration.
- Streamlit or dashboard shell code.
- Scheduler orchestration and daily job control.
- Archive, hygiene, or bundle cleanup logic.
- Backtest execution logic.
- AI/LLM/ML orchestration.
- Report generation for daily ops jobs.

## What Should Remain Outside Providers
- `main.py` app assembly.
- `src/api/*` route wiring.
- `src/services/*` application services that orchestrate provider results.
- `streamlit_app.py` UI shell.
- `scripts/*` operational wrappers and cron/task entrypoints.
- `automation_scheduler/*` only as temporary orchestration and compatibility glue.

## Compatibility-Only During Migration
- `betting_providers/*` should remain an adapter/compatibility layer until wrappers are proven.
- `providers/*` should remain a legacy enrichment compatibility shell until its importers move.
- `automation_scheduler/provider_*` should remain temporary compatibility surfaces until `src/providers/` exists and tests prove the move safe.

## Testing Policy
- Provider tests must use fake clients or static fixtures.
- Provider tests must not make live external API calls.
- Provider tests must not require real credentials.
- Provider route tests must verify wiring, not connectivity.
- Compatibility-wrapper tests must prove old import paths still work.

## Rollout Policy
1. Create the package with contracts, registry, health, and normalization first.
2. Add fake-client tests before adding any live adapter wrapper.
3. Move adapter families one at a time.
4. Keep old import paths as wrappers until the importer count drops to zero.
5. Only after wrappers and tests are stable should retirement of legacy provider surfaces be considered.

## What Should Never Call External APIs During Tests
- Any module under the future `src/providers/` package.
- Legacy compatibility wrappers.
- Provider health/status checks.
- Provider registry and normalization contracts.
- API route tests that expose provider status.

## Non-Goals
- no source migration in this phase
- no file moves in this phase
- no deletion in this phase
- no runtime behavior changes in this phase
- no AI integration, LLM integration, ML training, backtest runner, controlled data loader, broker execution, real trade execution, scraper actions, or live connector expansion

## Risks
- The repo still has live adapter code split across multiple packages.
- Compatibility shells can hide ownership boundaries if they are not documented.
- The test suite still imports the old surfaces directly.

## Recommended Next Phase
Create `src/providers/` in a later approved phase and begin with contracts, registry, health, and normalization. Keep every old provider path as a wrapper until the canonical package is proven stable.
