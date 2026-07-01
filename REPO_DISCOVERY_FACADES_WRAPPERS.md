# Repository Discovery Facades and Wrappers

- Candidate count: `178`

## `api_server.py`

- Reasons: `__getattr__, importlib.import_module`
- Wraps: `main`
- Imported by: `tests/support/action_imports.py`
- Owns logic or only forwards: `forwards-only-looking`
- Canonical target: `main`

## `src/brokerage/execution.py`

- Reasons: `star re-export`
- Wraps: `src.brokerage._execution_core`
- Imported by: `none`
- Owns logic or only forwards: `forwards-only-looking`
- Canonical target: `src.brokerage._execution_core`

## `src/brokerage/execution/__init__.py`

- Reasons: `star re-export`
- Wraps: `src.brokerage._execution_core`
- Imported by: `src/brokerage/__init__.py, tests/test_phase10k8zib_unified_brokerage_boundary.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zie_execution_scheduler_wrapper_deletion.py, tests/test_phase10k8zif_execution_boundary_checkpoint.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- Owns logic or only forwards: `forwards-only-looking`
- Canonical target: `src.brokerage._execution_core`

## `src/core/market_pricing.py`

- Reasons: `star re-export`
- Wraps: `src.core.clv, src.core.math_utils, src.core.pricing`
- Imported by: `main.py, src/services/bet_decision_engine.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py, tests/test_price_event.py`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `src/core/model_probability.py`

- Reasons: `star re-export`
- Wraps: `src.core.probability`
- Imported by: `main.py, tests/test_model_probability.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.core.probability`

## `src/core/quant_engine.py`

- Reasons: `star re-export`
- Wraps: `src.core.execution, src.core.game_theory, src.core.market_impact, src.core.math_utils, src.core.portfolio, src.core.pricing, src.core.probability, src.core.risk, src.core.risk_engine`
- Imported by: `main.py, src/market_intelligence/multi_sport_model_registry.py, src/services/bet_decision_engine.py, src/services/streamlit_dashboard_data.py, tests/test_evaluate_lines.py, tests/test_phase10k8f_paper_only_fixture_evaluation_helper.py, tests/test_phase10k8g_paper_only_evaluation_readiness_adapter.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py, tests/test_quant_engine_foundation.py`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `src/core/risk_engine.py`

- Reasons: `star re-export`
- Wraps: `src.core.clv, src.core.math_utils, src.core.risk`
- Imported by: `src/core/exposure_limits.py, src/core/quant_engine.py, src/core/stake_sizing_simulator.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `src/data/line_movement.py`

- Reasons: `__getattr__`
- Wraps: `src.data, src.data.historical_odds, src.services.streamlit_dashboard_data`
- Imported by: `src/data/historical_odds.py, src/services/streamlit_dashboard_data.py, tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py, tests/test_streamlit_dashboard_data.py`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `src/market_intelligence/sports.py`

- Reasons: `__getattr__, importlib.import_module`
- Wraps: `src.market_intelligence._shared, src.market_intelligence.confidence, src.market_intelligence.flow, src.market_intelligence.liquidity, src.market_intelligence.no_trade, src.market_intelligence.positioning, src.market_intelligence.report, src.market_intelligence.risk, src.market_intelligence.targets`
- Imported by: `src/market_intelligence/__init__.py, src/market_intelligence/feature_packs.py, src/market_intelligence/manifold.py, tests/test_baseball_impact_intelligence.py, tests/test_combat_impact_intelligence.py, tests/test_golf_impact_intelligence.py, tests/test_hockey_impact_intelligence.py, tests/test_phase10k8zl3_sports_intelligence_absorption.py, tests/test_soccer_impact_intelligence.py, tests/test_tennis_impact_intelligence.py`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `src/providers/compat.py`

- Reasons: `path-name signal`
- Wraps: `none detected`
- Imported by: `main.py, src/api/market_metadata_routes.py, src/providers/__init__.py, src/providers/provider_router.py`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `src/security/__init__.py`

- Reasons: `star re-export`
- Wraps: `src.security.policy, src.security.secret_safety`
- Imported by: `tests/test_phase10k8zt_provider_security_surface_retirement.py`
- Owns logic or only forwards: `forwards-only-looking`
- Canonical target: `not singular / unknown`

## `src/services/automation_scheduler_facade.py`

- Reasons: `path-name signal, __getattr__`
- Wraps: `src.ai.deepseek_disagreement_queue, src.ai.deepseek_profit_lab, src.ai.deepseek_reviewer, src.ai.institutional_deepseek_review, src.analytics.calibration, src.analytics.calibration_collector, src.analytics.intelligence_readiness_report, src.analytics.micro_outcome_calibration, src.analytics.pattern_review_queue, src.analytics.review_queue, src.analytics.strategy_readiness_report, src.core.balance_sheet_risk, src.data, src.data.data_paths, src.market_intelligence.institutional_cross_asset_lab, src.market_intelligence.model_input_coverage, src.providers.health, src.providers.ncaaf_collegefootballdata_adapter, src.providers.registry, src.research.pattern_calibration, src.services.collector_scheduled_runner, src.services.execution_service, src.services.ledger_service, src.services.odds_runtime_bridge, src.services.outcome_store, src.services.prediction_market_runtime_bridge, src.services.runtime_shared, src.services.scheduler_config, src.services.scheduler_runner, src.services.security_readiness, src.services.settlement_service, src.services.system_health`
- Imported by: `main.py, src/api/provider_status_routes.py, src/services/ops_workflow.py, tests/test_phase10k8zga_provider_registry_runtime_blocker.py, tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py, tests/test_phase10k8zgd_final_provider_foundation_blocker_deletion.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `src/services/ops_workflow.py`

- Reasons: `importlib.import_module`
- Wraps: `src.data, src.data.data_paths, src.services, src.services.automation_scheduler_facade`
- Imported by: `scripts/ops_check.py`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `src/services/streamlit_dashboard_facade.py`

- Reasons: `path-name signal, __getattr__`
- Wraps: `src.analytics.calibration_collector, src.analytics.institutional_cross_asset_reports, src.analytics.pattern_review_queue, src.analytics.performance_metrics, src.data, src.market_intelligence.local_sports_history_audit, src.market_intelligence.nfl_coaching_sources, src.providers.nfl_coaching_adapters, src.providers.nfl_open_data_adapters, src.research.pattern_calibration`
- Imported by: `streamlit_app.py, tests/test_advanced_red_team.py, tests/test_alert_engine.py, tests/test_arbitrage_detector.py, tests/test_arbitrage_draw_market.py, tests/test_arbitrage_exchange.py, tests/test_arbitrage_prediction_market.py, tests/test_arbitrage_risk_filters.py, tests/test_arbitrage_three_way.py, tests/test_arbitrage_two_way.py, tests/test_asof_line_movement_query.py, tests/test_audit_log.py, tests/test_backtest_dataset_builder.py, tests/test_backtest_leakage.py, tests/test_backtest_regression_strategy.py, tests/test_backtest_schema.py, tests/test_backtest_strategy_bankroll.py, tests/test_backtest_strategy_profiles.py, tests/test_backtesting.py, tests/test_backtesting_engine.py, tests/test_balance_sheet_risk.py, tests/test_basketball_player_impact.py, tests/test_bookmaker_normalizer.py, tests/test_budget_gates.py, tests/test_cadence_controller.py, tests/test_calibration.py, tests/test_calibration_collector.py, tests/test_calibration_strategy_filter.py, tests/test_calibration_tracker.py, tests/test_candlestick_pattern_detector.py, tests/test_clv_tracker.py, tests/test_collector_scheduled_runner.py, tests/test_cross_book_line_comparator.py, tests/test_crypto_edge_lab_registry.py, tests/test_data_availability_tiers.py, tests/test_data_intelligence_stack.py, tests/test_data_paths.py, tests/test_deepseek_data_pull_check_contract.py, tests/test_deepseek_profit_lab.py, tests/test_deepseek_reviewer.py, tests/test_derived_feature_backfill_report.py, tests/test_derived_feature_planner.py, tests/test_ev_line_shopper.py, tests/test_experiment_history_store.py, tests/test_experiment_report_exporter.py, tests/test_extreme_randomness_diagnostics.py, tests/test_feature_ablation_lab.py, tests/test_football_impact_intelligence.py, tests/test_historical_backtest_bridge.py, tests/test_historical_data_sources.py, tests/test_historical_line_movement.py, tests/test_historical_odds_importers.py, tests/test_historical_odds_sqlite.py, tests/test_historical_replay.py, tests/test_injury_weather_adapter_contract.py, tests/test_institutional_cross_asset_adapters.py, tests/test_institutional_cross_asset_lab.py, tests/test_institutional_cross_asset_reports.py, tests/test_institutional_cross_asset_scores.py, tests/test_institutional_deepseek_review.py, tests/test_institutional_model_router.py, tests/test_institutional_risk_engine.py, tests/test_institutional_stock_pro_analyst_registry.py, tests/test_kalshi_adapter_contract.py, tests/test_kalshi_market_provider.py, tests/test_kalshi_monitor.py, tests/test_kalshi_provider_shape_contract.py, tests/test_kalshi_readonly_readiness_contract.py, tests/test_kalshi_scoring.py, tests/test_later_auto_execution_policy.py, tests/test_line_movement_data_quality_dashboard.py, tests/test_line_movement_import_contract.py, tests/test_line_movement_readiness.py, tests/test_liquidity_context_scoring.py, tests/test_liquidity_risk.py, tests/test_local_sports_history_audit.py, tests/test_market_feature_packs.py, tests/test_market_identity_resolver.py, tests/test_market_state_manifold.py, tests/test_market_structure.py, tests/test_middle_alt_line.py, tests/test_middle_ev_simulator.py, tests/test_middle_key_number.py, tests/test_middle_opportunity_detector.py, tests/test_middle_prop.py, tests/test_middle_push_corridor.py, tests/test_middle_spread.py, tests/test_middle_team_total.py, tests/test_middle_total.py, tests/test_model_input_coverage.py, tests/test_model_performance_report.py, tests/test_ncaaf_collegefootballdata_adapter.py, tests/test_news_event_monitor.py, tests/test_news_events_adapter_contract.py, tests/test_nfl_coaching_adapters.py, tests/test_nfl_coaching_feature_builders.py, tests/test_nfl_coaching_sources.py, tests/test_nfl_historical_pattern_lab.py, tests/test_nfl_historical_pattern_validation.py, tests/test_nfl_open_data_adapters.py, tests/test_nfl_open_data_backfill.py, tests/test_nfl_open_data_feature_builders.py, tests/test_nfl_open_data_field_catalog.py, tests/test_nfl_open_data_sources.py, tests/test_nfl_source_exhaustion.py, tests/test_no_vig_pricing.py, tests/test_odds_line_monitor.py, tests/test_odds_math.py, tests/test_open_sports_history_derived_features.py, tests/test_open_sports_history_import.py, tests/test_opportunity_scoring.py, tests/test_ops_workflow.py, tests/test_outcome_import_endpoint.py, tests/test_outcome_migration.py, tests/test_outcome_reconciliation.py, tests/test_outcome_store.py, tests/test_paper_decision_ledger.py, tests/test_paper_trade_ledger.py, tests/test_pattern_calibration.py, tests/test_pattern_review_queue.py, tests/test_performance_metrics.py, tests/test_phase10k5_core_arbitrage_engine.py, tests/test_phase10k8c_paper_only_fixture_validation_helper.py, tests/test_phase10k8d_paper_only_fixture_readiness_payload_adapter.py, tests/test_phase10k8f_paper_only_fixture_evaluation_helper.py, tests/test_phase10k8g_paper_only_evaluation_readiness_adapter.py, tests/test_phase10k8m_strict_model_field_baseline_by_market_and_sport.py, tests/test_phase10k8n_controlled_field_catalog_ui_review.py, tests/test_phase10k8o_dedicated_0dte_paper_fixture_template.py, tests/test_phase10k8p_dedicated_0dte_fixture_validation_adapter.py, tests/test_phase10k8q_dedicated_0dte_validation_readiness_payload.py, tests/test_phase10k8s_dedicated_0dte_paper_evaluation_adapter.py, tests/test_phase10k8u_dedicated_0dte_evaluation_ui.py, tests/test_phase10k8v_full_0dte_paper_pipeline_adapter.py, tests/test_phase10k8y_0dte_prediction_testing_readiness_review.py, tests/test_phase10k8za_0dte_data_field_formula_coverage_audit.py, tests/test_phase10k8zb_0dte_field_formula_gap_patch.py, tests/test_phase10k8ze_institutional_market_metric_catalog.py, tests/test_phase10k8zfg_safe_migration_batch_1.py, tests/test_phase10k8zl6_market_intelligence_runtime_test_redirection.py, tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py, tests/test_player_prop_monitor.py, tests/test_player_props_adapter_contract.py, tests/test_report_writer.py, tests/test_response_compactor.py, tests/test_review_queue.py, tests/test_run_context.py, tests/test_scheduler_config.py, tests/test_scheduler_runner.py, tests/test_security_framework.py, tests/test_sharp_cross_book_review_queue.py, tests/test_sharp_scheduler_flow.py, tests/test_small_account_strategy.py, tests/test_snapshot_store.py, tests/test_source_event_link_resolver.py, tests/test_source_quality_scoring.py, tests/test_sport_feature_packs.py, tests/test_sportsbook_adapter_contract.py, tests/test_sportsbook_odds_provider.py, tests/test_stock_fundamentals_adapter_contract.py, tests/test_stock_monitor.py, tests/test_stock_price_adapter_contract.py, tests/test_strategy_framework.py, tests/test_streamlit_dashboard_data.py, tests/test_system_health.py`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/conftest.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `forwards-only-looking`
- Canonical target: `not singular / unknown`

## `tests/support/action_imports.py`

- Reasons: `__getattr__, importlib.import_module`
- Wraps: `api_server, src.api.schemas`
- Imported by: `tests/test_advanced_red_team.py, tests/test_afl_model_activation.py, tests/test_automation_scheduler_endpoints.py, tests/test_badminton_model_activation.py, tests/test_baseball_impact_intelligence.py, tests/test_basketball_player_impact.py, tests/test_bet_log.py, tests/test_call_of_duty_esports_model_activation.py, tests/test_collector_scheduled_runner.py, tests/test_college_football_model_activation.py, tests/test_combat_impact_intelligence.py, tests/test_combat_sports_model_activation.py, tests/test_cricket_model_activation.py, tests/test_cs2_esports_model_activation.py, tests/test_darts_model_activation.py, tests/test_data_intelligence_stack.py, tests/test_data_source_endpoints.py, tests/test_deepseek_data_pull_check_contract.py, tests/test_dota2_esports_model_activation.py, tests/test_extreme_randomness_diagnostics.py, tests/test_football_impact_intelligence.py, tests/test_formula_1_model_activation.py, tests/test_formula_e_model_activation.py, tests/test_golf_impact_intelligence.py, tests/test_golf_model_activation.py, tests/test_handball_model_activation.py, tests/test_hockey_impact_intelligence.py, tests/test_indycar_model_activation.py, tests/test_lacrosse_model_activation.py, tests/test_league_of_legends_esports_model_activation.py, tests/test_market_state_manifold.py, tests/test_mens_college_basketball_model_activation.py, tests/test_mlb_model_activation.py, tests/test_model_probability.py, tests/test_motogp_model_activation.py, tests/test_multi_sport_model_registry.py, tests/test_nascar_model_activation.py, tests/test_nba_model_activation.py, tests/test_nfl_model_activation.py, tests/test_nhl_model_activation.py, tests/test_outcome_import_endpoint.py, tests/test_overwatch_esports_model_activation.py, tests/test_pickleball_model_activation.py, tests/test_price_event.py, tests/test_rugby_model_activation.py, tests/test_screenshot_analysis.py, tests/test_screenshot_normalization_parity.py, tests/test_security_framework.py, tests/test_small_account_endpoints.py, tests/test_snooker_model_activation.py, tests/test_soccer_impact_intelligence.py, tests/test_soccer_model_activation.py, tests/test_sport_analysis_endpoint.py, tests/test_table_tennis_model_activation.py, tests/test_tennis_impact_intelligence.py, tests/test_tennis_model_activation.py, tests/test_valorant_esports_model_activation.py, tests/test_volleyball_model_activation.py, tests/test_water_polo_model_activation.py, tests/test_wnba_model_activation.py, tests/test_womens_college_basketball_model_activation.py`
- Owns logic or only forwards: `forwards-only-looking`
- Canonical target: `not singular / unknown`

## `tests/test_kalshi_readonly_adapter.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.prediction_market_data, src.providers.prediction_markets, src.services.prediction_market_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8z0_deployment_governance.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.adapter_readiness, src.brokerage.approval, src.brokerage.approval_evidence, src.brokerage.client_factory, src.brokerage.credential_readiness, src.brokerage.kill_switch, src.brokerage.monitoring, src.brokerage.rollback`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zf1_compatibility_alias_migration.py`

- Reasons: `path-name signal`
- Wraps: `src.data, src.services.streamlit_dashboard_data`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zf7_r2_archive_pipeline.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zf9b_batch_safe_remaining_transfer.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zf9c_headerless_csv_final_deletion.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zf9d_final_data_inventory_reconciliation.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zfo_src_providers_skeleton.py`

- Reasons: `importlib.import_module`
- Wraps: `src.providers.contracts, src.providers.health, src.providers.normalization, src.providers.registry`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zfr_production_module_boundaries.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zfs_legacy_vendor_transport_batch_plan.py`

- Reasons: `path-name signal`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zft_provider_foundation_transport.py`

- Reasons: `importlib.import_module`
- Wraps: `src.providers.base, src.providers.contracts, src.providers.kalshi_adapter_contract, src.providers.normalization, src.providers.policy.allowlist, src.providers.registry, src.providers.sportsbook_adapter_contract, src.providers.validation`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zfu_provider_foundation_completion.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zfw_runtime_provider_migration_batch_2.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zfx_connector_boundary_isolation.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zfy_prediction_market_connector_batch_1.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.prediction_market_data`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zfz_odds_data_connector_batch_2.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.odds_data, src.services.enrichment_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zg0_market_data_connector_batch_3.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.market_data, src.connectors.odds_data, src.connectors.prediction_market_data`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.market_data, src.connectors.odds_data, src.connectors.prediction_market_data, src.providers.errors, src.providers.zero_dte_stocks`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zg2_legacy_deletion_readiness_audit.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zg3_wrapper_import_redirection.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zg4_runtime_bridge_import_redirection.py`

- Reasons: `importlib.import_module`
- Wraps: `src.providers.provider_router`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.providers.provider_router`

## `tests/test_phase10k8zg5_provider_router_independence.py`

- Reasons: `importlib.import_module`
- Wraps: `src.providers.provider_router`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.providers.provider_router`

## `tests/test_phase10k8zg6_legacy_provider_router_delete_proof.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.providers.provider_router`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.providers.provider_router`

## `tests/test_phase10k8zg7_legacy_provider_router_deletion.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.providers.provider_router`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.providers.provider_router`

## `tests/test_phase10k8zg8_provider_foundation_deletion_proof.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zg9_provider_foundation_thin_wrapper_deletion.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zga_provider_registry_runtime_blocker.py`

- Reasons: `importlib.import_module`
- Wraps: `src.providers.kalshi_readonly_readiness, src.providers.registry, src.services.automation_scheduler_facade, src.services.cadence_controller, src.services.scheduler_config`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgb_provider_write_firewall_runtime_blocker.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.readiness, src.providers.policy.write_firewall`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.readiness, src.providers.policy.write_firewall, src.providers.registry, src.services.automation_scheduler_facade`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgd_final_provider_foundation_blocker_deletion.py`

- Reasons: `importlib.import_module`
- Wraps: `src.providers.policy.write_firewall, src.providers.registry, src.services.automation_scheduler_facade`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zge_broader_legacy_runtime_owner_audit.py`

- Reasons: `path-name signal`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgf_live_client_connector_isolation_proof.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.prediction_market_data, src.connectors.prediction_market_data.auth, src.connectors.prediction_market_data.configuration, src.connectors.prediction_market_data.disabled_client, src.connectors.prediction_market_data.readiness, src.connectors.prediction_market_data.signing, src.connectors.prediction_market_data.transport`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.odds_data, src.connectors.odds_data.auth, src.connectors.odds_data.configuration, src.connectors.odds_data.disabled_client, src.connectors.odds_data.live_client, src.connectors.odds_data.readiness, src.connectors.odds_data.source_profile, src.connectors.odds_data.transport`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.odds_data`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.odds_data, src.providers.sportsbooks, src.providers.sportsbooks.adapters, src.services.odds_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.odds_data, src.services.odds_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.odds_data, src.services.odds_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgm_odds_historical_test_redirection.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.odds_data, src.services.odds_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgn_odds_proof_history_cleanup.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.odds_data, src.services.odds_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgo_odds_compatibility_test_retirement.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.odds_data, src.providers.sportsbooks.adapters, src.services.odds_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.odds_data, src.providers.sportsbooks.adapters, src.services.odds_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py`

- Reasons: `importlib.import_module`
- Wraps: `src.services.enrichment_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.services.enrichment_service`

## `tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.connectors.errors, src.services.prediction_market_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.prediction_market_data, src.providers.prediction_markets, src.services.prediction_market_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py`

- Reasons: `importlib.import_module`
- Wraps: `src.analytics.calibration_collector, src.connectors.errors, src.connectors.odds_data, src.connectors.prediction_market_data, src.market_intelligence.prediction_market_outcome_candidates, src.providers.kalshi_readonly_readiness, src.providers.prediction_markets, src.providers.sportsbooks, src.services.automation_scheduler_facade, src.services.odds_runtime_bridge, src.services.prediction_market_runtime_bridge, src.services.scheduler_runner, src.services.settlement_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.analytics.calibration_collector, src.connectors.errors, src.connectors.odds_data, src.connectors.prediction_market_data, src.market_intelligence.prediction_market_outcome_candidates, src.providers.kalshi_readonly_readiness, src.providers.prediction_markets, src.providers.sportsbooks, src.services.odds_runtime_bridge, src.services.prediction_market_runtime_bridge, src.services.scheduler_runner, src.services.settlement_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.prediction_market_data, src.providers.prediction_markets, src.services.prediction_market_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.odds_data, src.connectors.prediction_market_data, src.providers.prediction_markets, src.providers.sportsbooks, src.services.odds_runtime_bridge, src.services.prediction_market_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.prediction_market_data, src.providers.prediction_markets, src.services.prediction_market_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgy_prediction_market_shell_deletion.py`

- Reasons: `importlib.import_module`
- Wraps: `src.connectors.errors, src.connectors.prediction_market_data, src.providers.prediction_markets, src.services.prediction_market_runtime_bridge`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zgz_post_provider_connector_cleanup_freeze.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zh4_core_pricing_extraction.py`

- Reasons: `importlib.import_module`
- Wraps: `market_pricing, quant_engine, src.core.pricing`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zh5_core_probability_extraction.py`

- Reasons: `importlib.import_module`
- Wraps: `model_probability, src.core.probability`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zh6_portfolio_foundation.py`

- Reasons: `importlib.import_module`
- Wraps: `src.core.portfolio`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.core.portfolio`

## `tests/test_phase10k8zh7_execution_game_theory_foundation.py`

- Reasons: `importlib.import_module`
- Wraps: `src.core.execution, src.core.game_theory, src.core.market_impact`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zh8_decision_engine_service_plan.py`

- Reasons: `importlib.import_module`
- Wraps: `src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.services.decision_engine`

## `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.core.market_pricing, src.core.model_probability, src.core.pricing, src.core.probability, src.core.quant_engine, src.core.risk, src.core.risk_engine, src.services.bet_decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zha_core_engine_migration_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhb_service_layer_ownership_audit.py`

- Reasons: `importlib.import_module`
- Wraps: `src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.services.decision_engine`

## `tests/test_phase10k8zhc_screenshot_workflow_thinning_plan.py`

- Reasons: `importlib.import_module`
- Wraps: `src.services.screenshot_intake`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.services.screenshot_intake`

## `tests/test_phase10k8zhd_decision_and_bet_log_audit.py`

- Reasons: `importlib.import_module`
- Wraps: `bet_decision_engine, bet_log, src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhe_api_layer_ownership_audit.py`

- Reasons: `importlib.import_module`
- Wraps: `src.api.model_card_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.api.model_card_service`

## `tests/test_phase10k8zhg_automation_scheduler_decommission_audit.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhh_service_api_dashboard_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhi_legacy_full_gate_remediation.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.api.model_backtest_routes, src.core.backtester, src.core.math_utils, src.core.risk, src.services.model_backtest_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhj_data_foundation.py`

- Reasons: `importlib.import_module`
- Wraps: `src.data, src.data.validation`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhk_backtesting_foundation.py`

- Reasons: `importlib.import_module`
- Wraps: `src.backtesting.datasets, src.backtesting.leakage, src.backtesting.replay, src.backtesting.simulation`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhl_legacy_data_backtesting_owner_map.py`

- Reasons: `path-name signal`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhm_data_backtesting_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `src.api.model_backtest_routes, src.api.performance_routes, src.backtesting, src.core.backtester, src.data, src.services.model_backtest_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhn_analytics_foundation.py`

- Reasons: `importlib.import_module`
- Wraps: `src.analytics`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.analytics`

## `tests/test_phase10k8zho_research_foundation.py`

- Reasons: `importlib.import_module`
- Wraps: `src.research`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.research`

## `tests/test_phase10k8zhp_legacy_analytics_research_owner_map.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.analytics, src.research`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhq_analytics_research_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `src.analytics, src.research`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhr_analytics_migration_batch_1.py`

- Reasons: `importlib.import_module`
- Wraps: `src.analytics.reports`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.analytics.reports`

## `tests/test_phase10k8zhs_research_migration_batch_1.py`

- Reasons: `importlib.import_module`
- Wraps: `src.research.storage`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.research.storage`

## `tests/test_phase10k8zht_analytics_research_batch_1_legacy_scan.py`

- Reasons: `path-name signal`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhv_analytics_downstream_redirection.py`

- Reasons: `importlib.import_module`
- Wraps: `src.analytics.governance, src.analytics.model_governance, src.analytics.reports`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhw_research_downstream_redirection.py`

- Reasons: `importlib.import_module`
- Wraps: `src.research`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.research`

## `tests/test_phase10k8zhx_analytics_research_batch_2_legacy_scan.py`

- Reasons: `path-name signal`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhz_analytics_research_wrapper_delete_proof.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.analytics, src.analytics.model_governance, src.research`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zhz_scheduler_coupled_research_blockers.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zi1_analytics_research_compatibility_test_retirement.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.analytics, src.research`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zi2_research_store_ownership_migration.py`

- Reasons: `importlib.import_module`
- Wraps: `src.research.storage`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.research.storage`

## `tests/test_phase10k8zi3_model_maturity_registry_decoupling.py`

- Reasons: `importlib.import_module`
- Wraps: `src.research`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.research`

## `tests/test_phase10k8zi4_final_analytics_research_delete_readiness.py`

- Reasons: `importlib.import_module`
- Wraps: `model_governance, src.analytics, src.research`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zi5_analytics_research_wrapper_deletion.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.analytics, src.analytics.model_governance, src.research`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zi6_ai_llm_boundary_audit.py`

- Reasons: `importlib.import_module`
- Wraps: `src.ai`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.ai`

## `tests/test_phase10k8zi7_ai_boundary_scaffold.py`

- Reasons: `importlib.import_module`
- Wraps: `src.ai, src.ai.contracts, src.ai.disabled_client, src.ai.prompt_policy, src.ai.readiness`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zia_execution_scheduler_audit.py`

- Reasons: `importlib.import_module`
- Wraps: `src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.services.decision_engine`

## `tests/test_phase10k8zib_unified_brokerage_boundary.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage, src.brokerage.contracts, src.brokerage.execution, src.brokerage.ledger, src.brokerage.orders, src.brokerage.positions, src.brokerage.readiness`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zic_execution_ownership_migration.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zid_execution_final_delete_readiness.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage, src.brokerage.execution, src.brokerage.ledger, src.brokerage.orders, src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine, tempfile`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zie_execution_scheduler_wrapper_deletion.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.brokerage, src.brokerage.execution`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zif_execution_boundary_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage, src.brokerage.execution, src.brokerage.readiness, src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zig_execution_blocker_remediation_audit.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage, src.brokerage.execution, src.brokerage.ledger, src.brokerage.orders, src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.brokerage.settlement, src.services.bet_decision_engine, src.services.bet_log, src.services.decision_engine, src.services.settlement_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zih_execution_blocker_canonicalization.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage, src.brokerage.execution, src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine, tempfile`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zii_execution_blocker_final_delete_readiness.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.brokerage, src.brokerage.execution, src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zik_execution_remediation_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage, src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zil_settlement_canonicalization.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.settlement, src.services.settlement_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zim_ledger_canonicalization.py`

- Reasons: `importlib.import_module`
- Wraps: `src.services.ledger_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.services.ledger_service`

## `tests/test_phase10k8zin_strategy_execution_helper_canonicalization.py`

- Reasons: `importlib.import_module`
- Wraps: `src.services.execution_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.services.execution_service`

## `tests/test_phase10k8zio_execution_helper_final_delete_readiness.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.settlement, src.services.execution_service, src.services.ledger_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zip_execution_helper_canonicalization_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.settlement, src.services.execution_service, src.services.ledger_service, src.services.settlement_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py`

- Reasons: `path-name signal, importlib.import_module`
- Wraps: `src.brokerage, src.brokerage.execution, src.brokerage.ledger, src.brokerage.orders, src.brokerage.readiness, src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8ziw_final_execution_blocker_audit.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage, src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zix_final_execution_blocker_canonicalization.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine, src.services.execution_service, src.services.ledger_service`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8ziz_final_execution_blocker_delete_proof.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zj0_final_execution_blocker_deletion.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage, src.brokerage.readiness, src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zj1_execution_cleanup_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage, src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zj2_broker_account_boundary_audit.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zj3_disabled_broker_account_boundary.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zj4_live_ledger_persistence_boundary_plan.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zj6_live_trading_readiness_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zj7_approval_gate_scaffold.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zj8_broker_client_factory_scaffold.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zj9_live_submit_interface_scaffold.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zja_live_reconciliation_ledger_scaffold.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjb_kill_switch_rollback_scaffold.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjc_live_activation_scaffold_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjd_broker_adapter_protocol.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zje_sandbox_broker_boundary.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjf_credential_activation_boundary.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjg_sandbox_submit_flow.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjh_production_activation_blocker_audit.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zji_sandbox_activation_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjj_activation_gate_verification.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.approval, src.brokerage.kill_switch`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjk_broker_adapter_readiness.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjl_credential_readiness_verification.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjm_live_submit_readiness_verification.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.approval, src.brokerage.client_factory, src.brokerage.ledger, src.brokerage.live_submit, src.brokerage.orders`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjn_monitoring_rollback_readiness.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.kill_switch, src.brokerage.rollback`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.accounts, src.brokerage.activation, src.brokerage.adapter_readiness, src.brokerage.approval, src.brokerage.client_factory, src.brokerage.credential_readiness, src.brokerage.credentials, src.brokerage.deployment_readiness, src.brokerage.execution, src.brokerage.kill_switch, src.brokerage.ledger, src.brokerage.live_ledger, src.brokerage.live_reconciliation, src.brokerage.live_submit, src.brokerage.monitoring, src.brokerage.orders, src.brokerage.readiness, src.brokerage.reconciliation, src.brokerage.rollback, src.brokerage.submit_readiness`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjp_approval_evidence.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjq_sandbox_activation_composition.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.approval_evidence`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.brokerage.approval_evidence`

## `tests/test_phase10k8zjr_dry_run_submit_proof.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjs_dry_run_ledger_verification.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjt_final_sandbox_activation_proof.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjv_operator_approval_interface.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.approval`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.brokerage.approval`

## `tests/test_phase10k8zjw_approval_audit_layer.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjx_sandbox_enablement_layer.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.activation, src.brokerage.approval, src.brokerage.approval_evidence, src.brokerage.client_factory, src.brokerage.credential_readiness, src.brokerage.deployment_readiness, src.brokerage.kill_switch, src.brokerage.monitoring, src.brokerage.rollback`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjy_sandbox_adapter_stub.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zjz_kill_switch_governance.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.approval, src.brokerage.approval_audit, src.brokerage.client_factory, src.brokerage.deployment_policy, src.brokerage.execution, src.brokerage.kill_switch_policy, src.brokerage.live_submit, src.brokerage.operator, src.brokerage.orders, src.brokerage.readiness, src.brokerage.sandbox_adapter, src.brokerage.sandbox_enablement`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zk2_credential_sdk_network_freeze.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.credential_readiness`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.brokerage.credential_readiness`

## `tests/test_phase10k8zk2_final_live_trading_disabled_proof.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.accounts, src.brokerage.approval, src.brokerage.client_factory, src.brokerage.credential_loader, src.brokerage.credentials, src.brokerage.deployment_readiness, src.brokerage.kill_switch, src.brokerage.live_ledger, src.brokerage.live_reconciliation, src.brokerage.live_submit, src.brokerage.orders`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zk2_final_system_freeze.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zk2_production_activation_readiness_ledger.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.accounts, src.brokerage.approval, src.brokerage.client_factory, src.brokerage.credential_readiness, src.brokerage.deployment_readiness, src.brokerage.kill_switch, src.brokerage.live_ledger, src.brokerage.live_reconciliation, src.brokerage.live_submit, src.brokerage.monitoring, src.brokerage.orders, src.brokerage.rollback`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zk3_final_production_readiness_checkpoint.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `src.brokerage`

## `tests/test_phase10k8zk4_architecture_invariants.py`

- Reasons: `importlib.import_module`
- Wraps: `src.brokerage.approval, src.brokerage.client_factory, src.brokerage.live_submit`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zk4_operator_implementation_plan.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zk5_automation_scheduler_full_inventory.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zk6_automation_scheduler_ownership_migration.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zl0_automation_scheduler_deletion.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`

- Reasons: `importlib.import_module`
- Wraps: `src.backtesting.dataset_builder, src.backtesting.engine, src.backtesting.strategy_profiles, src.data, src.data.historical_odds, src.data.historical_sources, src.data.line_movement, src.data.source_event_links, src.market_intelligence.feature_packs, src.research.feature_control`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zmh_automation_scheduler_final_removal_attempt.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zmi_streamlit_dashboard_test_import_redirection.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zmj_sports_impact_test_import_redirection.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zmr_security_policy_secret_safety_migration.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase10k8zms_security_cluster_migration.py`

- Reasons: `importlib.import_module`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`

## `tests/test_phase1_legacy_inventory.py`

- Reasons: `path-name signal`
- Wraps: `none detected`
- Imported by: `none`
- Owns logic or only forwards: `contains logic or public API surface`
- Canonical target: `not singular / unknown`
