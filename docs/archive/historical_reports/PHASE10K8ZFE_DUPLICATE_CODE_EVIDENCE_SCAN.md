# PHASE10K8ZFE Duplicate Code / Math / Metrics / Signal Evidence Scan

## Executive Summary
10K8ZFE is an evidence-only phase. No files deleted, no files moved, and no code migrated. The scan found duplicate-risk across math / core calculation, metrics / performance, signals / features, risk, providers / data adapter, backtest, storage / ledger / archive, API route, dashboard data, and orchestration / scheduler.

This phase does not authorize deletion.

## Current HEAD
Current HEAD before patch: `5fa4c59cb548474096d56e374efd00303b45390a`

## Purpose
Collect concrete ownership evidence before AI integration and before backtesting so the next phase can decide canonical owners without deleting anything prematurely.

## Scope
- Text-only repository scan
- Fresh inventory of major Python areas
- Duplicate-risk evidence gathering
- Canonical future owner candidate identification
- Report and focused test creation

## Non-Goals
- No files deleted
- No files moved
- No code migrated
- No AI optimizer implementation
- No backtest runner
- No controlled data loader
- No broker execution
- No real trade execution
- No scraper actions
- No frontend page files

## Relationship to 10K8ZF9D
10K8ZF9D completed the residual JSON cleanup flow, but the current workspace inventory must still be treated as the source of truth for this phase. The earlier cleanup summary is not sufficient for ownership decisions by itself.

## Repo Inventory
Major Python file counts:
- `automation_scheduler`: 355
- `betting_providers`: 9
- `model_governance`: 30
- `math_models`: 14
- `src`: 51
- `tests`: 344
- top-level Python entry points: 20

Current `data/` inventory at scan time:
- Total files: 97
- Total bytes: 6,872,650
- JSON: 57
- JSON bytes: 5,901,027
- JSONL: 0
- JSONL bytes: 0
- CSV: 0
- CSV bytes: 0
- Markdown: 38
- Markdown bytes: 45,927
- DB: 2
- DB bytes: 925,696
- Tracked files under `data/`: 0

The phrase `data raw JSON/JSONL/CSV cleanup remained complete` is not currently true in this workspace because the fresh inventory still shows 57 JSON files under `data/`. That is why this scan uses the inventory as the source of truth.

`.r2.env` is ignored by git and is not tracked.
No obvious credentials were found in README, report text, or source snippets sampled for this scan.

## Method
- Enumerated repository Python entry points and major folders
- Sampled short source snippets with `rg -n`
- Focused on repeated helper names and overlapping responsibilities
- Avoided large dumps and avoided destructive actions

## Duplicate-Risk Summary
- High-risk groups: 7
- Medium-risk groups: 3
- Low-risk groups: 2
- Every group below is marked `duplicate-risk`
- Every group below has a `canonical future owner` candidate
- Every group below is marked `must_not_delete_yet: yes`

## Math / Core Calculation Evidence
- Group: odds / vig / EV math overlap. Files: `src/core/math_utils.py`, `automation_scheduler/odds_math.py`, `market_pricing.py`, `betting_providers/normalization.py`, `model_probability.py`. Matching symbols: `american_to_decimal`, `american_to_implied_probability`, `remove_two_way_vig`, `no_vig_consensus_probability`, `calculate_ev`, `normalize_probability`. Risk: high. Why duplicate-risk: the same odds conversion, vig removal, EV, and probability normalization logic appears in multiple modules. Canonical future owner: `src/core/math_utils.py`. `must_not_delete_yet: yes`. Confidence: high.
- Group: CLV / line-movement math overlap. Files: `src/core/clv.py`, `automation_scheduler/clv_tracker.py`, `market_pricing.py`, `historical_line_movement.py`. Matching symbols: `calculate_clv_percent`, `calculate_clv_for_american_odds`, `opening_vs_current_clv_implied_change_pct`, `steam_move_from_implied_series`, `closing_line_value_pct`. Risk: medium. Why duplicate-risk: the same CLV and line-movement ideas are expressed in both core math helpers and tracker/report modules. Canonical future owner: `src/core/clv.py`. `must_not_delete_yet: yes`. Confidence: medium.

## Metrics / Performance Evidence
- Group: performance and CLV metrics overlap. Files: `automation_scheduler/performance_metrics.py`, `automation_scheduler/clv_tracker.py`, `automation_scheduler/strategy_performance_ledger.py`, `automation_scheduler/field_scorecard.py`, `model_governance/model_validation_report.py`. Matching symbols: `calculate_performance_metrics`, `summarize_clv_by_model`, `summarize_clv_by_market`, `append_strategy_performance_record`, `build_field_scorecard`, `build_model_validation_report`. Risk: medium. Why duplicate-risk: several modules summarize returns, CLV, drawdown, ROI, and readiness with different output shapes. Canonical future owner: `automation_scheduler/performance_metrics.py`. `must_not_delete_yet: yes`. Confidence: medium.

## Signals / Features Evidence
- Group: feature and signal definition overlap. Files: `automation_scheduler/feature_ablation_lab.py`, `automation_scheduler/derived_feature_planner.py`, `automation_scheduler/technical_signal_fields.py`, `automation_scheduler/representation_feature_builder.py`, `automation_scheduler/sport_feature_packs.py`, `automation_scheduler/market_feature_packs.py`, `automation_scheduler/historical_line_movement.py`, `automation_scheduler/asof_line_movement_query.py`, `automation_scheduler/synthetic_line_movement_sandbox.py`. Matching symbols: `get_ablation_field_groups_for_sport`, `plan_derived_features`, `technical_fields_for_market`, `build_representation_vector`, `get_sport_feature_pack`, `get_market_feature_pack`, `calculate_line_volatility_summary`, `build_asof_line_movement_query_snapshot`, `build_synthetic_line_movement_rows`. Risk: high. Why duplicate-risk: feature lists, signal labels, line-movement fields, and derived feature logic overlap across multiple modules and dashboard helpers. Canonical future owner: `automation_scheduler/sport_feature_packs.py` and `automation_scheduler/market_feature_packs.py` for feature definitions, with `automation_scheduler/feature_ablation_lab.py` as the ablation executor. `must_not_delete_yet: yes`. Confidence: high.

## Risk Evidence
- Group: execution risk gate overlap. Files: `automation_scheduler/risk_limit_guard.py`, `automation_scheduler/drawdown_controls.py`, `automation_scheduler/exposure_limits.py`, `automation_scheduler/budget_gates.py`, `automation_scheduler/hard_gate_policy.py`, `automation_scheduler/risk_of_ruin.py`, `automation_scheduler/session_risk_rules.py`, `automation_scheduler/small_account_strategy.py`, `model_governance/risk_gate.py`, `model_governance/kelly_gate.py`. Matching symbols: `evaluate_risk_limits`, `apply_drawdown_controls`, `cap_single_bet_exposure`, `build_budget_gate`, `evaluate_hard_gates`, `evaluate_risk_of_ruin`, `evaluate_session_risk`, `calculate_risk_reward`, `evaluate_risk_gate`, `evaluate_kelly_gate`. Risk: high. Why duplicate-risk: bankroll sizing, drawdown control, exposure caps, Kelly sizing, and hard gates are split across multiple modules with overlapping gating semantics. Canonical future owner: `automation_scheduler/hard_gate_policy.py` for final execution gating and `automation_scheduler/risk_limit_guard.py` for raw limits. `must_not_delete_yet: yes`. Confidence: high.

## Providers / Data Adapter Evidence
- Group: provider adapters and normalization overlap. Files: `betting_providers/base.py`, `betting_providers/provider_router.py`, `betting_providers/normalization.py`, `betting_providers/the_odds_api.py`, `betting_providers/sharp_api.py`, `betting_providers/kalshi_api.py`, `automation_scheduler/provider_adapter_base.py`, `automation_scheduler/provider_health.py`, `automation_scheduler/provider_payload_validator.py`, `automation_scheduler/provider_normalization_contract.py`, `automation_scheduler/provider_registry.py`, `automation_scheduler/sharp_sportsbook_adapter.py`, `automation_scheduler/sportsbook_odds_provider.py`, `automation_scheduler/sportsbook_adapter_contract.py`, `kalshi_client.py`. Matching symbols: `ProviderAdapter`, `ProviderRouter`, `american_to_decimal`, `normalize_sportsbook_event`, `normalize_provider_payload`, `validate_provider_payload`, `compact_provider_health`, `SharpSportsbookAdapter`, `get_kalshi_market_snapshot`. Risk: high. Why duplicate-risk: provider wrappers, payload normalization, health summaries, and routing exist in both `betting_providers/` and `automation_scheduler/`. Canonical future owner candidate: `automation_scheduler/provider_normalization_contract.py` for schema normalization and `betting_providers/provider_router.py` for provider dispatch. `must_not_delete_yet: yes`. Confidence: medium.

## Backtest Evidence
- Group: backtest engine split. Files: `src/core/backtester.py`, `automation_scheduler/backtesting_engine.py`, `automation_scheduler/backtest_dataset_builder.py`, `automation_scheduler/historical_backtest_bridge.py`, `automation_scheduler/backtest_strategy_bankroll.py`, `automation_scheduler/backtest_strategy_profiles.py`, `automation_scheduler/historical_odds_sqlite.py`, `model_governance/backtest_gate.py`, `src/services/model_backtest_service.py`. Matching symbols: `run_walk_forward_backtest`, `run_backtest`, `build_canonical_backtest_dataset`, `run_sqlite_historical_backtest`, `simulate_backtest_bankroll`, `build_strategy_config_for_row`, `upsert_canonical_historical_odds_rows`, `evaluate_backtest_gate`, `run_model_backtest`. Risk: high. Why duplicate-risk: there is a canonical model backtester in `src/core` and a separate historical replay / bankroll / dataset stack in `automation_scheduler/`. Canonical future owner candidate: `src/core/backtester.py` for the model-training path and `automation_scheduler/backtesting_engine.py` for the historical replay path. `must_not_delete_yet: yes`. Confidence: high.

## Storage / Ledger / Archive Evidence
- Group: storage, ledgers, and archives overlap. Files: `automation_scheduler/outcome_store.py`, `automation_scheduler/paper_trade_ledger.py`, `automation_scheduler/paper_decision_ledger.py`, `automation_scheduler/experiment_history_store.py`, `automation_scheduler/snapshot_store.py`, `automation_scheduler/audit_ledger.py`, `automation_scheduler/historical_odds_sqlite.py`, `model_governance/governance_audit_log.py`. Matching symbols: `load_outcome_records`, `create_paper_entry`, `create_paper_decision_record`, `save_experiment_history_run`, `save_snapshot`, `append_security_event`, `upsert_canonical_historical_odds_rows`, `write_governance_audit_record`. Risk: medium. Why duplicate-risk: multiple persistence layers record similar run/result/history/audit data with separate JSON and SQLite surfaces. Canonical future owner candidate: `automation_scheduler/outcome_store.py` for outcomes, `automation_scheduler/historical_odds_sqlite.py` for canonical odds storage, and `automation_scheduler/experiment_history_store.py` for experiments. `must_not_delete_yet: yes`. Confidence: medium.

## API Route Evidence
- Group: route wiring overlap. Files: `main.py`, `api_server.py`, `src/api/system_routes.py`, `src/api/provider_status_routes.py`, `src/api/performance_routes.py`, `src/api/model_backtest_routes.py`, `src/api/debug_routes.py`. Matching symbols: `FastAPI`, `register_system_routes`, `register_provider_status_routes`, `register_performance_routes`, `register_model_backtest_routes`, `register_debug_routes`. Risk: low. Why duplicate-risk: `api_server.py` is a proxy for deployment, while route registration happens in `main.py` and route modules in `src/api/`. Canonical future owner candidate: `src/api/*` for endpoints, `main.py` for app assembly. `must_not_delete_yet: yes`. Confidence: high.

## Dashboard Data Evidence
- Group: dashboard transforms and summaries overlap. Files: `streamlit_app.py`, `automation_scheduler/streamlit_dashboard_data.py`, `automation_scheduler/report_writer.py`. Matching symbols: `build_readiness_display_payload`, `build_readiness_display_rows`, `build_market_metric_display_payload`, `summarize_backtest_result`, `generate_latest_dashboard_outputs`, `load_dashboard_snapshot`, `render_dashboard_markdown`, `write_report`, `write_compact_report`. Risk: high. Why duplicate-risk: the dashboard helper module performs summary-building, file I/O, feature readiness checks, and backtest presentation all in one place, while `streamlit_app.py` repeats display-side transformations. Canonical future owner candidate: `automation_scheduler/streamlit_dashboard_data.py`. `must_not_delete_yet: yes`. Confidence: high.

## Orchestration / Scheduler Evidence
- Group: orchestration and scheduled workflow overlap. Files: `automation_scheduler/scheduler_runner.py`, `automation_scheduler/collector_scheduled_runner.py`, `automation_scheduler/ops_workflow.py`, `automation_scheduler/calibration_collector.py`, `automation_scheduler/deepseek_daily_report.py`, `automation_scheduler/data_source_registry.py`, `automation_scheduler/execution_gatekeeper.py`, `automation_scheduler/strategy_router.py`. Matching symbols: `run_scheduler_once`, `run_scheduled_collector_cycle`, `run_ops_check`, `run_collector_cycle`, `write_daily_report`, `build_registry_report`, `evaluate_future_execution_eligibility`, `route_strategies`. Risk: medium. Why duplicate-risk: several orchestration modules own scheduling, report writing, policy checks, and collection workflows with overlapping safety flags and execution gating. Canonical future owner candidate: `automation_scheduler/scheduler_runner.py` for orchestration and `automation_scheduler/ops_workflow.py` for system checks. `must_not_delete_yet: yes`. Confidence: medium.

## Must-Not-Delete-Yet List
- `src/core/math_utils.py`
- `src/core/clv.py`
- `src/core/backtester.py`
- `automation_scheduler/odds_math.py`
- `automation_scheduler/performance_metrics.py`
- `automation_scheduler/feature_ablation_lab.py`
- `automation_scheduler/sport_feature_packs.py`
- `automation_scheduler/market_feature_packs.py`
- `automation_scheduler/risk_limit_guard.py`
- `automation_scheduler/hard_gate_policy.py`
- `automation_scheduler/provider_normalization_contract.py`
- `betting_providers/provider_router.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/historical_backtest_bridge.py`
- `automation_scheduler/streamlit_dashboard_data.py`
- `streamlit_app.py`
- `automation_scheduler/outcome_store.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `main.py`
- `api_server.py`
- `automation_scheduler/scheduler_runner.py`
- `automation_scheduler/ops_workflow.py`

## Likely Canonical Owner Candidates
- `src/core/math_utils.py`
- `src/core/clv.py`
- `src/core/backtester.py`
- `automation_scheduler/performance_metrics.py`
- `automation_scheduler/sport_feature_packs.py`
- `automation_scheduler/market_feature_packs.py`
- `automation_scheduler/hard_gate_policy.py`
- `automation_scheduler/risk_limit_guard.py`
- `automation_scheduler/provider_normalization_contract.py`
- `betting_providers/provider_router.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/outcome_store.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `src/api/system_routes.py`
- `automation_scheduler/streamlit_dashboard_data.py`
- `automation_scheduler/scheduler_runner.py`

## High-Risk Duplicate Groups
- Odds / probability / vig math overlap
- Feature and signal definition overlap
- Execution risk gate overlap
- Provider adapters and normalization overlap
- Backtest engine split
- Dashboard transforms and summaries overlap
- CLV / line-movement math overlap

## Medium-Risk Duplicate Groups
- Performance and CLV metrics overlap
- Storage, ledgers, and archives overlap
- Orchestration and scheduled workflow overlap

## Low-Risk Duplicate Groups
- Route wiring overlap
- ASGI proxy / model backtest service wrappers

## Safe Next Actions
- Use this scan as the input to the next canonical-owner decision phase.
- Centralize ownership in the candidate modules above without deleting any file yet.
- Keep the evidence in place until a deliberate migration plan exists.
- Continue to treat the inventory as the source of truth for any future cleanup decision.

## Unsafe Actions
- Do not delete files in this phase.
- Do not move files in this phase.
- Do not migrate code in this phase.
- Do not add AI optimizer implementation yet.
- Do not add backtest runner changes yet.
- Do not add controlled data loader behavior yet.
- Do not add broker execution.
- Do not add real trade execution.
- Do not add scraper actions.
- Do not add frontend page files.

## Acceptance Results
- evidence-only phase: yes
- no files deleted: yes
- no files moved: yes
- no code migrated: yes
- duplicate categories covered: yes
- duplicate-risk: yes
- canonical future owner: yes
- must_not_delete_yet: yes
- source code was preserved
- tests/fixtures were preserved
- manifests were preserved
- archives were preserved
- tracked files were preserved
- no credentials committed
- no secrets printed
- no broker execution
- no real trade execution
- no scraper actions
- no controlled data loader
- no backtest runner
- no AI optimizer implementation

## Next Phase Recommendation
Proceed to 10K8ZFF Canonical Owner Decision Report.
