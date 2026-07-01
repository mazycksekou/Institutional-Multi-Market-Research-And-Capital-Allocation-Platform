# Repository Discovery Entrypoints

## `api_server.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `main.py`

- Ownership: `root/non-src python`
- Imports: `src.analytics.model_governance, src.analytics.model_governance.model_inventory, src.api.automation_core_routes, src.api.automation_data_source_routes, src.api.automation_deepseek_routes, src.api.automation_institutional_lab_routes, src.api.automation_manifold_routes, src.api.automation_review_outcomes_routes, src.api.automation_run_once_routes, src.api.automation_small_account_routes, src.api.automation_sport_impact_routes, src.api.bet_csv_routes, src.api.betting_action_routes, src.api.betting_metadata_routes, src.api.debug_routes, src.api.governance_routes, src.api.market_metadata_routes, src.api.market_utility_routes, src.api.model_backtest_routes, src.api.model_card_service, src.api.performance_routes, src.api.provider_status_routes, src.api.quant_routes, src.api.schemas.automation, src.api.schemas.bet_csv, src.api.schemas.performance, src.api.schemas.quant, src.api.stock_analysis_routes, src.api.system_routes, src.core.market_pricing, src.core.model_probability, src.core.quant_engine, src.market_intelligence.multi_sport_model_registry, src.providers.compat, src.providers.provider_router, src.services.action_betting_service, src.services.automation_scheduler_facade, src.services.bet_csv_service, src.services.bet_decision_engine, src.services.bet_log, src.services.screenshot_intake`
- Package dependencies: `analytics, api, core, market intelligence, providers, services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `scripts/README_live_tests.md`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/analyze_json_data.py`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `scripts/backfill_open_sports_history.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/check_all.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/check_cron.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/check_data_availability_tiers.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/check_derived_features.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/check_kalshi_readonly_ready.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/check_live_payload_contract.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/check_local.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/check_local_sports_history.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/check_nfl_open_data_sources.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/check_open_sports_history_sources.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/check_outcome_reconcile.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/check_render.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/daily_data_hygiene.py`

- Ownership: `scripts/ops`
- Imports: `scripts.r2_archive_pipeline, src.storage.archive_manifest`
- Package dependencies: `scripts/ops, src/unknown`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `scripts/deepseek_data_pull_check.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/dry_run_import_kalshi_outcomes.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/export_kalshi_local_outcomes.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `scripts/import_open_sports_history.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/init_sports_master_db.py`

- Ownership: `scripts/ops`
- Imports: `src.core.math_utils`
- Package dependencies: `core`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/install_json_audit_scheduled_task.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_afl_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_all_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_badminton_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_basketball_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_checks.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_cod_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_combat_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_core_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_cricket_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_cs2_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_darts_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_dota2_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_f1_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_formula_e_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_golf_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_handball_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_helpers.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_indycar_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_lacrosse_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_lol_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_mlb_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_motogp_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_nascar_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_nba_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_ncaab_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_ncaaf_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_ncaawb_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_nfl_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_nhl_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_overwatch_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_payloads.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `scripts/live_pickleball_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_rugby_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_snooker_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_soccer_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_sport_template.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_table_tennis_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_tennis_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_valorant_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_volleyball_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_water_polo_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/live_wnba_smoke.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/ops_check.py`

- Ownership: `scripts/ops`
- Imports: `src.services.ops_workflow, src.services.repo_inventory`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `scripts/persist_import_kalshi_outcomes.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/r2_archive_pipeline.py`

- Ownership: `scripts/ops`
- Imports: `src.storage.archive_manifest, src.storage.r2_archive_adapter`
- Package dependencies: `src/unknown`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/review_json_audit_with_deepseek.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `scripts/run_daily_data_hygiene.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/run_json_audit_pipeline.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `scripts/run_nfl_coaching_import.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=True, live=False, credential=False`
- Likely mode: `active-external-boundary-looking`

## `scripts/run_nfl_cutoff_features.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/run_nfl_open_data_backfill.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/run_nfl_open_data_feature_readiness.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/run_nfl_open_data_field_catalog.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/run_nfl_partial_backfills_v2.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/run_nfl_pattern_lab.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/run_nfl_pattern_validation.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/run_scheduler_health_check.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `scripts/run_scheduler_once.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/run_tests.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `scripts/setup_dev.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `scripts/smoke_test.py`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=True, live=False, credential=True`
- Likely mode: `active-external-boundary-looking`

## `scripts/uninstall_json_audit_scheduled_task.ps1`

- Ownership: `scripts/ops`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/ai/deepseek_data_pull_check.py`

- Ownership: `ai`
- Imports: `src.data, src.data.data_paths, src.market_intelligence.prediction_market_outcome_candidates, src.providers.kalshi_readonly_readiness, src.services.scheduler_config`
- Package dependencies: `data, market intelligence, providers, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/analytics/calibration_collector.py`

- Ownership: `analytics`
- Imports: `src.ai.deepseek_reviewer, src.analytics.calibration, src.analytics.review_queue, src.brokerage.paper_decision_ledger, src.data.data_paths, src.services.outcome_store, src.services.prediction_market_runtime_bridge, src.services.scheduler_config, src.services.scheduler_runner, src.services.settlement_service`
- Package dependencies: `ai, analytics, brokerage, data, services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/analytics/derived_feature_backfill_report.py`

- Ownership: `analytics`
- Imports: `src.data, src.data.data_paths, src.market_intelligence.nfl_coaching_feature_builders, src.market_intelligence.nfl_cutoff_week_features, src.providers.nfl_open_data_feature_builders, src.services.scheduler_config`
- Package dependencies: `data, market intelligence, providers, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/api/__init__.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/automation_core_routes.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/automation_data_source_routes.py`

- Ownership: `api`
- Imports: `src.api.schemas.automation`
- Package dependencies: `api`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/automation_deepseek_routes.py`

- Ownership: `api`
- Imports: `src.api.schemas.automation`
- Package dependencies: `api`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/automation_institutional_lab_routes.py`

- Ownership: `api`
- Imports: `src.api.schemas.automation, src.services.execution_service`
- Package dependencies: `api, services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `src/api/automation_manifold_routes.py`

- Ownership: `api`
- Imports: `src.api.schemas.automation`
- Package dependencies: `api`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/automation_review_outcomes_routes.py`

- Ownership: `api`
- Imports: `src.api.automation_security, src.api.schemas.automation`
- Package dependencies: `api`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/automation_run_once_routes.py`

- Ownership: `api`
- Imports: `src.api.schemas.automation`
- Package dependencies: `api`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/automation_security.py`

- Ownership: `api`
- Imports: `src.services.execution_support`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/api/automation_small_account_routes.py`

- Ownership: `api`
- Imports: `src.api.schemas.automation`
- Package dependencies: `api`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `src/api/automation_sport_impact_routes.py`

- Ownership: `api`
- Imports: `src.api.schemas.automation`
- Package dependencies: `api`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/bet_csv_routes.py`

- Ownership: `api`
- Imports: `src.api.schemas.bet_csv, src.services.bet_csv_service`
- Package dependencies: `api, services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/betting_action_routes.py`

- Ownership: `api`
- Imports: `src.api.schemas.betting_actions, src.services.action_betting_service`
- Package dependencies: `api, services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/betting_metadata_routes.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/debug_routes.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `src/api/governance_routes.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/market_metadata_routes.py`

- Ownership: `api`
- Imports: `src.providers.compat`
- Package dependencies: `providers`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/market_utility_routes.py`

- Ownership: `api`
- Imports: `src.core.opportunity_scanner`
- Package dependencies: `core`
- Network/live/credential signals: `network=True, live=False, credential=False`
- Likely mode: `active-external-boundary-looking`

## `src/api/model_backtest_routes.py`

- Ownership: `api`
- Imports: `src.services.model_backtest_service`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/model_card_service.py`

- Ownership: `api`
- Imports: `src.core.backtester, src.core.math_utils, src.providers.provider_router, src.sports.nba_features`
- Package dependencies: `core, providers, src/unknown`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/performance_routes.py`

- Ownership: `api`
- Imports: `src.api.schemas.performance`
- Package dependencies: `api`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `src/api/provider_status_routes.py`

- Ownership: `api`
- Imports: `src.services.automation_scheduler_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/quant_routes.py`

- Ownership: `api`
- Imports: `src.api.schemas.quant`
- Package dependencies: `api`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/schemas/__init__.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/schemas/automation.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `src/api/schemas/bet_csv.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/schemas/betting_actions.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/schemas/performance.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/schemas/quant.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/stock_analysis_routes.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/api/system_routes.py`

- Ownership: `api`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `src/market_intelligence/local_sports_history_audit.py`

- Ownership: `market intelligence`
- Imports: `src.data.data_paths, src.services.scheduler_config`
- Package dependencies: `data, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/market_intelligence/nfl_coaching_feature_builders.py`

- Ownership: `market intelligence`
- Imports: `src.data, src.data.data_paths, src.market_intelligence, src.market_intelligence.nfl_coaching_sources, src.providers.nfl_coaching_adapters, src.services.scheduler_config`
- Package dependencies: `data, market intelligence, providers, services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/market_intelligence/nfl_coaching_sources.py`

- Ownership: `market intelligence`
- Imports: `src.data, src.data.data_paths, src.services.scheduler_config`
- Package dependencies: `data, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/market_intelligence/nfl_cutoff_week_features.py`

- Ownership: `market intelligence`
- Imports: `src.data, src.data.data_paths, src.services.scheduler_config`
- Package dependencies: `data, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/providers/kalshi_readonly_readiness.py`

- Ownership: `providers`
- Imports: `src.providers.registry, src.services.prediction_market_runtime_bridge`
- Package dependencies: `providers, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/providers/nfl_coaching_adapters.py`

- Ownership: `providers`
- Imports: `src.data, src.data.data_paths, src.market_intelligence.nfl_coaching_sources, src.services.scheduler_config`
- Package dependencies: `data, market intelligence, services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/providers/nfl_open_data_adapters.py`

- Ownership: `providers`
- Imports: `src.data, src.data.data_paths, src.services.scheduler_config`
- Package dependencies: `data, services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/providers/nfl_open_data_backfill.py`

- Ownership: `providers`
- Imports: `src.data, src.data.data_paths, src.providers.nfl_open_data_adapters, src.services.scheduler_config`
- Package dependencies: `data, providers, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/providers/nfl_open_data_feature_builders.py`

- Ownership: `providers`
- Imports: `src.data, src.data.data_paths, src.services.scheduler_config`
- Package dependencies: `data, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `src/providers/nfl_open_data_feature_readiness.py`

- Ownership: `providers`
- Imports: `src.data, src.data.data_paths, src.providers.nfl_open_data_feature_builders, src.services.scheduler_config`
- Package dependencies: `data, providers, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `streamlit_app.py`

- Ownership: `dashboard/frontend`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_advanced_red_team.py`

- Ownership: `tests`
- Imports: `src.analytics.advanced_red_team_report, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- Package dependencies: `analytics, services, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_afl_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_analyze_event.py`

- Ownership: `tests`
- Imports: `src.api.schemas.betting_actions, src.services.action_betting_service`
- Package dependencies: `api, services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_backtesting_engine.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_badminton_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_balance_sheet_risk.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_bankroll_state.py`

- Ownership: `tests`
- Imports: `src.backtesting.bankroll_state`
- Package dependencies: `backtesting`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `tests/test_baseball_impact_intelligence.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.response_compactor, src.market_intelligence.sports, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_basketball_player_impact.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.basketball_player_impact, src.market_intelligence.basketball_player_impact_readiness, src.market_intelligence.response_compactor, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- Package dependencies: `market intelligence, services, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_bet_log.py`

- Ownership: `tests`
- Imports: `src.services.bet_log, tests.support.action_imports`
- Package dependencies: `services, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_broker_quality_scoring.py`

- Ownership: `tests`
- Imports: `src.services.execution_service`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_budget_gates.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_calibration_collector.py`

- Ownership: `tests`
- Imports: `src.services.prediction_market_runtime_bridge, src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_calibration_tracker.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_call_of_duty_esports_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_candlestick_pattern_detector.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_clv_tracker.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_collector_scheduled_runner.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade, tests.support.action_imports`
- Package dependencies: `services, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_college_football_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_combat_impact_intelligence.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.response_compactor, src.market_intelligence.sports, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_combat_sports_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_cricket_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_crypto_edge_lab_registry.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_cs2_esports_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_darts_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_data_availability_tiers.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_data_intelligence_stack.py`

- Ownership: `tests`
- Imports: `src.analytics.intelligence_readiness_report, src.market_intelligence.cross_asset_intelligence_router, src.market_intelligence.response_compactor, src.research, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- Package dependencies: `analytics, market intelligence, research, services, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_data_paths.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `tests/test_data_source_endpoints.py`

- Ownership: `tests`
- Imports: `src.data, tests.support.action_imports`
- Package dependencies: `data, tests`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_data_source_registry.py`

- Ownership: `tests`
- Imports: `src.data`
- Package dependencies: `data`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_data_source_research_lanes.py`

- Ownership: `tests`
- Imports: `src.data`
- Package dependencies: `data`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_deepseek_data_pull_check_contract.py`

- Ownership: `tests`
- Imports: `src.ai.deepseek_data_pull_check, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- Package dependencies: `ai, services, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_deepseek_profit_lab.py`

- Ownership: `tests`
- Imports: `src.ai.deepseek_profit_lab, src.services.streamlit_dashboard_facade`
- Package dependencies: `ai, services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_deepseek_reviewer.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_derived_feature_backfill_report.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_derived_feature_planner.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `tests/test_dota2_esports_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_drawdown_controls.py`

- Ownership: `tests`
- Imports: `src.core.drawdown_controls`
- Package dependencies: `core`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_evaluate_lines.py`

- Ownership: `tests`
- Imports: `src.core.quant_engine, src.services.bet_decision_engine`
- Package dependencies: `core, services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_exposure_limits.py`

- Ownership: `tests`
- Imports: `src.core.exposure_limits`
- Package dependencies: `core`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_extreme_randomness_diagnostics.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.response_compactor, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- Package dependencies: `market intelligence, services, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_football_impact_intelligence.py`

- Ownership: `tests`
- Imports: `src.analytics.football_impact_report, src.market_intelligence.response_compactor, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- Package dependencies: `analytics, market intelligence, services, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_formula_1_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_formula_e_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_golf_impact_intelligence.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.response_compactor, src.market_intelligence.sports, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_golf_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_handball_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_historical_replay.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_hockey_impact_intelligence.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.response_compactor, src.market_intelligence.sports, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_indycar_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_injury_weather_adapter_contract.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_institutional_audit_ledger.py`

- Ownership: `tests`
- Imports: `src.services.ledger_service`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_institutional_cross_asset_adapters.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_institutional_cross_asset_calibration.py`

- Ownership: `tests`
- Imports: `src.analytics.institutional_cross_asset_calibration`
- Package dependencies: `analytics`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_institutional_cross_asset_lab.py`

- Ownership: `tests`
- Imports: `src.core.stake_sizing_simulator, src.services.streamlit_dashboard_facade`
- Package dependencies: `core, services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_institutional_cross_asset_reports.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_institutional_cross_asset_scores.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_institutional_deepseek_review.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_institutional_execution_desk.py`

- Ownership: `tests`
- Imports: `src.services.execution_service`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_institutional_risk_engine.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_institutional_stock_pro_analyst_registry.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_kalshi_adapter_contract.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_kalshi_market_provider.py`

- Ownership: `tests`
- Imports: `src.providers.prediction_markets, src.providers.registry, src.services.prediction_market_runtime_bridge, src.services.streamlit_dashboard_facade`
- Package dependencies: `providers, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_kalshi_readonly_adapter.py`

- Ownership: `tests`
- Imports: `src.connectors.errors, src.connectors.prediction_market_data, src.providers.prediction_markets`
- Package dependencies: `providers, src/unknown`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `tests/test_kalshi_readonly_readiness_contract.py`

- Ownership: `tests`
- Imports: `src.services.prediction_market_runtime_bridge, src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_kelly_staking.py`

- Ownership: `tests`
- Imports: `src.core.kelly_staking, src.core.stake_confidence`
- Package dependencies: `core`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_lacrosse_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_league_of_legends_esports_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_liquidity_context_scoring.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_live_smoke_payload_contract.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry`
- Package dependencies: `market intelligence`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_local_sports_history_audit.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_market_state_manifold.py`

- Ownership: `tests`
- Imports: `src.analytics.manifold_calibration, src.market_intelligence.cross_asset_manifold_router, src.market_intelligence.response_compactor, src.services.execution_service, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- Package dependencies: `analytics, market intelligence, services, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_mens_college_basketball_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_mlb_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_model_input_coverage.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.model_input_coverage, src.services.streamlit_dashboard_facade`
- Package dependencies: `market intelligence, services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_model_performance_report.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_model_probability.py`

- Ownership: `tests`
- Imports: `src.core.model_probability, tests.support.action_imports`
- Package dependencies: `core, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_motogp_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_multi_sport_model_registry.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_nascar_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_ncaaf_collegefootballdata_adapter.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_news_events_adapter_contract.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_nfl_coaching_adapters.py`

- Ownership: `tests`
- Imports: `src.providers.nfl_coaching_adapters, src.services.streamlit_dashboard_facade`
- Package dependencies: `providers, services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_nfl_coaching_feature_builders.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.nfl_coaching_feature_builders, src.providers.nfl_coaching_adapters, src.services.streamlit_dashboard_facade`
- Package dependencies: `market intelligence, providers, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_nfl_coaching_sources.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_nfl_cutoff_week_features.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.nfl_cutoff_week_features`
- Package dependencies: `market intelligence`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_nfl_historical_pattern_lab.py`

- Ownership: `tests`
- Imports: `src.data, src.services.streamlit_dashboard_facade`
- Package dependencies: `data, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_nfl_historical_pattern_validation.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_nfl_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_nfl_open_data_adapters.py`

- Ownership: `tests`
- Imports: `src.providers.nfl_open_data_adapters, src.services.streamlit_dashboard_facade`
- Package dependencies: `providers, services`
- Network/live/credential signals: `network=True, live=False, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_nfl_open_data_backfill.py`

- Ownership: `tests`
- Imports: `src.providers.nfl_open_data_adapters, src.providers.nfl_open_data_backfill, src.services.streamlit_dashboard_facade`
- Package dependencies: `providers, services`
- Network/live/credential signals: `network=True, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_nfl_open_data_feature_builders.py`

- Ownership: `tests`
- Imports: `src.providers.nfl_open_data_feature_readiness, src.services.streamlit_dashboard_facade`
- Package dependencies: `providers, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_nfl_open_data_field_catalog.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_nfl_open_data_sources.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_nfl_source_exhaustion.py`

- Ownership: `tests`
- Imports: `src.data, src.services.streamlit_dashboard_facade`
- Package dependencies: `data, services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_nhl_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_open_sports_history_backfill.py`

- Ownership: `tests`
- Imports: `src.data`
- Package dependencies: `data`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_open_sports_history_derived_features.py`

- Ownership: `tests`
- Imports: `src.analytics.derived_feature_backfill_report, src.services.streamlit_dashboard_facade`
- Package dependencies: `analytics, services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_open_sports_history_import.py`

- Ownership: `tests`
- Imports: `src.data, src.services.streamlit_dashboard_facade`
- Package dependencies: `data, services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_open_sports_history_sources.py`

- Ownership: `tests`
- Imports: `src.data`
- Package dependencies: `data`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_ops_scripts_contract.py`

- Ownership: `tests`
- Imports: `none/AST not applicable`
- Package dependencies: `none`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_ops_workflow.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_outcome_import_endpoint.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade, tests.support.action_imports`
- Package dependencies: `services, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_outcome_migration.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_outcome_reconciliation.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_overwatch_esports_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_paper_trade_ledger.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_pattern_calibration.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.response_compactor, src.services.streamlit_dashboard_facade`
- Package dependencies: `market intelligence, services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_pattern_review_queue.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_performance_metrics.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_phase10k5_core_arbitrage_engine.py`

- Ownership: `tests`
- Imports: `src, src.core, src.core.math_utils, src.market_intelligence.arbitrage.two_way_arbitrage, src.research, src.research.storage, src.services.streamlit_dashboard_facade`
- Package dependencies: `core, market intelligence, research, services, src/unknown`
- Network/live/credential signals: `network=True, live=False, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_pickleball_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_player_props_adapter_contract.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_price_event.py`

- Ownership: `tests`
- Imports: `src.core.market_pricing, tests.support.action_imports`
- Package dependencies: `core, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_provider_adapter_base.py`

- Ownership: `tests`
- Imports: `src.providers.base, src.providers.contracts`
- Package dependencies: `providers`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `tests/test_provider_contracts.py`

- Ownership: `tests`
- Imports: `src.providers.contracts`
- Package dependencies: `providers`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `tests/test_provider_health.py`

- Ownership: `tests`
- Imports: `src.providers.contracts, src.providers.health`
- Package dependencies: `providers`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `tests/test_provider_normalization_contract.py`

- Ownership: `tests`
- Imports: `src.providers.normalization, src.providers.sportsbooks`
- Package dependencies: `providers`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_provider_payload_validator.py`

- Ownership: `tests`
- Imports: `src.providers.validation`
- Package dependencies: `providers`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_provider_secret_policy.py`

- Ownership: `tests`
- Imports: `src.providers.policy.secret_policy`
- Package dependencies: `providers`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `tests/test_quant_engine_foundation.py`

- Ownership: `tests`
- Imports: `src.core.quant_engine`
- Package dependencies: `core`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_risk_of_ruin.py`

- Ownership: `tests`
- Imports: `src.core.risk_of_ruin`
- Package dependencies: `core`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_rugby_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_screenshot_normalization_parity.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_security_framework.py`

- Ownership: `tests`
- Imports: `src.brokerage.readiness, src.providers.policy.write_firewall, src.services.ledger_service, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- Package dependencies: `brokerage, providers, services, tests`
- Network/live/credential signals: `network=True, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_settlement_discovery.py`

- Ownership: `tests`
- Imports: `src.services.settlement_service`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_sharp_cross_book_review_queue.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.response_compactor, src.services.streamlit_dashboard_facade`
- Package dependencies: `market intelligence, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_sharp_scheduler_flow.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_sharp_sportsbook_adapter.py`

- Ownership: `tests`
- Imports: `src.connectors.errors, src.connectors.odds_data, src.providers.sportsbooks.adapters, src.services.odds_runtime_bridge`
- Package dependencies: `providers, services, src/unknown`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `tests/test_small_account_endpoints.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_small_account_strategy.py`

- Ownership: `tests`
- Imports: `src.services.execution_service, src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=True, credential=False`
- Likely mode: `active-external-boundary-looking`

## `tests/test_snooker_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_soccer_impact_intelligence.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.response_compactor, src.market_intelligence.sports, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_soccer_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_source_quality_scoring.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_sport_analysis_endpoint.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `tests/test_sport_model_routing.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry`
- Package dependencies: `market intelligence`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `tests/test_sportsbook_adapter_contract.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_sportsbook_odds_provider.py`

- Ownership: `tests`
- Imports: `src.connectors.odds_data, src.providers.registry, src.providers.sportsbooks.contracts, src.services.odds_runtime_bridge, src.services.streamlit_dashboard_facade`
- Package dependencies: `providers, services, src/unknown`
- Network/live/credential signals: `network=False, live=False, credential=True`
- Likely mode: `credential-aware/local`

## `tests/test_stake_confidence.py`

- Ownership: `tests`
- Imports: `src.core.stake_confidence`
- Package dependencies: `core`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_stock_fundamentals_adapter_contract.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_stock_price_adapter_contract.py`

- Ownership: `tests`
- Imports: `src.services.streamlit_dashboard_facade`
- Package dependencies: `services`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_strategy_framework.py`

- Ownership: `tests`
- Imports: `src.brokerage.readiness, src.core.strategy_disagreement, src.core.strategy_promotion, src.core.strategy_score_aggregator, src.services.streamlit_dashboard_facade`
- Package dependencies: `brokerage, core, services`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_table_tennis_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_tennis_impact_intelligence.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.response_compactor, src.market_intelligence.sports, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=True, credential=True`
- Likely mode: `active-external-boundary-looking`

## `tests/test_tennis_model_activation.py`

- Ownership: `tests`
- Imports: `src.services.screenshot_intake, tests.support.action_imports`
- Package dependencies: `services, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_valorant_esports_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_volleyball_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_water_polo_model_activation.py`

- Ownership: `tests`
- Imports: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- Package dependencies: `market intelligence, tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_wnba_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`

## `tests/test_womens_college_basketball_model_activation.py`

- Ownership: `tests`
- Imports: `tests.support.action_imports`
- Package dependencies: `tests`
- Network/live/credential signals: `network=False, live=False, credential=False`
- Likely mode: `local-only/read-only-looking`
