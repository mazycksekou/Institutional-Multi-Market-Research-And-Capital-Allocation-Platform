# PHASE10K8ZFF Canonical Owner Decision Report

## Executive Summary
10K8ZFF turns the 10K8ZFE evidence scan into a canonical owner map for later migration phases. It is a decision report only. This phase does not authorize deletion.

The plan is to centralize pure math, risk policy, provider normalization, storage contracts, and backtest engines behind stable canonical owners while keeping current scheduler and dashboard code in place until the next migration batch.

## Current HEAD
Current HEAD before patch: `8a6ec4d73303824c51f99b8845c758d0e81722c8`

## Purpose
Decide canonical owners, define migration direction, identify future deprecation candidates, and make cleanup safer without changing any implementations yet.

## Scope
- Use the 10K8ZFE evidence scan as the source of truth
- Decide canonical owner by responsibility area
- Define safe migration order
- Preserve current behavior and compatibility
- Keep the daily data hygiene scheduler operational

## Non-Goals
- no files deleted
- no files moved
- no code migrated
- no AI integration
- no ML training
- no backtest runner
- no controlled data loader
- no broker execution
- no real trade execution
- no scraper actions

## Relationship to 10K8ZFE
10K8ZFE was evidence-only and identified duplicate-risk across math / core calculation, metrics / performance, signals / features, risk, providers / data adapter, backtest, storage / ledger / archive, API route, dashboard data, and orchestration / scheduler. This report converts that evidence into a canonical owner decision map.

## Relationship to 10K8ZFE1
10K8ZFE1 aligned product language so that risk preset controls sizing and scenario mode controls missing-data handling. Those terms remain separate and will stay separate in later migration work.

## Relationship to 10K8ZFE2
10K8ZFE2 added the daily data hygiene scheduler, which remains operational. The scheduler is advisory only and does not directly delete files.

## Decision Method
- Start with the duplicate-risk evidence report
- Prefer pure modules over orchestration modules when the code is mathematical or policy-only
- Keep user-facing shells thin
- Use `src/` as the long-term home for canonical logic
- Keep `automation_scheduler/` as orchestration-only where possible

Observed inventory at decision time:
- `automation_scheduler/`: 355 Python files
- `src/`: 51 Python files
- `tests/`: 347 Python files
- `data/`: 172 JSON files, 0 JSONL files, 0 CSV files

## Target Architecture
```text
src/
├── core/          # pure math only: EV, odds, Kelly, CLV, no-vig, arbitrage math
├── risk/          # bankroll, drawdown, exposure, ruin, sizing, hard risk policy
├── providers/     # API/data vendor adapters only
├── markets/       # market schemas + feature definitions
├── signals/       # ORB, footprint, whale flow, RLM, steam, breakouts
├── backtester/    # engine, fills, slippage, costs, scenario backtests
├── metrics/       # Sharpe, CLV, Brier, calibration, ROI, drawdown, PnL
├── storage/       # archive, manifests, repositories, local warehouse contracts
└── api/           # FastAPI routes only

dashboard/
tests/
docs/
scripts/
```

## Canonical Owner Summary Table
| Domain | canonical owner | Supporting modules | migration direction | Keep-for-now files | Future deprecation candidate | Blockers / unknowns | Confidence | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Math / Core Calculation | `src/core/` | `src/core/math_utils.py`, `src/core/clv.py` | Move pure odds, EV, Kelly, CLV, vig, and probability math into `src/core/` | `automation_scheduler/odds_math.py`, `market_pricing.py`, `betting_providers/normalization.py`, `model_probability.py` | Duplicate odds and probability helpers outside `src/core/` | Dashboard and provider code still imports current helper names | high | Freeze a single import surface and add wrapper coverage |
| Metrics / Performance | `src/metrics/` | `automation_scheduler/performance_metrics.py`, `clv_tracker.py`, `strategy_performance_ledger.py`, `field_scorecard.py`, `model_governance/model_validation_report.py` | Extract metric calculations into `src/metrics/` and keep renderers as consumers | `automation_scheduler/performance_metrics.py` | Repeated ROI, drawdown, CLV, calibration, and scorecard calculators | `src/metrics/` does not exist yet and will need a first pass package shape | medium | Create `src/metrics/` next to host pure metric math |
| Signals / Features | `src/signals/` and `src/markets/` | `feature_ablation_lab.py`, `sport_feature_packs.py`, `market_feature_packs.py`, `technical_signal_fields.py`, `representation_feature_builder.py`, `historical_line_movement.py`, `asof_line_movement_query.py` | Split signal algorithms from market schema/feature definitions | Current feature pack and ablation modules in `automation_scheduler/` | Duplicate field packs and signal-derived summaries inside scheduler helpers | Some dashboard helpers consume the same feature catalogs | medium-high | Split schema definitions into `src/markets/` and signal math into `src/signals/` |
| Risk | `src/risk/` | `automation_scheduler/risk_limit_guard.py`, `hard_gate_policy.py`, `drawdown_controls.py`, `exposure_limits.py`, `budget_gates.py`, `risk_of_ruin.py`, `session_risk_rules.py`, `small_account_strategy.py`, `model_governance/risk_gate.py`, `kelly_gate.py` | Move bankroll sizing, exposure, ruin, and hard policy into `src/risk/` | `automation_scheduler/hard_gate_policy.py`, `risk_limit_guard.py` | Split risk policy across too many scheduler modules | UI and scheduler code still expect current helper locations | high | Define a single risk policy package and wrapper contract |
| Providers / Data Adapter | `src/providers/` | `betting_providers/*`, `automation_scheduler/provider_*`, `kalshi_client.py` | Build one provider interface and one normalization contract under `src/providers/` | `betting_providers/provider_router.py`, `automation_scheduler/provider_normalization_contract.py` | Duplicate normalization and adapter logic in scheduler/provider wrappers | Existing route and dashboard consumers still reference old package names | medium | Introduce `src/providers/` as the canonical adapter home |
| Backtest | `src/backtester/` | `src/core/backtester.py`, `automation_scheduler/backtesting_engine.py`, `backtest_dataset_builder.py`, `historical_backtest_bridge.py`, `backtest_strategy_profiles.py`, `backtest_strategy_bankroll.py`, `src/services/model_backtest_service.py` | Move engine, fills, slippage, cost, and scenario backtests into `src/backtester/` | `src/core/backtester.py`, `automation_scheduler/backtesting_engine.py` | Replay and bankroll logic duplicated across backtest helpers | Dashboard and report outputs expect current result shapes | high | Split walk-forward engine from replay bridge before widening callers |
| Storage / Ledger / Archive | `src/storage/` | `src/storage/archive_manifest.py`, `src/storage/r2_archive_adapter.py`, `automation_scheduler/outcome_store.py`, `historical_odds_sqlite.py`, `experiment_history_store.py`, `snapshot_store.py`, `paper_trade_ledger.py`, `paper_decision_ledger.py`, `audit_ledger.py` | Keep archive and manifest contracts in `src/storage/` and move ledgers / warehouse helpers under storage subpackages | Existing storage modules in `automation_scheduler/` | Repeated JSON/SQLite persistence helpers and archive-like wrappers | Operational scripts need stable report paths | high | Preserve current storage contracts and narrow wrappers later |
| API Route | `src/api/` | `main.py`, `api_server.py`, `src/api/*` | Keep all FastAPI routes in `src/api/` with `main.py` as app assembly | `api_server.py` as a thin proxy if needed | Route logic duplicated outside `src/api/` | Low risk, mostly wiring | high | Keep route definitions centralized and avoid new route logic elsewhere |
| Dashboard Data | `dashboard/` later, with `streamlit_app.py` shell and `automation_scheduler/streamlit_dashboard_data.py` as temporary owner | `streamlit_app.py`, `automation_scheduler/streamlit_dashboard_data.py`, `automation_scheduler/report_writer.py` | Split UI shell from data transforms when the dashboard package is introduced | Current Streamlit app shell and dashboard-data helpers | Repeated display payload builders and summaries inside helper code | Streamlit remains the active UI until a future dashboard package exists | medium | Keep Streamlit thin and migrate pure transforms into the future dashboard/service split |
| Orchestration / Scheduler | `automation_scheduler/` temporarily, with `scripts/` for operational jobs | `scheduler_runner.py`, `ops_workflow.py`, `collector_scheduled_runner.py`, `calibration_collector.py`, `deepseek_daily_report.py`, `data_source_registry.py`, `execution_gatekeeper.py`, `strategy_router.py`, `scripts/daily_data_hygiene.py`, `scripts/run_daily_data_hygiene.ps1` | Keep orchestration glue in scheduler/scripts and move business logic out to `src/` | Current scheduler and daily hygiene scripts | Business logic embedded in scheduler modules | Many call sites still depend on scheduler helpers | medium-high | Make `automation_scheduler/` orchestration-only and preserve the daily data hygiene scheduler |

## Math / Core Calculation Decision
Canonical owner: `src/core/`

The canonical future owner is `src/core/math_utils.py` plus `src/core/clv.py`, with `src/core/` as the package boundary. The long-term migration direction is to move pure EV, odds conversion, no-vig, Kelly, CLV, arbitrage, and probability math into `src/core/` and keep older helper modules as compatibility wrappers until callers are updated.

Supporting modules today:
- `src/core/math_utils.py`
- `src/core/clv.py`
- `automation_scheduler/odds_math.py`
- `market_pricing.py`
- `betting_providers/normalization.py`
- `model_probability.py`

Keep for now:
- `automation_scheduler/odds_math.py`
- `market_pricing.py`
- `betting_providers/normalization.py`

Future deprecation candidate:
- duplicate odds and probability helpers outside `src/core/`

Blockers / unknowns:
- provider adapters and dashboard code still import current helper names

Confidence:
- high

Next action:
- freeze a single import surface in `src/core/` and add wrapper tests before moving call sites

## Metrics / Performance Decision
Canonical owner: `src/metrics/`

The canonical future owner should be a new `src/metrics/` package. The migration direction is to move pure metric computation there and leave rendering, persistence, and dashboard formatting in their callers.

Supporting modules today:
- `automation_scheduler/performance_metrics.py`
- `automation_scheduler/clv_tracker.py`
- `automation_scheduler/strategy_performance_ledger.py`
- `automation_scheduler/field_scorecard.py`
- `model_governance/model_validation_report.py`

Keep for now:
- `automation_scheduler/performance_metrics.py`

Future deprecation candidate:
- duplicated ROI, drawdown, CLV, calibration, and scorecard calculators spread across scheduler modules

Blockers / unknowns:
- `src/metrics/` does not exist yet and will need a first package layout

Confidence:
- medium

Next action:
- create `src/metrics/` as the first new home for pure metric math

## Signals / Features Decision
Canonical owner: `src/signals/` for signal algorithms and `src/markets/` for market schemas and feature definitions

The migration direction is to split signal math from market schema/feature catalogs. The scheduler should keep orchestration and ablation workflows, but the signal definitions themselves should move into `src/signals/` and `src/markets/`.

Supporting modules today:
- `automation_scheduler/feature_ablation_lab.py`
- `automation_scheduler/sport_feature_packs.py`
- `automation_scheduler/market_feature_packs.py`
- `automation_scheduler/technical_signal_fields.py`
- `automation_scheduler/representation_feature_builder.py`
- `automation_scheduler/historical_line_movement.py`
- `automation_scheduler/asof_line_movement_query.py`
- `automation_scheduler/synthetic_line_movement_sandbox.py`

Keep for now:
- current feature pack and ablation modules in `automation_scheduler/`

Future deprecation candidate:
- duplicate field packs and signal-derived summaries inside scheduler helpers

Blockers / unknowns:
- dashboard helpers currently consume the same feature catalogs

Confidence:
- medium-high

Next action:
- split feature schema definitions into `src/markets/` and signal math into `src/signals/`

## Risk Decision
Canonical owner: `src/risk/`

The migration direction is to move bankroll sizing, exposure, ruin, drawdown, Kelly, and hard policy logic into `src/risk/` while keeping the scheduler as a thin policy consumer.

Supporting modules today:
- `automation_scheduler/risk_limit_guard.py`
- `automation_scheduler/hard_gate_policy.py`
- `automation_scheduler/drawdown_controls.py`
- `automation_scheduler/exposure_limits.py`
- `automation_scheduler/budget_gates.py`
- `automation_scheduler/risk_of_ruin.py`
- `automation_scheduler/session_risk_rules.py`
- `automation_scheduler/small_account_strategy.py`
- `model_governance/risk_gate.py`
- `model_governance/kelly_gate.py`

Keep for now:
- `automation_scheduler/hard_gate_policy.py`
- `automation_scheduler/risk_limit_guard.py`

Future deprecation candidate:
- split risk policy spread across many scheduler modules

Blockers / unknowns:
- UI and scheduler code still expect the current helper locations

Confidence:
- high

Next action:
- define one `src/risk/` contract and treat everything else as a wrapper surface

## Providers / Data Adapter Decision
Canonical owner: `src/providers/`

The migration direction is to create one provider interface and one normalization contract under `src/providers/`. The current `betting_providers/` package should remain as a compatibility layer until the new package is ready.

Supporting modules today:
- `betting_providers/base.py`
- `betting_providers/provider_router.py`
- `betting_providers/normalization.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sharp_api.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `automation_scheduler/sportsbook_adapter_contract.py`
- `kalshi_client.py`

Keep for now:
- `betting_providers/provider_router.py`
- `automation_scheduler/provider_normalization_contract.py`

Future deprecation candidate:
- duplicate normalization and adapter logic in scheduler/provider wrappers

Blockers / unknowns:
- existing route and dashboard consumers still reference old package names

Confidence:
- medium

Next action:
- introduce `src/providers/` and move the normalization contract there first

## Backtest Decision
Canonical owner: `src/backtester/`

The migration direction is to move the engine, fill logic, slippage, cost modeling, and future scenario backtests into `src/backtester/`. Compatibility wrappers can remain in `src/core/backtester.py` and `automation_scheduler/backtesting_engine.py` until callers are migrated.

Supporting modules today:
- `src/core/backtester.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/historical_backtest_bridge.py`
- `automation_scheduler/backtest_strategy_profiles.py`
- `automation_scheduler/backtest_strategy_bankroll.py`
- `src/services/model_backtest_service.py`

Keep for now:
- `src/core/backtester.py`
- `automation_scheduler/backtesting_engine.py`

Future deprecation candidate:
- replay and bankroll logic duplicated across backtest helpers

Blockers / unknowns:
- dashboard and report outputs expect current result shapes

Confidence:
- high

Next action:
- separate walk-forward engine logic from historical replay helpers

## Storage / Ledger / Archive Decision
Canonical owner: `src/storage/`

The migration direction is to keep archive and manifest contracts in `src/storage/` and move ledger and warehouse helpers under storage subpackages. `scripts/` should remain the operational wrapper layer, including the daily data hygiene scheduler.

Supporting modules today:
- `src/storage/archive_manifest.py`
- `src/storage/r2_archive_adapter.py`
- `automation_scheduler/outcome_store.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `automation_scheduler/experiment_history_store.py`
- `automation_scheduler/snapshot_store.py`
- `automation_scheduler/paper_trade_ledger.py`
- `automation_scheduler/paper_decision_ledger.py`
- `automation_scheduler/audit_ledger.py`
- `model_governance/governance_audit_log.py`

Keep for now:
- existing storage modules in `automation_scheduler/`

Future deprecation candidate:
- duplicated JSON and SQLite persistence helpers across scheduler modules

Blockers / unknowns:
- operational scripts need stable report and manifest paths

Confidence:
- high

Next action:
- keep archive contracts stable and narrow wrappers later

## API Route Decision
Canonical owner: `src/api/`

The migration direction is to keep route registration in `src/api/`, use `main.py` for app assembly, and leave `api_server.py` as a thin deployment proxy if it is still needed.

Supporting modules today:
- `main.py`
- `api_server.py`
- `src/api/system_routes.py`
- `src/api/provider_status_routes.py`
- `src/api/performance_routes.py`
- `src/api/model_backtest_routes.py`
- `src/api/debug_routes.py`

Keep for now:
- `api_server.py`

Future deprecation candidate:
- route logic duplicated outside `src/api/`

Blockers / unknowns:
- low risk; mostly wiring

Confidence:
- high

Next action:
- keep API definitions centralized and avoid adding route logic elsewhere

## Dashboard Data Decision
Canonical owner: `dashboard/` later, with `streamlit_app.py` as the shell and `automation_scheduler/streamlit_dashboard_data.py` as the temporary data owner

The migration direction is to split the Streamlit shell from the data transform layer later. Until that future UI package exists, `streamlit_app.py` remains the app shell and `automation_scheduler/streamlit_dashboard_data.py` remains the temporary data-transform owner.

Supporting modules today:
- `streamlit_app.py`
- `automation_scheduler/streamlit_dashboard_data.py`
- `automation_scheduler/report_writer.py`

Keep for now:
- `streamlit_app.py`
- `automation_scheduler/streamlit_dashboard_data.py`

Future deprecation candidate:
- repeated display payload builders and summary helpers in dashboard code

Blockers / unknowns:
- the Streamlit app is still the active UI, so we should not move the UI shell yet

Confidence:
- medium

Next action:
- keep Streamlit thin and migrate pure transforms into the future dashboard/service split

## Orchestration / Scheduler Decision
Canonical owner: `automation_scheduler/` temporarily, with `scripts/` for operational jobs

The migration direction is to keep orchestration glue in scheduler/scripts, move business logic out to `src/`, and preserve the daily data hygiene scheduler as a script-level operational entry point. Agent policy remains advisory only.

Supporting modules today:
- `automation_scheduler/scheduler_runner.py`
- `automation_scheduler/ops_workflow.py`
- `automation_scheduler/collector_scheduled_runner.py`
- `automation_scheduler/calibration_collector.py`
- `automation_scheduler/deepseek_daily_report.py`
- `automation_scheduler/data_source_registry.py`
- `automation_scheduler/execution_gatekeeper.py`
- `automation_scheduler/strategy_router.py`
- `scripts/daily_data_hygiene.py`
- `scripts/run_daily_data_hygiene.ps1`

Keep for now:
- `automation_scheduler/scheduler_runner.py`
- `automation_scheduler/ops_workflow.py`
- `scripts/daily_data_hygiene.py`

Future deprecation candidate:
- business logic embedded in scheduler modules

Blockers / unknowns:
- many call sites still depend on scheduler helpers directly

Confidence:
- medium-high

Next action:
- make `automation_scheduler/` orchestration-only and preserve the daily data hygiene scheduler

## Must-Not-Delete-Yet List
- `src/core/math_utils.py`
- `src/core/clv.py`
- `automation_scheduler/odds_math.py`
- `market_pricing.py`
- `betting_providers/normalization.py`
- `automation_scheduler/performance_metrics.py`
- `automation_scheduler/clv_tracker.py`
- `automation_scheduler/feature_ablation_lab.py`
- `automation_scheduler/sport_feature_packs.py`
- `automation_scheduler/market_feature_packs.py`
- `automation_scheduler/risk_limit_guard.py`
- `automation_scheduler/hard_gate_policy.py`
- `betting_providers/provider_router.py`
- `automation_scheduler/provider_normalization_contract.py`
- `src/core/backtester.py`
- `automation_scheduler/backtesting_engine.py`
- `src/storage/archive_manifest.py`
- `src/storage/r2_archive_adapter.py`
- `automation_scheduler/outcome_store.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `automation_scheduler/experiment_history_store.py`
- `src/api/system_routes.py`
- `automation_scheduler/streamlit_dashboard_data.py`
- `streamlit_app.py`
- `automation_scheduler/scheduler_runner.py`
- `automation_scheduler/ops_workflow.py`
- `scripts/daily_data_hygiene.py`
- `scripts/run_daily_data_hygiene.ps1`

## Future Deprecation Candidates
- `automation_scheduler/odds_math.py`
- `market_pricing.py`
- `betting_providers/normalization.py`
- `automation_scheduler/performance_metrics.py`
- `automation_scheduler/clv_tracker.py`
- `automation_scheduler/strategy_performance_ledger.py`
- `automation_scheduler/field_scorecard.py`
- `automation_scheduler/feature_ablation_lab.py`
- `automation_scheduler/sport_feature_packs.py`
- `automation_scheduler/market_feature_packs.py`
- `automation_scheduler/risk_limit_guard.py`
- `automation_scheduler/hard_gate_policy.py`
- `betting_providers/provider_router.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/historical_backtest_bridge.py`
- `automation_scheduler/outcome_store.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `automation_scheduler/experiment_history_store.py`
- `automation_scheduler/streamlit_dashboard_data.py`
- `streamlit_app.py`
- `automation_scheduler/scheduler_runner.py`
- `automation_scheduler/ops_workflow.py`

## Migration Order
1. Math / Core Calculation
2. Risk
3. Providers / Data Adapter
4. Storage / Ledger / Archive
5. Signals / Features
6. Metrics / Performance
7. Backtest
8. API Route
9. Dashboard Data
10. Orchestration / Scheduler

This order keeps pure logic ahead of wrappers and reduces the chance of breaking the daily data hygiene scheduler or dashboard consumers.

## Safe Next Actions
- Create thin compatibility wrappers around the canonical owner packages
- Add import-surface tests before moving call sites
- Introduce `src/metrics/`, `src/providers/`, `src/markets/`, `src/signals/`, `src/backtester/`, and `src/risk/` in later phases
- Keep the daily data hygiene scheduler operational
- Review one domain at a time in the migration order above

## Unsafe Actions
- Do not delete files in this phase
- Do not move files in this phase
- Do not migrate code in this phase
- Do not add AI integration
- Do not add ML training
- Do not add backtest runner changes
- Do not add controlled data loader behavior
- Do not add broker execution
- Do not add real trade execution
- Do not add scraper actions

## Acceptance Results
- canonical owner report created: yes
- no files deleted: yes
- no files moved: yes
- no code migrated: yes
- all ten decision domains covered: yes
- must_not_delete_yet list updated: yes
- future deprecation candidates listed: yes
- migration order created: yes
- daily data hygiene scheduler remains operational: yes
- agent is advisory only: yes
- risk preset controls sizing: yes
- scenario mode controls missing-data handling: yes
- source code was preserved: yes
- tests/fixtures were preserved: yes
- manifests were preserved: yes
- archives were preserved: yes
- tracked files were preserved: yes
- no credentials committed: yes
- no secrets printed: yes

## Next Phase Recommendation
Proceed to 10K8ZFG Safe Migration Batch 1.

This phase does not authorize deletion.

