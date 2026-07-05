# DUPLICATE_LOGIC_EVIDENCE_REPORT_AFTER_10K8ZFM

## Executive Summary
The repo still contains several overlapping implementations that are safe to observe but not to delete yet. The highest-risk duplication is in math/pricing, provider adapters, backtest scaffolding, dashboard data helpers, and orchestration. The canonical future owner map from 10K8ZFF still applies:
- pure math -> `src/core/`
- risk -> `src/risk/`
- providers -> `src/providers/`
- metrics -> `src/metrics/`
- signals -> `src/signals/` and `src/markets/`
- backtest -> `src/backtester/`
- storage -> `src/storage/`
- API -> `src/api/`

This report is evidence-only. It does not authorize deletion.

## Current HEAD
`9402a91` (`docs: plan test suite cleanup`)

## Duplicate-Risk Summary

| Group | Category | Files involved | Matching symbols / keywords | Risk | Canonical future owner | must_not_delete_yet | Recommended next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Math / Core Calculation | math / core calculation | `src/core/math_utils.py`, `src/core/clv.py`, `automation_scheduler/odds_math.py`, `automation_scheduler/no_vig_pricing.py`, `betting_providers/normalization.py`, `automation_scheduler/sharp_sportsbook_adapter.py`, `market_pricing.py`, `quant_engine.py` | `american_to_decimal`, `decimal_to_american`, `implied_probability_from_*`, `remove_two_way_vig`, `calculate_ev`, `calculate_clv*` | high | `src/core/` | yes | Keep canonical math in `src/core`; leave wrappers in place until behavior-equivalence tests are broader |
| Metrics / Performance | metrics / performance | `automation_scheduler/performance_metrics.py`, `automation_scheduler/model_performance_report.py`, `automation_scheduler/field_scorecard.py`, `automation_scheduler/clv_tracker.py`, `research_engine/evidence_scorecard.py`, `model_governance/model_validation_report.py` | `calculate_performance_metrics`, `build_compact_performance_report`, `build_field_scorecard`, `calculate_positive_clv_rate`, evidence/scorecard keywords | medium-high | `src/metrics/` | yes | Consolidate metric semantics later; keep current reports and scorecards stable |
| Signals / Features | signals / features | `automation_scheduler/feature_ablation_lab.py`, `automation_scheduler/sport_feature_packs.py`, `automation_scheduler/market_feature_packs.py`, `automation_scheduler/source_event_link_resolver.py`, `automation_scheduler/historical_line_movement.py`, `automation_scheduler/asof_line_movement_query.py`, `automation_scheduler/synthetic_line_movement_sandbox.py`, `automation_scheduler/line_movement_data_quality_dashboard.py`, `automation_scheduler/model_data_field_catalog.py` | feature pack / ablation / line-movement / readiness / data-quality terms | medium-high | `src/signals/` + `src/markets/` | yes | Keep orchestration in scheduler for now; move signal math only after canonical data contracts stabilize |
| Risk | risk | `risk_engine.py`, `automation_scheduler/risk_limit_guard.py`, `automation_scheduler/hard_gate_policy.py`, `automation_scheduler/budget_gates.py`, `automation_scheduler/drawdown_controls.py`, `automation_scheduler/exposure_limits.py`, `automation_scheduler/liquidity_risk.py`, `automation_scheduler/balance_sheet_risk.py`, `automation_scheduler/kelly_staking.py`, `model_governance/risk_gate.py` | Kelly, drawdown, exposure, ruin, gates, sizing | high | `src/risk/` | yes | Freeze semantics first; later extract pure policy/math into `src/risk` |
| Providers / Data Adapter | providers / data adapter | `betting_providers/*`, `providers/*`, `automation_scheduler/provider_*`, `automation_scheduler/kalshi_*`, `automation_scheduler/sharp_sportsbook_adapter.py`, `src/services/enrichment_service.py`, `src/api/provider_status_routes.py`, `src/api/model_card_service.py` | provider router, normalization, health, status, sportsbook, Kalshi, sharp, enrichment | high | `src/providers/` | yes | Preserve compatibility wrappers; move adapter ownership later, not now |
| Backtest | backtest | `src/core/backtester.py`, `automation_scheduler/backtesting_engine.py`, `automation_scheduler/backtest_dataset_builder.py`, `automation_scheduler/historical_backtest_bridge.py`, `automation_scheduler/historical_odds_sqlite.py`, `src/services/model_backtest_service.py`, `src/api/model_backtest_routes.py` | backtest, replay, bankroll, leakage, calibration, historical bridge | high | `src/backtester/` | yes | Keep existing flow as-is; any migration must prove identical outputs first |
| Storage / Ledger / Archive | storage / ledger / archive | `src/storage/archive_manifest.py`, `src/storage/r2_archive_adapter.py`, `scripts/daily_data_hygiene.py`, `scripts/r2_archive_pipeline.py`, `automation_scheduler/outcome_store.py`, `automation_scheduler/paper_trade_ledger.py`, `automation_scheduler/experiment_history_store.py`, `automation_scheduler/audit_ledger.py`, `automation_scheduler/historical_odds_sqlite.py`, `research/market_research_store.py` | manifest, archive, ledger, store, sqlite, cleanup, verify, upload | medium | `src/storage/` | yes | Keep archive contracts centralized; consolidate storage semantics before any retirement |
| API Route | API route | `main.py`, `api_server.py`, `src/api/*` | app assembly, proxy, route registration, endpoint groups | medium | `src/api/` | yes | Keep `api_server.py` as proxy only; avoid route logic outside `src/api` |
| Dashboard Data | dashboard data | `streamlit_app.py`, `automation_scheduler/streamlit_dashboard_data.py`, `tests/test_streamlit_dashboard_data.py` | dashboard-data, readiness, feature groups, baseline, scenario, risk preset | high | `streamlit_app.py` shell + future `dashboard/` / `src/dashboard_data` | yes | Keep `streamlit_app.py` as shell; move data helpers only after ownership is frozen |
| Orchestration / Scheduler | orchestration / scheduler | `automation_scheduler/ops_workflow.py`, `automation_scheduler/scheduler_runner.py`, `automation_scheduler/collector_scheduled_runner.py`, `scripts/ops_check.py`, `scripts/daily_data_hygiene.py` | runner, workflow, cron, check, schedule, cleanup, health | high | `automation_scheduler/` temporarily, `scripts/` for ops wrappers | yes | Keep orchestration in place for now; do not delete before canonical owners are stable |
| Test helpers / config / env handling | test helpers / config / env handling | `tests/support/action_imports.py`, `tests/conftest.py`, `.gitignore`, `.r2.env`, `config.py`, `logger_setup.py` | env, token, secret, credential, test export/import helpers | medium | n/a | yes | Keep safety utilities and local-only config untouched until later review |

## Math / Core Calculation Evidence
- `src/core/math_utils.py` is the canonical pure math owner and includes American/decimal conversion, implied probability, break-even probability, vig stripping, and EV support.
- `automation_scheduler/odds_math.py` reimplements many of the same conversion and EV functions.
- `automation_scheduler/no_vig_pricing.py` duplicates no-vig and fair-odds logic.
- `betting_providers/normalization.py` also reuses math conversions.
- `automation_scheduler/sharp_sportsbook_adapter.py` keeps local copies of the conversion helpers even though it imports canonical math helpers.
- `market_pricing.py` and `quant_engine.py` are additional legacy math surfaces that should be reviewed against `src/core`.

## Metrics / Performance Evidence
- `automation_scheduler/performance_metrics.py` computes ROI, drawdown, volatility, and risk-adjusted return.
- `automation_scheduler/model_performance_report.py` packages reporting payloads.
- `automation_scheduler/field_scorecard.py` scores candidate fields using risk/reward heuristics.
- `automation_scheduler/clv_tracker.py` summarizes CLV as a performance metric.
- `research_engine/evidence_scorecard.py` and `model_governance/model_validation_report.py` are adjacent evidence/validation surfaces and may duplicate reporting semantics later.

## Signals / Features Evidence
- `automation_scheduler/feature_ablation_lab.py`, `sport_feature_packs.py`, and `market_feature_packs.py` all shape feature-group logic.
- `source_event_link_resolver.py` and `historical_line_movement.py` both touch event/line relationship shaping.
- `asof_line_movement_query.py` and `synthetic_line_movement_sandbox.py` also overlap on movement feature generation and analysis.
- `model_data_field_catalog.py` and `line_movement_data_quality_dashboard.py` are display/selection layers that should stay aligned with canonical feature definitions.

## Risk Evidence
- `risk_engine.py` remains a broad legacy surface.
- `automation_scheduler/risk_limit_guard.py`, `hard_gate_policy.py`, `budget_gates.py`, `drawdown_controls.py`, `exposure_limits.py`, `liquidity_risk.py`, `balance_sheet_risk.py`, and `kelly_staking.py` all express overlapping risk policy ideas.
- The risk duplication is high because the same concepts show up in both runtime code and dashboard/test fixtures.

## Providers / Data Adapter Evidence
- `betting_providers/` is the active adapter layer.
- `providers/` is a legacy compatibility shell for screenshot/full-board enrichment workflows.
- `automation_scheduler/provider_*` files hold contracts, health, normalization, secret policy, and registry logic.
- `automation_scheduler/kalshi_*` and `automation_scheduler/sharp_sportsbook_adapter.py` are live-adapter-capable and must not be retired until `src/providers/` exists.
- `src/services/enrichment_service.py` still routes through `providers`, which is the clearest sign that provider ownership is not yet fully canonical.

## Backtest Evidence
- `src/core/backtester.py` is the pure canonical backtest owner today.
- `automation_scheduler/backtesting_engine.py` still holds legacy scaffold, report, and replay logic.
- `automation_scheduler/backtest_dataset_builder.py` and `automation_scheduler/historical_backtest_bridge.py` duplicate historical dataset prep and replay plumbing.
- `src/services/model_backtest_service.py` is a thin service wrapper but still ties product behavior to the current backtest contract.

## Storage / Ledger / Archive Evidence
- `src/storage/archive_manifest.py` owns archive ID, path, batch ID, upload/verify/deletion gates, and manifest serialization.
- `src/storage/r2_archive_adapter.py` owns the R2 client interface.
- `scripts/daily_data_hygiene.py` and `scripts/r2_archive_pipeline.py` are operational wrappers around the storage contract.
- `automation_scheduler/outcome_store.py`, `paper_trade_ledger.py`, `experiment_history_store.py`, and `historical_odds_sqlite.py` show that storage semantics are still spread across scheduler modules.

## API Route Evidence
- `main.py` is still the app assembly surface.
- `api_server.py` is a deployment/test proxy only.
- `src/api/provider_status_routes.py`, `market_metadata_routes.py`, and `market_utility_routes.py` are the clearest route-ownership examples.
- The route layer is not yet fully isolated from scheduler helpers.

## Dashboard Data Evidence
- `streamlit_app.py` is the UI shell.
- `automation_scheduler/streamlit_dashboard_data.py` is still the data-helper owner.
- The dashboard-data helper file is large and touches readiness, backtest summaries, risk presets, scenario modes, field catalogs, and historical views. That makes it a high duplicate-risk surface.

## Orchestration / Scheduler Evidence
- `automation_scheduler/ops_workflow.py` and `automation_scheduler/scheduler_runner.py` are the densest orchestration hubs.
- `collector_scheduled_runner.py` is a cron-token gated operational helper.
- `scripts/ops_check.py` is the external operational wrapper.
- `scripts/daily_data_hygiene.py` is the daily cleanup orchestrator and should stay a wrapper around storage contracts, not a data owner.

## Unsafe Actions
- Do not delete anything in this phase.
- Do not migrate source functions in this phase.
- Do not rewrite math, provider, risk, backtest, or scheduler behavior in this phase.
- Do not mark these groups as safe for deletion just because they have duplicates. They are still live dependencies.

## Conclusion
The repo still has multiple same-purpose implementations, but the safe approach is still wrapper-first and canonical-owner-first. Deletion is not authorized here; the next useful step is controlled consolidation only after dependency migration, wrapper coverage, and behavior-equivalence proof.
