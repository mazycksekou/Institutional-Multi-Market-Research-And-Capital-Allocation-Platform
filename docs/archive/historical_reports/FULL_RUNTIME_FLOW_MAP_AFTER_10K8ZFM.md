# FULL_RUNTIME_FLOW_MAP_AFTER_10K8ZFM

## Executive Summary
This phase is a full architecture flow audit before any AI, LLM, ML, backtest, broker, or controlled-loader planning. The repo still has a concentrated legacy hub in `automation_scheduler/`, a thin provider compatibility layer, and a large Streamlit dashboard shell. The runtime is still safe for future AI planning because no AI integration is being added here, but the contract boundaries are not yet fully canonicalized.

## Current HEAD
`9402a91` (`docs: plan test suite cleanup`)

## Repo Inventory Snapshot
- Total files in repo: `1554`
- `automation_scheduler/`: `709` files, `355` Python files
- `tests/`: `725` files, `354` Python files
- `src/`: `100` files, `51` Python files
- `scripts/`: `87` files, `6` Python files
- `providers/`: `10` files, `5` Python files
- `betting_providers/`: `18` files, `9` Python files
- `live_market_intelligence/`: `0` files, scaffold-only directory tree
- `data/`: `434` files total, `394` JSON, `38` markdown, `2` DB, `0` JSONL, `0` CSV
- `data/` tracked files: `0`

## Primary Runtime Entry Points
### API
- `main.py` is the FastAPI app assembly entrypoint.
- `api_server.py` is a deployment proxy that dynamically forwards to `main.py`.
- `src/api/*` owns the route registration surfaces.

### Dashboard
- `streamlit_app.py` is the Streamlit shell entrypoint.
- `automation_scheduler/streamlit_dashboard_data.py` owns dashboard-data helpers today.

### CLI / Scheduler
- `scripts/daily_data_hygiene.py` is the daily cleanup orchestration wrapper.
- `scripts/r2_archive_pipeline.py` is the archive bundle / upload / verify / cleanup pipeline.
- `scripts/ops_check.py` is the ops health wrapper.
- `scripts/analyze_json_data.py` and `scripts/init_sports_master_db.py` are additional CLI utilities.

### Scheduler-style entrypoints
The repo has 26 entrypoint-style Python files under `automation_scheduler/` or `scripts/` based on `if __name__ == "__main__"`, `argparse`, `click`, or `typer` style discovery. Representative examples:
- `automation_scheduler/calibration_collector.py`
- `automation_scheduler/open_sports_history_import.py`
- `automation_scheduler/open_sports_history_backfill.py`
- `automation_scheduler/nfl_open_data_backfill.py`
- `automation_scheduler/nfl_open_data_sources.py`
- `automation_scheduler/ops_workflow.py`
- `automation_scheduler/collector_scheduled_runner.py`
- `scripts/daily_data_hygiene.py`
- `scripts/r2_archive_pipeline.py`

## Primary Flow Map
### API Flow
1. `main.py` assembles the FastAPI app.
2. `main.py` registers `src/api/*` route modules.
3. `src/api/provider_status_routes.py` calls into `automation_scheduler` provider health and snapshot helpers.
4. `src/api/automation_review_outcomes_routes.py` and `src/api/automation_institutional_lab_routes.py` still lazily import `automation_scheduler` helpers for auth and approval flows.
5. `src/api/model_card_service.py` uses `betting_providers.ProviderRouter` and `src.core` model math for live-card rendering.

### Dashboard Flow
1. `streamlit_app.py` imports `automation_scheduler.streamlit_dashboard_data`.
2. Dashboard-data helpers aggregate historical rows, feature packs, readiness previews, and backtest summaries.
3. `streamlit_app.py` also imports feature utilities from `automation_scheduler.feature_ablation_lab`, `source_event_link_resolver`, `zero_dte_fixture_template`, `model_data_field_catalog`, and `historical_data_sources`.
4. The UI shell remains separate from the data helpers, and the language boundary is now aligned around risk preset vs scenario mode.

### Provider Flow
1. `main.py` imports `betting_providers.ProviderRouter`.
2. `src/services/enrichment_service.py` still uses the legacy `providers` compatibility shell for enrichment.
3. `src/api/provider_status_routes.py` uses `automation_scheduler` provider health/snapshot helpers for public status endpoints.
4. `betting_providers` contains the active adapter implementations for sportsbook and prediction-market access.
5. `providers/` remains a thin compatibility layer for screenshot/full-board workflows.

### Archive / Hygiene Flow
1. `scripts/daily_data_hygiene.py` inspects `data/`, counts raw/generated inventory, and decides whether a cleanup batch is needed.
2. If cleanup is warranted, it shells into `scripts/r2_archive_pipeline.py`.
3. `scripts/r2_archive_pipeline.py` builds a manifest, bundles candidate JSON/JSONL/CSV inputs into `jsonl.gz`, optionally uploads to R2, verifies the object, marks cleanup eligibility, and only then permits explicit cleanup.
4. `src/storage/archive_manifest.py` owns manifest construction, path generation, and gate state transitions.
5. `src/storage/r2_archive_adapter.py` owns the upload and verification client interface.

### Backtest / Historical Flow
1. `src/services/model_backtest_service.py` delegates to `src.core.backtester`.
2. `automation_scheduler/backtesting_engine.py` still holds legacy backtest scaffolding, calibration summaries, and report builders.
3. `automation_scheduler/historical_backtest_bridge.py` bridges historical odds storage into the backtest flow.
4. `automation_scheduler/historical_odds_sqlite.py` and `automation_scheduler/historical_line_movement.py` still own storage/replay-adjacent historical logic.

### Orchestration Flow
1. `automation_scheduler/ops_workflow.py` is the broad operational workflow hub.
2. `automation_scheduler/scheduler_runner.py` coordinates risk, provider, backtest, alert, review, and health helpers.
3. `automation_scheduler/collector_scheduled_runner.py` validates cron-token based scheduled collection access.
4. `scripts/ops_check.py` is the external CLI wrapper for the ops workflow.

## What Starts Execution
- FastAPI starts in `main.py`, with `api_server.py` used as a proxy entrypoint for deployment/test compatibility.
- Streamlit starts in `streamlit_app.py`.
- Batch hygiene starts in `scripts/daily_data_hygiene.py`.
- Archive storage cleanup starts in `scripts/r2_archive_pipeline.py`.
- Scheduler-style jobs start in `automation_scheduler/*` CLI modules and `scripts/*` wrappers.

## What Owns What
- `src/api/` owns public API routes.
- `src/core/` owns canonical math and pure pricing helpers.
- `src/storage/` owns archive manifests and R2 adapter contracts.
- `automation_scheduler/` still owns most orchestration, legacy provider helpers, dashboard-data helpers, and backtest scaffolding.
- `betting_providers/` is the active compatibility adapter home.
- `providers/` is a thin legacy enrichment shell.
- `streamlit_app.py` is the UI shell, not the data owner.

## Unclear or Unresolved Flows
- `live_market_intelligence/` exists as an empty scaffold tree only; there are no Python files, so it is not yet a runtime flow.
- `src/providers/` does not exist yet, even though the canonical ownership map says provider logic should eventually land there.
- Several root-level legacy modules still exist (`market_pricing.py`, `quant_engine.py`, `risk_engine.py`, `bet_log.py`, `bet_decision_engine.py`, `model_probability.py`, `multi_sport_model_registry.py`, `screenshot_intake.py`), but their precise end-state ownership is not yet canonicalized.

## Safest Future Insertion Points For AI Planning
The safest places to insert AI planning later, without implementing AI now, are the canonical boundaries that already have clear ownership intent:
- `src/core/` for pure math and pricing
- `src/risk/` for policy and sizing
- `src/providers/` for provider adapters and normalization
- `src/metrics/` for reporting metrics
- `src/backtester/` for backtest execution
- `src/storage/` for manifest/archive contracts
- `src/api/` for route ownership
- `streamlit_app.py` as a shell over dashboard-data helpers
- `automation_scheduler/` only as a temporary orchestration layer

## Safety Notes
- No AI integration, commercial LLM integration, ML training, backtest runner implementation, controlled data loader implementation, broker execution, real trade execution, scraper actions, or external live connector work is authorized in this phase.
- This audit maps flow and ownership only; it does not change behavior.
