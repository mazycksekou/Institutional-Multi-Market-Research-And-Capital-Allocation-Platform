# PHASE10K8ZFI automation_scheduler Decomposition Plan

## Executive Summary
10K8ZFI is the automation_scheduler Decomposition Plan. It is a decomposition plan only. This phase does not authorize deletion.

The objective is to classify `automation_scheduler/` into responsibility lanes, define a future owner map, and create a safe migration sequence without changing runtime behavior. automation_scheduler should become orchestration-only over time, while canonical business logic migrates into the owner packages already defined in 10K8ZFF.

## Current HEAD
Current HEAD before patch: `c128c1542c08f372223f1b7d22e8f06e82d82fa9`

## Purpose
Create a professional decomposition plan for `automation_scheduler/` before any moving, deleting, or source migration work begins.

## Scope
- Use the canonical ownership map and earlier guard reports as source of truth
- Classify `automation_scheduler/` files into responsibility lanes
- Define a migration direction and wave order
- Keep the daily data hygiene scheduler remains operational
- Keep behavior unchanged

## Non-Goals
- no files deleted
- no files moved
- no source-function migration
- no public functions removed
- behavior unchanged
- no AI integration
- no ML training
- no backtest runner
- no controlled data loader
- no broker execution
- no real trade execution
- no scraper actions

## Relationship to 10K8ZFF
10K8ZFF is the canonical owner decision report. It defines the canonical owner, canonical ownership map, migration direction, and must_not_delete_yet guidance.

## Relationship to 10K8ZFG
10K8ZFG was report-only and test-only. It preserved old import path preserved, wrapper preserved, and behavior unchanged while deferring all higher-risk work.

## Relationship to 10K8ZFH
10K8ZFH added Ownership Boundary Guards and preserved the API ownership boundary, dashboard ownership boundary, storage operation boundary, and orchestration boundary.

## Decomposition Method
- Inventory `automation_scheduler/` by file and responsibility
- Group files by lane, not by directory accident
- Prefer canonical future owner packages already selected in 10K8ZFF
- Mark unclear files as deprecated/manual-review candidates
- Keep automation_scheduler as orchestration-only over time

## automation_scheduler Inventory
- Total files: 709
- Python files: 355
- Test files in repo: 351
- `src/` Python files: 51
- `data/` inventory: 283 JSON, 0 JSONL, 0 CSV
- daily hygiene script exists: yes
- no frontend page folders were introduced: yes

## Responsibility Lanes

| file | primary lane | secondary lane if any | likely future owner | keep in automation_scheduler temporarily | migration priority | risk level | reason | blockers | recommended future action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `scheduler_runner.py`, `collector_scheduled_runner.py`, `ops_workflow.py`, `calibration_collector.py`, `execution_gatekeeper.py`, `strategy_router.py`, `data_source_registry.py`, `model_maturity_registry.py` | Orchestration / Scheduler | Daily / Ops Utilities | `automation_scheduler/` temporarily, then `src/` for business logic | yes | P1 | medium | These files coordinate scheduled runs, checks, routing, and report generation; they should not own core business logic long term | Many callers still depend on these entry points | Keep orchestration shell only and move business rules later |
| `streamlit_dashboard_data.py`, `report_writer.py` | Dashboard Data | Daily / Ops Utilities | temporary `automation_scheduler/streamlit_dashboard_data.py`, future `dashboard/` or `src/dashboard_data/` split | yes | P1 | high | These helpers build dashboard payloads and display-ready summaries; they are a temporary owner only | Streamlit app shell still consumes them directly | Keep as temporary owner and avoid adding UI logic elsewhere |
| `risk_limit_guard.py`, `hard_gate_policy.py`, `drawdown_controls.py`, `exposure_limits.py`, `budget_gates.py`, `risk_of_ruin.py`, `session_risk_rules.py`, `liquidity_risk.py`, `balance_sheet_risk.py` | Risk / Gating | Orchestration / Scheduler | `src/risk/` | yes | P1 | high | These files implement bankroll, drawdown, exposure, Kelly, ruin, and hard gating logic | UI and scheduler code still expect current helper locations | Keep wrappers stable and migrate policy later |
| `provider_adapter_base.py`, `provider_health.py`, `provider_payload_validator.py`, `provider_normalization_contract.py`, `provider_registry.py`, `sportsbook_adapter_contract.py`, `sportsbook_odds_provider.py`, `sharp_sportsbook_adapter.py` | Providers / Normalization | Orchestration / Scheduler | `src/providers/` or `providers/` | yes | P2 | medium | These files normalize provider payloads, health, routing, and adapter contracts | Existing route and dashboard consumers still reference old package names | Introduce one provider interface and one normalization contract later |
| `performance_metrics.py`, `clv_tracker.py`, `model_performance_report.py`, `field_scorecard.py`, `strategy_performance_ledger.py`, `experiment_report_exporter.py` | Metrics / Reporting | Storage / Ledgers | `src/metrics/` | yes | P2 | medium | These modules calculate or present performance, CLV, and scorecard style outputs | `src/metrics/` is not yet the active home | Extract pure metrics later and leave renderers as consumers |
| `feature_ablation_lab.py`, `derived_feature_planner.py`, `technical_signal_fields.py`, `sport_feature_packs.py`, `market_feature_packs.py`, `historical_line_movement.py`, `asof_line_movement_query.py`, `synthetic_line_movement_sandbox.py`, `representation_feature_builder.py` | Signals / Features | Metrics / Reporting | `src/signals/` and `src/markets/` | yes | P2 | high | These modules mix signal algorithms, feature packs, field catalogs, and derived feature planning | Dashboard helpers still consume the same catalogs | Split schema and signal math later |
| `backtesting_engine.py`, `backtest_dataset_builder.py`, `historical_backtest_bridge.py`, `backtest_strategy_bankroll.py`, `backtest_strategy_profiles.py`, `historical_odds_sqlite.py` | Backtest / Historical Replay | Storage / Ledgers | `src/backtester/` and `src/storage/` | yes | P3 | high | These modules handle historical replay, dataset construction, strategy profiles, bankroll simulation, and SQLite backtest storage | Scenario-based backtesting is not being introduced now | Move engine and replay layers later, keep wrappers until callers are stable |
| `outcome_store.py`, `paper_trade_ledger.py`, `paper_decision_ledger.py`, `experiment_history_store.py`, `snapshot_store.py`, `audit_ledger.py` | Storage / Ledgers | Daily / Ops Utilities | `src/storage/` | yes | P2 | medium | These modules persist outcomes, ledgers, snapshots, experiments, and audit records | Naming and location still carry compatibility baggage | Keep storage contracts stable and migrate later by owner |
| `deepseek_daily_report.py`, `security_readiness_report.py`, `strategy_readiness_report.py`, `intelligence_readiness_report.py`, `derived_feature_backfill_report.py`, `system_health.py`, `manifold_cluster_registry.py` | Daily / Ops Utilities | Orchestration / Scheduler | `scripts/` plus `automation_scheduler/` as shell only | yes | P1 | medium | These are operational checks, readiness reports, or daily utility helpers | Some are still used as scheduled workflow support | Keep ops wrappers thin and move business logic later |
| `baseball_impact_report.py`, `combat_impact_report.py`, `football_impact_report.py`, `golf_impact_report.py`, `hockey_impact_report.py`, `soccer_impact_report.py`, `tennis_impact_report.py`, `extreme_randomness_report.py`, `advanced_red_team_report.py` | Deprecated / Manual Review Candidates | Daily / Ops Utilities | manual review | no | manual-review | low | These names look generated, historical, or domain-specific and do not yet have a clear migration target | Some may be report artifacts or compatibility surface | Review manually before any migration |

## Orchestration / Scheduler Lane
This lane should remain the long-term shell of `automation_scheduler/`. It can host orchestration glue, safety checks, scheduling entry points, and compatibility wrappers, but it should not become a permanent home for core business logic.

## Dashboard Data Lane
This lane stays temporarily in `automation_scheduler/streamlit_dashboard_data.py`. `streamlit_app.py` remains the Streamlit shell. No frontend page files were added. The dashboard ownership boundary remains intact.

## Risk / Gating Lane
This lane should migrate to `src/risk/` in a later wave. The lane keeps risk preset controls sizing and scenario mode controls missing-data handling separate.

## Providers / Normalization Lane
This lane should converge on one provider interface and one normalization contract in `src/providers/` or `providers/`. Current adapters remain in place until the new owner is stable.

## Metrics / Reporting Lane
This lane should move to `src/metrics/` for pure calculations while leaving report formatting and persistence wrappers behind until later.

## Signals / Features Lane
This lane should split into `src/signals/` for algorithms and `src/markets/` for market schemas and feature definitions.

## Backtest / Historical Replay Lane
This lane should move toward `src/backtester/` for engine and replay logic, with `src/storage/` handling repository-style storage boundaries. Scenario backtest work is deferred.

## Storage / Ledgers Lane
This lane should converge on `src/storage/` for archive contracts, ledgers, SQLite repositories, and audit-like persistence.

## Daily / Ops Utilities Lane
This lane includes operational reports, readiness checks, and daily jobs. The daily data hygiene scheduler remains operational, dry-run by default, and agent is advisory only.
agent does not directly delete files.

## Deprecated / Manual Review Candidates
Files in this lane are not safe to migrate blindly. They need manual review because they may be generated, compatibility-only, historical, or mixed-purpose. No deletion is authorized in this phase.

## Future Owner Map
- Orchestration / Scheduler -> `automation_scheduler/` temporarily, with business logic moving later
- Dashboard Data -> `automation_scheduler/streamlit_dashboard_data.py` temporarily, then `dashboard/` or `src/dashboard_data/` later
- Risk / Gating -> `src/risk/`
- Providers / Normalization -> `src/providers/` or `providers/`
- Metrics / Reporting -> `src/metrics/`
- Signals / Features -> `src/signals/` and `src/markets/`
- Backtest / Historical Replay -> `src/backtester/` and `src/storage/`
- Storage / Ledgers -> `src/storage/`
- Daily / Ops Utilities -> `scripts/` for wrappers, `automation_scheduler/` only as shell where needed
- Deprecated / Manual Review Candidates -> no canonical owner until review

## Migration Waves
- Wave 0: Guardrails already done
- Wave 1: Low-risk documentation/wrapper-only migrations
- Wave 2: Pure math and metrics extraction
- Wave 3: Risk extraction
- Wave 4: Providers extraction
- Wave 5: Signals/features extraction
- Wave 6: Backtest extraction
- Wave 7: Dashboard split
- Wave 8: automation_scheduler becomes orchestration-only
- Wave 9: deletion candidate review

## Must-Not-Delete-Yet Compliance
must_not_delete_yet is still in force. This decomposition plan does not authorize deletion.

## Unsafe Actions
- Do not delete files in this phase.
- Do not move files in this phase.
- Do not migrate source functions in this phase.
- Do not remove public functions in this phase.
- Do not add AI integration.
- Do not add ML training.
- Do not add backtest runner work.
- Do not add controlled data loader behavior.
- Do not add broker execution.
- Do not add real trade execution.
- Do not add scraper actions.

## Acceptance Results
This phase produced a decomposition plan only. It preserved the canonical owner map, the guard reports, and the daily hygiene scheduler without changing runtime behavior.

## Next Phase Recommendation
Proceed to 10K8ZFJ Provider / live_market_intelligence Decomposition Plan

This phase does not authorize deletion.
