# Repository Discovery Orphan / Dead Code Report

- Candidate modules: `593`

| Path | Classification | Ownership | Main guard |
| --- | --- | --- | --- |
| `src/ai/evaluation/__init__.py` | `dead candidate` | `ai` | `False` |
| `src/ai/llm/__init__.py` | `dead candidate` | `ai` | `False` |
| `src/ai/models/__init__.py` | `dead candidate` | `ai` | `False` |
| `src/ai/policy/__init__.py` | `dead candidate` | `ai` | `False` |
| `src/ai/prompts/__init__.py` | `dead candidate` | `ai` | `False` |
| `src/analytics/baseball_impact_report.py` | `dead candidate` | `analytics` | `False` |
| `src/analytics/combat_impact_report.py` | `dead candidate` | `analytics` | `False` |
| `src/analytics/extreme_signal_red_team.py` | `dead candidate` | `analytics` | `False` |
| `src/analytics/golf_impact_report.py` | `dead candidate` | `analytics` | `False` |
| `src/analytics/hockey_impact_report.py` | `dead candidate` | `analytics` | `False` |
| `src/analytics/soccer_impact_report.py` | `dead candidate` | `analytics` | `False` |
| `src/analytics/tennis_impact_report.py` | `dead candidate` | `analytics` | `False` |
| `src/brokerage/execution.py` | `dead candidate` | `brokerage` | `False` |
| `src/brokerage/later/__init__.py` | `dead candidate` | `brokerage` | `False` |
| `src/brokerage/live_trading/__init__.py` | `dead candidate` | `brokerage` | `False` |
| `src/brokerage/order_gateway/__init__.py` | `dead candidate` | `brokerage` | `False` |
| `src/brokerage/paper_trading/__init__.py` | `dead candidate` | `brokerage` | `False` |
| `src/brokerage/risk_controls/__init__.py` | `dead candidate` | `brokerage` | `False` |
| `src/connectors/__init__.py` | `dead candidate` | `src/unknown` | `False` |
| `src/connectors/feeds/__init__.py` | `dead candidate` | `src/unknown` | `False` |
| `src/connectors/web_scraping/__init__.py` | `dead candidate` | `src/unknown` | `False` |
| `src/core/budget_gates.py` | `dead candidate` | `core` | `False` |
| `src/core/liquidity_context_scoring.py` | `dead candidate` | `core` | `False` |
| `src/core/session_risk_rules.py` | `dead candidate` | `core` | `False` |
| `src/core/settings.py` | `dead candidate` | `core` | `False` |
| `src/core/status_codes.py` | `dead candidate` | `core` | `False` |
| `src/market_intelligence/arbitrage/__init__.py` | `dead candidate` | `market intelligence` | `False` |
| `src/market_intelligence/baseball_impact_readiness.py` | `dead candidate` | `market intelligence` | `False` |
| `src/market_intelligence/middles/__init__.py` | `dead candidate` | `market intelligence` | `False` |
| `src/market_intelligence/technical_signal_fields.py` | `dead candidate` | `market intelligence` | `False` |
| `src/providers/adapters/__init__.py` | `dead candidate` | `providers` | `False` |
| `src/providers/injury_weather_adapter_contract.py` | `dead candidate` | `providers` | `False` |
| `src/providers/news_events_adapter_contract.py` | `dead candidate` | `providers` | `False` |
| `src/providers/player_props_adapter_contract.py` | `dead candidate` | `providers` | `False` |
| `src/providers/stock_fundamentals_adapter_contract.py` | `dead candidate` | `providers` | `False` |
| `src/providers/stock_price_adapter_contract.py` | `dead candidate` | `providers` | `False` |
| `src/research/correlation_structure_diagnostics.py` | `dead candidate` | `research` | `False` |
| `src/research/derived_feature_planner.py` | `dead candidate` | `research` | `False` |
| `src/research/experiment_history_store.py` | `dead candidate` | `research` | `False` |
| `src/research/extreme_randomness_report.py` | `dead candidate` | `research` | `False` |
| `src/services/audit_log.py` | `dead candidate` | `services` | `False` |
| `src/sports/__init__.py` | `dead candidate` | `src/unknown` | `False` |
| `src/storage/__init__.py` | `dead candidate` | `src/unknown` | `False` |
| `scripts/analyze_json_data.py` | `possible entrypoint` | `scripts/ops` | `True` |
| `scripts/init_sports_master_db.py` | `possible entrypoint` | `scripts/ops` | `True` |
| `scripts/ops_check.py` | `possible entrypoint` | `scripts/ops` | `True` |
| `scripts/smoke_test.py` | `possible entrypoint` | `scripts/ops` | `True` |
| `src/api/__init__.py` | `possible entrypoint` | `api` | `False` |
| `streamlit_app.py` | `possible entrypoint` | `dashboard/frontend` | `False` |
| `tests/test_advanced_red_team.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_afl_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_analyze_event.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_backtesting_engine.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_badminton_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_balance_sheet_risk.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_bankroll_state.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_baseball_impact_intelligence.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_basketball_player_impact.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_bet_log.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_broker_quality_scoring.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_budget_gates.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_calibration_collector.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_calibration_tracker.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_call_of_duty_esports_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_candlestick_pattern_detector.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_clv_tracker.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_collector_scheduled_runner.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_college_football_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_combat_impact_intelligence.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_combat_sports_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_cricket_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_crypto_edge_lab_registry.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_cs2_esports_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_darts_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_data_availability_tiers.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_data_intelligence_stack.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_data_paths.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_data_source_endpoints.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_data_source_registry.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_data_source_research_lanes.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_deepseek_data_pull_check_contract.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_deepseek_profit_lab.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_deepseek_reviewer.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_derived_feature_backfill_report.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_derived_feature_planner.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_dota2_esports_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_drawdown_controls.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_evaluate_lines.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_exposure_limits.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_extreme_randomness_diagnostics.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_football_impact_intelligence.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_formula_1_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_formula_e_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_golf_impact_intelligence.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_golf_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_handball_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_historical_replay.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_hockey_impact_intelligence.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_indycar_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_injury_weather_adapter_contract.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_institutional_audit_ledger.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_institutional_cross_asset_adapters.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_institutional_cross_asset_calibration.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_institutional_cross_asset_lab.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_institutional_cross_asset_reports.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_institutional_cross_asset_scores.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_institutional_deepseek_review.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_institutional_execution_desk.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_institutional_risk_engine.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_institutional_stock_pro_analyst_registry.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_kalshi_adapter_contract.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_kalshi_market_provider.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_kalshi_readonly_adapter.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_kalshi_readonly_readiness_contract.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_kelly_staking.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_lacrosse_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_league_of_legends_esports_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_liquidity_context_scoring.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_live_smoke_payload_contract.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_local_sports_history_audit.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_market_state_manifold.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_mens_college_basketball_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_mlb_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_model_input_coverage.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_model_performance_report.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_model_probability.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_motogp_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_multi_sport_model_registry.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nascar_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_ncaaf_collegefootballdata_adapter.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_news_events_adapter_contract.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_coaching_adapters.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_coaching_feature_builders.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_coaching_sources.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_cutoff_week_features.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_historical_pattern_lab.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_historical_pattern_validation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_open_data_adapters.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_open_data_backfill.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_open_data_feature_builders.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_open_data_field_catalog.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_open_data_sources.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nfl_source_exhaustion.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_nhl_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_open_sports_history_backfill.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_open_sports_history_derived_features.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_open_sports_history_import.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_open_sports_history_sources.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_ops_scripts_contract.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_ops_workflow.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_outcome_import_endpoint.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_outcome_migration.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_outcome_reconciliation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_overwatch_esports_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_paper_trade_ledger.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_pattern_calibration.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_pattern_review_queue.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_performance_metrics.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_phase10k5_core_arbitrage_engine.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_pickleball_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_player_props_adapter_contract.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_price_event.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_provider_adapter_base.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_provider_contracts.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_provider_health.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_provider_normalization_contract.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_provider_payload_validator.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_provider_secret_policy.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_quant_engine_foundation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_risk_of_ruin.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_rugby_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_screenshot_normalization_parity.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_security_framework.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_settlement_discovery.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_sharp_cross_book_review_queue.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_sharp_scheduler_flow.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_sharp_sportsbook_adapter.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_small_account_endpoints.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_small_account_strategy.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_snooker_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_soccer_impact_intelligence.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_soccer_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_source_quality_scoring.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_sport_analysis_endpoint.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_sport_model_routing.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_sportsbook_adapter_contract.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_sportsbook_odds_provider.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_stake_confidence.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_stock_fundamentals_adapter_contract.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_stock_price_adapter_contract.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_strategy_framework.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_table_tennis_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_tennis_impact_intelligence.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_tennis_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_valorant_esports_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_volleyball_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_water_polo_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_wnba_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/test_womens_college_basketball_model_activation.py` | `possible entrypoint` | `tests` | `True` |
| `tests/conftest.py` | `test-only` | `tests` | `False` |
| `tests/support/__init__.py` | `test-only` | `tests` | `False` |
| `tests/test_activation_tiers.py` | `test-only` | `tests` | `False` |
| `tests/test_alert_engine.py` | `test-only` | `tests` | `False` |
| `tests/test_alert_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_arbitrage_detector.py` | `test-only` | `tests` | `False` |
| `tests/test_arbitrage_draw_market.py` | `test-only` | `tests` | `False` |
| `tests/test_arbitrage_exchange.py` | `test-only` | `tests` | `False` |
| `tests/test_arbitrage_prediction_market.py` | `test-only` | `tests` | `False` |
| `tests/test_arbitrage_risk_filters.py` | `test-only` | `tests` | `False` |
| `tests/test_arbitrage_three_way.py` | `test-only` | `tests` | `False` |
| `tests/test_arbitrage_two_way.py` | `test-only` | `tests` | `False` |
| `tests/test_asof_line_movement_query.py` | `test-only` | `tests` | `False` |
| `tests/test_audit_log.py` | `test-only` | `tests` | `False` |
| `tests/test_automation_scheduler_endpoints.py` | `test-only` | `tests` | `False` |
| `tests/test_automation_scheduler_scripts.py` | `test-only` | `tests` | `False` |
| `tests/test_backtest_dataset_builder.py` | `test-only` | `tests` | `False` |
| `tests/test_backtest_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_backtest_leakage.py` | `test-only` | `tests` | `False` |
| `tests/test_backtest_regression_strategy.py` | `test-only` | `tests` | `False` |
| `tests/test_backtest_schema.py` | `test-only` | `tests` | `False` |
| `tests/test_backtest_strategy_bankroll.py` | `test-only` | `tests` | `False` |
| `tests/test_backtest_strategy_profiles.py` | `test-only` | `tests` | `False` |
| `tests/test_backtesting.py` | `test-only` | `tests` | `False` |
| `tests/test_bookmaker_normalizer.py` | `test-only` | `tests` | `False` |
| `tests/test_cadence_controller.py` | `test-only` | `tests` | `False` |
| `tests/test_calibration.py` | `test-only` | `tests` | `False` |
| `tests/test_calibration_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_calibration_strategy_filter.py` | `test-only` | `tests` | `False` |
| `tests/test_champion_challenger.py` | `test-only` | `tests` | `False` |
| `tests/test_cross_book_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_cross_book_line_comparator.py` | `test-only` | `tests` | `False` |
| `tests/test_data_lineage.py` | `test-only` | `tests` | `False` |
| `tests/test_data_quality_monitor.py` | `test-only` | `tests` | `False` |
| `tests/test_ev_line_shopper.py` | `test-only` | `tests` | `False` |
| `tests/test_execution_later_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_experiment_history_store.py` | `test-only` | `tests` | `False` |
| `tests/test_experiment_report_exporter.py` | `test-only` | `tests` | `False` |
| `tests/test_feature_ablation_lab.py` | `test-only` | `tests` | `False` |
| `tests/test_field_scorecard.py` | `test-only` | `tests` | `False` |
| `tests/test_governance_audit_log.py` | `test-only` | `tests` | `False` |
| `tests/test_governance_config.py` | `test-only` | `tests` | `False` |
| `tests/test_governance_health.py` | `test-only` | `tests` | `False` |
| `tests/test_governance_report.py` | `test-only` | `tests` | `False` |
| `tests/test_historical_backtest_bridge.py` | `test-only` | `tests` | `False` |
| `tests/test_historical_data_sources.py` | `test-only` | `tests` | `False` |
| `tests/test_historical_line_movement.py` | `test-only` | `tests` | `False` |
| `tests/test_historical_odds_importers.py` | `test-only` | `tests` | `False` |
| `tests/test_historical_odds_sqlite.py` | `test-only` | `tests` | `False` |
| `tests/test_human_approval_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_input_quality_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_alternative_investments.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_credit_risk_models.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_derivatives_hedging.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_execution_cost_models.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_factor_risk_models.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_fixed_income_rates.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_liability_retirement_models.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_macro_regime_models.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_model_governance.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_model_router.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_performance_attribution.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_portfolio_construction.py` | `test-only` | `tests` | `False` |
| `tests/test_institutional_tax_aware_models.py` | `test-only` | `tests` | `False` |
| `tests/test_kalshi_monitor.py` | `test-only` | `tests` | `False` |
| `tests/test_kalshi_provider_shape_contract.py` | `test-only` | `tests` | `False` |
| `tests/test_kalshi_scoring.py` | `test-only` | `tests` | `False` |
| `tests/test_kelly_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_later_auto_execution_policy.py` | `test-only` | `tests` | `False` |
| `tests/test_line_movement_data_quality_dashboard.py` | `test-only` | `tests` | `False` |
| `tests/test_line_movement_import_contract.py` | `test-only` | `tests` | `False` |
| `tests/test_line_movement_readiness.py` | `test-only` | `tests` | `False` |
| `tests/test_liquidity_risk.py` | `test-only` | `tests` | `False` |
| `tests/test_market_clock.py` | `test-only` | `tests` | `False` |
| `tests/test_market_feature_packs.py` | `test-only` | `tests` | `False` |
| `tests/test_market_identity_resolver.py` | `test-only` | `tests` | `False` |
| `tests/test_market_research_store.py` | `test-only` | `tests` | `False` |
| `tests/test_market_structure.py` | `test-only` | `tests` | `False` |
| `tests/test_middle_alt_line.py` | `test-only` | `tests` | `False` |
| `tests/test_middle_ev_simulator.py` | `test-only` | `tests` | `False` |
| `tests/test_middle_key_number.py` | `test-only` | `tests` | `False` |
| `tests/test_middle_opportunity_detector.py` | `test-only` | `tests` | `False` |
| `tests/test_middle_prop.py` | `test-only` | `tests` | `False` |
| `tests/test_middle_push_corridor.py` | `test-only` | `tests` | `False` |
| `tests/test_middle_spread.py` | `test-only` | `tests` | `False` |
| `tests/test_middle_team_total.py` | `test-only` | `tests` | `False` |
| `tests/test_middle_total.py` | `test-only` | `tests` | `False` |
| `tests/test_model_card.py` | `test-only` | `tests` | `False` |
| `tests/test_model_drift_monitor.py` | `test-only` | `tests` | `False` |
| `tests/test_model_inventory.py` | `test-only` | `tests` | `False` |
| `tests/test_model_recheck_runner.py` | `test-only` | `tests` | `False` |
| `tests/test_model_router.py` | `test-only` | `tests` | `False` |
| `tests/test_model_router_registry.py` | `test-only` | `tests` | `False` |
| `tests/test_model_validation_report.py` | `test-only` | `tests` | `False` |
| `tests/test_nba_model_activation.py` | `test-only` | `tests` | `False` |
| `tests/test_news_event_monitor.py` | `test-only` | `tests` | `False` |
| `tests/test_no_vig_pricing.py` | `test-only` | `tests` | `False` |
| `tests/test_odds_line_monitor.py` | `test-only` | `tests` | `False` |
| `tests/test_odds_math.py` | `test-only` | `tests` | `False` |
| `tests/test_opportunity_scoring.py` | `test-only` | `tests` | `False` |
| `tests/test_outcome_store.py` | `test-only` | `tests` | `False` |
| `tests/test_paper_decision_ledger.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k0_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k2_sports_snapshot_pipeline.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k3_runtime_csv_migration_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k4_0dte_options_schema_foundation.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k6a_frontend_readiness_gate_inspection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k6b_dashboard_navigation_plan_contract.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k6c_controlled_ui_shell.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k6d_readiness_gate_display_contract.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k6e_readiness_display_data_helper.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k6f_readiness_display_payload_builder.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k6g_readiness_display_renderer_contract.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k6h_readiness_display_renderer_helper.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k6i_controlled_navigation_shell.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k6j_controlled_readiness_ui_wiring.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k6k_controlled_dashboard_shell_review.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k7a_full_suite_readiness_ownership_map.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k7b_test_guardrail_stabilization.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k7c_full_suite_readiness_gate_matrix.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k7d_10k8_prediction_testing_entry_contract.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8a_paper_only_prediction_testing_owner_scan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8b_paper_only_fixture_testing_contract.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8c_paper_only_fixture_validation_helper.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8d_paper_only_fixture_readiness_payload_adapter.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8e_paper_only_fixture_evaluation_contract.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8f_paper_only_fixture_evaluation_helper.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8g_paper_only_evaluation_readiness_adapter.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8h_paper_only_fixture_pipeline_contract.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8i_paper_only_fixture_pipeline_helper.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8j_controlled_pipeline_smoke_review.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8k_prediction_testing_readiness_review.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8l_controlled_multi_market_test_mode_ui.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8m_strict_model_field_baseline_by_market_and_sport.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8n_controlled_field_catalog_ui_review.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8o_dedicated_0dte_paper_fixture_template.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8p_dedicated_0dte_fixture_validation_adapter.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8q_dedicated_0dte_validation_readiness_payload.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8r_dedicated_0dte_validation_readiness_ui.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8s_dedicated_0dte_paper_evaluation_adapter.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8t_dedicated_0dte_evaluation_readiness_payload.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8u_dedicated_0dte_evaluation_ui.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8v_full_0dte_paper_pipeline_adapter.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8w_full_0dte_paper_pipeline_ui.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8x_controlled_0dte_paper_run_smoke_review.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8y_0dte_prediction_testing_readiness_review.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8z0_deployment_governance.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8z_final_controlled_prediction_testing_freeze.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8za_0dte_data_field_formula_coverage_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zb0_product_contract_reset.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zb_0dte_field_formula_gap_patch.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zc_dashboard_product_lane_cleanup.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zd_orb_strategy_research_integration_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8ze_institutional_market_metric_catalog.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf0_canonical_research_backtest_workflow_migration_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf0a_frozen_test_contract_reset.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf1_compatibility_alias_migration.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf2_production_symbol_migration.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf3_product_ui_language_finalization.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf4_asset_grade_repo_clean_inventory.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf5_universal_runtime_ownership_map.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf6_r2_object_storage_archive_contract.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf7_r2_archive_pipeline.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf8_r2_transfer_proof_report.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf9_full_r2_transfer_report.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf9b_batch_safe_remaining_transfer.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf9c_headerless_csv_final_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zf9d_final_data_inventory_reconciliation.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfe1_universal_product_language_alignment.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfe2_daily_data_hygiene_scheduler.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfe_duplicate_code_evidence_scan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zff_canonical_owner_decision_report.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfg_safe_migration_batch_1.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfh_safe_migration_batch_2_boundary_guards.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfi_automation_scheduler_decomposition_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfj_provider_live_market_decomposition_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfk_test_suite_cleanup_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfo_src_providers_skeleton.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfp_provider_taxonomy_correction.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfr_production_module_boundaries.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfs_legacy_vendor_transport_batch_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zft_provider_foundation_transport.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfu_provider_foundation_completion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfw_runtime_provider_migration_batch_2.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfx_connector_boundary_isolation.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfy_prediction_market_connector_batch_1.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zfz_odds_data_connector_batch_2.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zg0_market_data_connector_batch_3.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zg2_legacy_deletion_readiness_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zg3_wrapper_import_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zg4_runtime_bridge_import_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zg5_provider_router_independence.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zg6_legacy_provider_router_delete_proof.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zg7_legacy_provider_router_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zg8_provider_foundation_deletion_proof.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zg9_provider_foundation_thin_wrapper_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zga_provider_registry_runtime_blocker.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgb_provider_write_firewall_runtime_blocker.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgd_final_provider_foundation_blocker_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zge_broader_legacy_runtime_owner_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgf_live_client_connector_isolation_proof.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgm_odds_historical_test_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgn_odds_proof_history_cleanup.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgo_odds_compatibility_test_retirement.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgy_prediction_market_shell_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zgz_post_provider_connector_cleanup_freeze.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zh0_core_engine_extraction_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zh1_core_math_foundation_batch.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zh2_risk_foundation_batch.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zh3_game_theory_execution_edge_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zh4_core_pricing_extraction.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zh5_core_probability_extraction.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zh6_portfolio_foundation.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zh7_execution_game_theory_foundation.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zh8_decision_engine_service_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zha_core_engine_migration_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhb_service_layer_ownership_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhc_screenshot_workflow_thinning_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhd_decision_and_bet_log_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhe_api_layer_ownership_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhf_dashboard_entrypoint_ownership_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhg_automation_scheduler_decommission_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhh_service_api_dashboard_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhi_legacy_full_gate_remediation.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhj_data_foundation.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhk_backtesting_foundation.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhl_legacy_data_backtesting_owner_map.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhm_data_backtesting_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhn_analytics_foundation.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zho_research_foundation.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhp_legacy_analytics_research_owner_map.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhq_analytics_research_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhr_analytics_migration_batch_1.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhs_research_migration_batch_1.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zht_analytics_research_batch_1_legacy_scan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhu_analytics_research_batch_1_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhv_analytics_downstream_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhw_research_downstream_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhx_analytics_research_batch_2_legacy_scan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhy_analytics_research_batch_2_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhz_analytics_research_reference_scan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhz_analytics_research_wrapper_delete_proof.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zhz_scheduler_coupled_research_blockers.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zi0_analytics_research_delete_proof_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zi1_analytics_research_compatibility_test_retirement.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zi2_research_store_ownership_migration.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zi3_model_maturity_registry_decoupling.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zi4_final_analytics_research_delete_readiness.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zi5_analytics_research_wrapper_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zi6_ai_llm_boundary_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zi7_ai_boundary_scaffold.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zi8_ai_scheduler_blocker_map.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zi9_ai_boundary_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zia_execution_scheduler_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zib_unified_brokerage_boundary.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zic_execution_ownership_migration.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zid_execution_final_delete_readiness.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zie_execution_scheduler_wrapper_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zif_execution_boundary_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zig_execution_blocker_remediation_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zih_execution_blocker_canonicalization.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zii_execution_blocker_final_delete_readiness.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zik_execution_remediation_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zil_settlement_canonicalization.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zim_ledger_canonicalization.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zin_strategy_execution_helper_canonicalization.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zio_execution_helper_final_delete_readiness.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zip_execution_helper_canonicalization_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8ziq_execution_helper_reference_redirection_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zir_execution_helper_runtime_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zis_execution_helper_test_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zit_execution_helper_final_delete_proof.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8ziv_execution_helper_deletion_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8ziw_final_execution_blocker_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zix_final_execution_blocker_canonicalization.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8ziy_final_execution_test_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8ziz_final_execution_blocker_delete_proof.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zj0_final_execution_blocker_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zj1_execution_cleanup_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zj2_broker_account_boundary_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zj3_disabled_broker_account_boundary.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zj4_live_ledger_persistence_boundary_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zj5_production_approval_gate_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zj6_live_trading_readiness_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zj7_approval_gate_scaffold.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zj8_broker_client_factory_scaffold.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zj9_live_submit_interface_scaffold.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zja_live_reconciliation_ledger_scaffold.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjb_kill_switch_rollback_scaffold.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjc_live_activation_scaffold_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjd_broker_adapter_protocol.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zje_sandbox_broker_boundary.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjf_credential_activation_boundary.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjg_sandbox_submit_flow.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjh_production_activation_blocker_audit.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zji_sandbox_activation_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjj_activation_gate_verification.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjk_broker_adapter_readiness.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjl_credential_readiness_verification.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjm_live_submit_readiness_verification.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjn_monitoring_rollback_readiness.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjp_approval_evidence.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjq_sandbox_activation_composition.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjr_dry_run_submit_proof.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjs_dry_run_ledger_verification.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjt_final_sandbox_activation_proof.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjv_operator_approval_interface.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjw_approval_audit_layer.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjx_sandbox_enablement_layer.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjy_sandbox_adapter_stub.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zjz_kill_switch_governance.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk2_credential_sdk_network_freeze.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk2_final_live_trading_disabled_proof.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk2_final_system_freeze.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk2_production_activation_readiness_ledger.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk3_final_production_readiness_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk4_architecture_invariants.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk4_operator_implementation_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk4_project_completion_status.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk4_rollout_plan.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk5_automation_scheduler_full_inventory.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk6_automation_scheduler_ownership_migration.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk7_automation_scheduler_runtime_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk8_automation_scheduler_test_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zk9_automation_scheduler_final_delete_proof.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zl0_automation_scheduler_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zl1_automation_scheduler_decommission_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zl2_market_intelligence_foundation.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zl3_sports_intelligence_absorption.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zl4_prediction_market_intelligence_absorption.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zl5_options_0dte_gex_vanna_foundation.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zl6_market_intelligence_runtime_test_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zl7_market_intelligence_scheduler_deletion.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zl8_market_intelligence_absorption_checkpoint.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zmh_automation_scheduler_final_removal_attempt.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zmi_streamlit_dashboard_test_import_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zmj_sports_impact_test_import_redirection.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zmr_security_policy_secret_safety_migration.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zms_security_cluster_migration.py` | `test-only` | `tests` | `False` |
| `tests/test_phase10k8zt_provider_security_surface_retirement.py` | `test-only` | `tests` | `False` |
| `tests/test_phase1_legacy_inventory.py` | `test-only` | `tests` | `False` |
| `tests/test_phase_x_non_src_inventory.py` | `test-only` | `tests` | `False` |
| `tests/test_player_prop_monitor.py` | `test-only` | `tests` | `False` |
| `tests/test_promotion_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_provider_registry.py` | `test-only` | `tests` | `False` |
| `tests/test_repo_architecture_guard.py` | `test-only` | `tests` | `False` |
| `tests/test_report_writer.py` | `test-only` | `tests` | `False` |
| `tests/test_research_evidence_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_response_compactor.py` | `test-only` | `tests` | `False` |
| `tests/test_review_queue.py` | `test-only` | `tests` | `False` |
| `tests/test_review_queue_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_risk_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_run_context.py` | `test-only` | `tests` | `False` |
| `tests/test_scheduler_config.py` | `test-only` | `tests` | `False` |
| `tests/test_scheduler_runner.py` | `test-only` | `tests` | `False` |
| `tests/test_screenshot_analysis.py` | `test-only` | `tests` | `False` |
| `tests/test_settlement_liquidity_gate.py` | `test-only` | `tests` | `False` |
| `tests/test_settlement_rule_checker.py` | `test-only` | `tests` | `False` |
| `tests/test_snapshot_store.py` | `test-only` | `tests` | `False` |
| `tests/test_source_event_link_resolver.py` | `test-only` | `tests` | `False` |
| `tests/test_sport_feature_packs.py` | `test-only` | `tests` | `False` |
| `tests/test_stake_sizing_simulator.py` | `test-only` | `tests` | `False` |
| `tests/test_status_classifier.py` | `test-only` | `tests` | `False` |
| `tests/test_stock_monitor.py` | `test-only` | `tests` | `False` |
| `tests/test_streamlit_dashboard_data.py` | `test-only` | `tests` | `False` |
| `tests/test_synthetic_line_movement_sandbox.py` | `test-only` | `tests` | `False` |
| `tests/test_system_health.py` | `test-only` | `tests` | `False` |
| `tests/test_walk_forward_gate.py` | `test-only` | `tests` | `False` |
