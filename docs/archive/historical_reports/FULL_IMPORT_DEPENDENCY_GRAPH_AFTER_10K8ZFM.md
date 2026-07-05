# FULL_IMPORT_DEPENDENCY_GRAPH_AFTER_10K8ZFM

## Executive Summary
The repo’s static import graph is still centered on `automation_scheduler/`, with `main.py`, `streamlit_app.py`, and `src/api/*` pulling from it heavily. `src/core/` is the clearest canonical math owner, `src/storage/` is the archive/hygiene owner, and `betting_providers/` remains the active provider compatibility home. `src/providers/` is not present yet, so provider retirement is still blocked on future migration.

## Current HEAD
`9402a91` (`docs: plan test suite cleanup`)

## High-Level Graph
```text
main.py
  -> src.api.*
  -> betting_providers.*
  -> automation_scheduler
  -> model_governance.*
  -> root legacy helpers (bet_log, market_pricing, model_probability, screenshot_intake)

api_server.py
  -> main.py (dynamic proxy)

streamlit_app.py
  -> automation_scheduler.*
  -> pandas / streamlit

src/api/*
  -> automation_scheduler.*
  -> betting_providers.*
  -> src.core.*
  -> src.services.*

src/services/*
  -> providers.*
  -> src.core.*

scripts/*
  -> src.storage.*
  -> automation_scheduler.*

automation_scheduler/*
  -> src.core.*
  -> src.storage.*
  -> model_governance.*
  -> selected root helpers
```

## Cross-Directory Dependency Counts
Static AST scan of the repo found these major cross-group edges:

| From | To | Count | Notes |
| --- | ---: | ---: | --- |
| `tests` | `automation_scheduler` | 555 | Dominant test dependency surface |
| `[root]` | `src` | 37 | Top-level scripts and entrypoints |
| `[root]` | `automation_scheduler` | 23 | Entry scripts and app shells |
| `automation_scheduler` | `src` | 14 | Canonical math/storage/service migration direction is already in motion |
| `src` | `automation_scheduler` | 5 | Current API and service code still depends on scheduler helpers |
| `scripts` | `src` | 4 | Hygiene and archive scripts already use canonical storage contracts |
| `src` | `betting_providers` | 2 | Provider compatibility still bypasses `src/providers/` |
| `src` | `providers` | 2 | Legacy enrichment shell still in use |
| `providers` | `src` | 1 | Legacy shell forwards to canonical service |
| `betting_providers` | `src` | 1 | Canonical math helper reuse already exists |
| `scripts` | `automation_scheduler` | 1 | Ops wrapper reaches into scheduler helpers |
| `tests` | `providers` | 1 | Compatibility-layer coverage still matters |

## Key Runtime Importers
### `main.py`
`main.py` is the largest runtime composition point. It imports:
- `src/api/*` route registration modules
- `betting_providers.ProviderRouter`
- `automation_scheduler`
- `model_governance` gates
- root-level helper modules such as `bet_log`, `bet_decision_engine`, `market_pricing`, `model_probability`, `multi_sport_model_registry`, and `screenshot_intake`

### `streamlit_app.py`
`streamlit_app.py` imports:
- `automation_scheduler.streamlit_dashboard_data`
- `automation_scheduler.feature_ablation_lab`
- `automation_scheduler.source_event_link_resolver`
- `automation_scheduler.zero_dte_fixture_template`
- `automation_scheduler.model_data_field_catalog`
- `automation_scheduler.historical_data_sources`

### `src/api/provider_status_routes.py`
This route module imports `automation_scheduler` and `automation_scheduler.response_compactor` to expose provider status and snapshot endpoints.

### `src/services/enrichment_service.py`
This service imports `providers.kalshi_provider`, `providers.sharp_provider`, and `src.core.entity_resolver`, which shows the legacy provider shell is still part of the runtime graph.

### `scripts/daily_data_hygiene.py`
This wrapper imports `src.storage.archive_manifest` and shells into the archive pipeline. It also reads `git ls-files` to count tracked input files.

### `scripts/r2_archive_pipeline.py`
This pipeline imports `src.storage.archive_manifest` and `src.storage.r2_archive_adapter`. It owns the bundle/upload/verify/cleanup path for generated local data.

### `automation_scheduler/scheduler_runner.py`
This module is still a broad fan-in point for calibration, backtesting, provider health, review queue, and risk helpers. It is one of the clearest pieces of evidence that `automation_scheduler` is still too much of the product brain.

## Provider / Scheduler / Storage Direction Notes
- `src/core/math_utils.py` is already the canonical math helper target.
- `src/core/clv.py` is already the canonical CLV helper target.
- `src/storage/archive_manifest.py` and `src/storage/r2_archive_adapter.py` are the canonical storage/archive contracts.
- `automation_scheduler/provider_*` modules still hold provider contract and policy logic that should later be displaced into `src/providers/`.
- `automation_scheduler/backtesting_engine.py` and friends still hold backtest logic that should later move toward `src/backtester/`.

## Circular Dependency Risk
No hard circular dependency was surfaced in the major package graph, but there are two risk patterns:
1. `automation_scheduler/__init__.py` is a very broad facade that imports many submodules and can create side-effect cascades at import time.
2. `api_server.py` is a dynamic proxy to `main.py`, so runtime dependency order is more indirect than the static graph suggests.

The dependency direction violations that matter most for retirement are:
- `src/services/enrichment_service.py` still imports the legacy `providers` shell instead of a future `src/providers/` home.
- `src/api/*` still depends on `automation_scheduler` for status and review helpers.
- `streamlit_app.py` still depends on `automation_scheduler` dashboard-data helpers.
- `main.py` still composes runtime behavior from legacy root modules that have not been consolidated into canonical owners.

## live_market_intelligence
`live_market_intelligence/` has no files, so there is no import graph to map yet. The directory exists only as a scaffold tree.

## Modules Importing automation_scheduler
The static import scan found direct runtime importers in:
- `main.py`
- `streamlit_app.py`
- `scripts/ops_check.py`
- `src/api/provider_status_routes.py`
- `src/api/automation_review_outcomes_routes.py`
- `src/api/automation_institutional_lab_routes.py`
- `src/services/*` only through local helpers, not by the scheduler root

The test suite also imports `automation_scheduler` heavily, with 555 test import edges in the static scan. That is expected today, but it is a blocker for a clean retirement plan until wrappers and canonical owners are stable.

## Modules Importing providers / betting_providers
- `providers/` is imported by `screenshot_intake.py`, `src/services/enrichment_service.py`, and `tests/test_screenshot_analysis.py`.
- `betting_providers/` is imported by `main.py`, `src/api/model_card_service.py`, and `src/services/action_betting_service.py`.
- `src/providers/` does not yet exist, so the canonical provider destination is still a future migration target rather than a present import destination.

## Dependency Blocks On Decommissioning
The following dependency patterns block any decommissioning of `automation_scheduler/` today:
- public API routes still depend on scheduler health/status helpers
- dashboard data still depends on scheduler data helpers
- daily hygiene still depends on scheduler archive logic
- provider adapters and health checks still live in scheduler modules
- backtest scaffolding still lives in scheduler modules
- the test suite still has deep `automation_scheduler` coverage

## Summary
The graph already points in the right direction:
- canonical math and CLV logic -> `src/core`
- archive/hygiene contracts -> `src/storage`
- API routes -> `src/api`
- dashboard shell -> `streamlit_app.py`
- provider ownership -> future `src/providers/`
- scheduler should become orchestration-only over time

What is still blocking retirement is not architecture intent. It is the amount of live import traffic and the number of remaining compatibility surfaces.
