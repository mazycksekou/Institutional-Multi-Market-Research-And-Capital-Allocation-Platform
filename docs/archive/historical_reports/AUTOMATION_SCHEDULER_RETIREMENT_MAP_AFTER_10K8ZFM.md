# AUTOMATION_SCHEDULER_RETIREMENT_MAP_AFTER_10K8ZFM

## Executive Summary
`automation_scheduler/` is still the largest legacy hub in the repo and is the main blocker to a clean canonical-owner architecture. It currently holds orchestration, provider logic, dashboard-data helpers, risk/gating, backtest scaffolding, and operational wrappers all in one tree. It is not the long-term product brain.

> automation_scheduler is not the long-term product brain. It is retained only while dependencies still require it. The long-term target remains full removal or reduction to a minimal compatibility/orchestration shell before eventual retirement.

## Current HEAD
`9402a91` (`docs: plan test suite cleanup`)

## Known Dependencies On automation_scheduler
### Runtime-critical importers
- `main.py`
- `streamlit_app.py`
- `scripts/ops_check.py`
- `src/api/provider_status_routes.py`
- `src/api/automation_review_outcomes_routes.py`
- `src/api/automation_institutional_lab_routes.py`

### Test-only importers
The static scan found `555` test import edges into `automation_scheduler`. The largest families include:
- dashboard-data tests
- provider tests
- scheduler tests
- backtest tests
- risk / metrics / math tests
- phase-report tests

### Compatibility-only import surfaces
- `automation_scheduler/__init__.py`
- `automation_scheduler/response_compactor.py`
- `automation_scheduler/streamlit_dashboard_data.py`
- `automation_scheduler/provider_*` helpers that are already acting as compatibility bridges

## What Currently Depends On automation_scheduler
| Dependent surface | Current use of automation_scheduler | Runtime-critical | Test-only | Compatibility-only | Blocker for removal |
| --- | --- | --- | --- | --- | --- |
| `main.py` | App assembly imports scheduler modules and compactor helpers | yes | no | no | Main app still composes behavior from scheduler helpers |
| `streamlit_app.py` | Imports dashboard-data and feature helper modules | yes | no | no | Dashboard shell still depends on scheduler data helpers |
| `src/api/provider_status_routes.py` | Serves provider status/snapshot endpoints | yes | no | no | Provider health/status logic still lives in scheduler code |
| `src/api/automation_review_outcomes_routes.py` | Uses cron-token validation helper | yes | no | no | Route still reaches into scheduler for auth helper |
| `src/api/automation_institutional_lab_routes.py` | Uses rejection-response helper | yes | no | no | Route still reaches into scheduler for lab helper |
| `scripts/ops_check.py` | CLI wrapper around ops workflow | yes | no | no | Operational shell still depends on scheduler workflows |
| `tests/*` | Coverage and contract guardrails | no | yes | no | Retirement cannot proceed until wrappers are stable and tests are updated |

## Scheduler Areas That Should Eventually Move Out
### Orchestration only should remain
- `automation_scheduler/ops_workflow.py`
- `automation_scheduler/scheduler_runner.py`
- `automation_scheduler/collector_scheduled_runner.py`
- other thin operational wrappers that only glue jobs together

### Should migrate to canonical owners later
- provider adapters and normalization -> `src/providers/`
- dashboard data -> future `dashboard/` or `src/dashboard_data`
- risk/gating -> `src/risk/`
- metrics/reporting -> `src/metrics/`
- signals/features -> `src/signals/` and `src/markets/`
- backtest/historical replay -> `src/backtester/`
- storage/ledgers -> `src/storage/`

## Runtime-Critical Pieces Still Inside automation_scheduler
- `streamlit_dashboard_data.py`
- `provider_contracts.py`
- `provider_registry.py`
- `provider_health.py`
- `provider_secret_policy.py`
- `provider_payload_validator.py`
- `sharp_sportsbook_adapter.py`
- `kalshi_readonly_adapter.py`
- `kalshi_market_provider.py`
- `sportsbook_odds_provider.py`
- `backtesting_engine.py`
- `backtest_dataset_builder.py`
- `historical_backtest_bridge.py`
- `historical_odds_sqlite.py`
- `streamlit_dashboard_data.py`
- `ops_workflow.py`
- `scheduler_runner.py`

These pieces are runtime-critical today, so they are not deletion candidates.

## Duplicate / Overlap Surfaces Inside automation_scheduler
- provider contracts and provider health mirror future `src/providers` ownership
- backtesting engine and historical bridge mirror future `src/backtester` ownership
- dashboard-data helpers overlap with the Streamlit shell
- risk policy modules overlap with future `src/risk`
- historical SQLite and ledger modules overlap with future `src/storage`

## Migration Must Happen Before Removal
Before any meaningful retirement can happen, the repo needs:
1. canonical owner packages to exist and be stable
2. compatibility wrappers with old import paths preserved
3. behavior-equivalence tests for the wrapper layer
4. no-network fake-client tests for provider surfaces
5. a stable dashboard-data split
6. a clean backtest boundary
7. a storage contract that owns archive and cleanup gates

## End-State Decision
The end state should be:
- full deletion if wrappers and dependencies are fully migrated and the repo no longer needs a scheduler shell, or
- a minimal compatibility/orchestration shell before final retirement if a very small surface remains necessary

Today, the repo is not at that end state.

## Stability Notes
- `automation_scheduler` is still deeply entangled with the runtime app, dashboard, providers, and test suite.
- The daily data hygiene scheduler remains operational, and that operational contract is still one of the reasons the tree cannot be retired yet.
- `agent is advisory only`; no autonomous delete/migrate action is authorized here.

## Conclusion
`automation_scheduler/` is not yet safe to remove. The immediate target is reduction and boundary tightening, not deletion.
