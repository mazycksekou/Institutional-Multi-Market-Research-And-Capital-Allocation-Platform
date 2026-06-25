# Automation Scheduler Decommission Inventory

Canonical src.* architecture already exists. Live trading, broker/account/credential/order/deployment activation remain disabled.

Inventory summary:
- Remaining automation_scheduler files: 329
- Runtime-referenced files: 70
- Test-referenced files: 303
- Delete-ready after proof: 23

| file | runtime_ref_count | test_ref_count | classification | canonical_target | deletion_decision |
| --- | --- | --- | --- | --- | --- |
| automation_scheduler/__init__.py | 11 | 47 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/advanced_red_team_provider_policy.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/advanced_red_team_report.py | 1 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/advanced_shape_diagnostics.py | 1 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/ai_provider_security.py | 0 | 4 | MIGRATE_TO_SRC_AI | src.ai | preserve |
| automation_scheduler/alert_engine.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/arbitrage/__init__.py | 11 | 47 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/arbitrage/arbitrage_risk_filters.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/arbitrage/draw_market_arbitrage.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/arbitrage/exchange_arbitrage.py | 1 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/arbitrage/prediction_market_arbitrage.py | 1 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/arbitrage/three_way_arbitrage.py | 0 | 4 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/arbitrage/two_way_arbitrage.py | 0 | 4 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/arbitrage_detector.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/asof_line_movement_query.py | 1 | 3 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/audit_log.py | 1 | 3 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/backtest_dataset_builder.py | 0 | 14 | MIGRATE_TO_SRC_BACKTESTING | src.backtesting | preserve |
| automation_scheduler/backtest_leakage.py | 0 | 2 | MIGRATE_TO_SRC_BACKTESTING | src.backtesting | preserve |
| automation_scheduler/backtest_schema.py | 0 | 2 | MIGRATE_TO_SRC_BACKTESTING | src.backtesting | preserve |
| automation_scheduler/backtest_strategy_bankroll.py | 0 | 3 | MIGRATE_TO_SRC_BACKTESTING | src.backtesting | preserve |
| automation_scheduler/backtest_strategy_profiles.py | 0 | 2 | MIGRATE_TO_SRC_BACKTESTING | src.backtesting | preserve |
| automation_scheduler/backtesting_engine.py | 0 | 12 | MIGRATE_TO_SRC_BACKTESTING | src.backtesting | preserve |
| automation_scheduler/balance_sheet_risk.py | 3 | 4 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/bankroll_state.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/baseball_availability_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/baseball_batter_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/baseball_bullpen_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/baseball_data_availability.py | 0 | 1 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/baseball_defense_baserunning_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/baseball_impact_calibration.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/baseball_impact_common.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/baseball_impact_readiness.py | 2 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/baseball_impact_red_team.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/baseball_impact_report.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/baseball_incentive_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/baseball_lineup_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/baseball_market_relevance.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/baseball_matchup_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/baseball_park_weather_umpire_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/baseball_pitcher_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/baseball_run_value_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/basketball_incentive_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/basketball_lineup_matchup_context.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/basketball_market_relevance.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/basketball_player_impact.py | 2 | 2 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/basketball_player_impact_calibration.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/basketball_player_impact_common.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/basketball_player_impact_readiness.py | 2 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/basketball_player_impact_red_team.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/basketball_possession_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/basketball_role_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/basketball_tracking_opportunity.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/bayesian_structural_baseline.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/bookmaker_normalizer.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/budget_gates.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/cadence_controller.py | 0 | 2 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/calibration.py | 23 | 103 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/calibration_collector.py | 2 | 11 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/calibration_strategy_filter.py | 1 | 6 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/calibration_tracker.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/candlestick_manifold_detector.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/candlestick_pattern_detector.py | 1 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/causal_discovery_research.py | 0 | 1 | MIGRATE_TO_SRC_RESEARCH | src.research | preserve |
| automation_scheduler/causal_scaffold.py | 0 | 1 | MIGRATE_TO_SRC_RESEARCH | src.research | preserve |
| automation_scheduler/clv_tracker.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/collector_scheduled_runner.py | 1 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/combat_availability_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/combat_damage_durability_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/combat_data_availability.py | 0 | 1 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/combat_grappling_control_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/combat_impact_calibration.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/combat_impact_common.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/combat_impact_readiness.py | 2 | 0 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/combat_impact_red_team.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/combat_impact_report.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/combat_incentive_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/combat_market_relevance.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/combat_matchup_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/combat_pace_cardio_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/combat_phase_control_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/combat_ruleset_referee_judging_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/combat_striking_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/conformal_uncertainty.py | 0 | 1 | MIGRATE_TO_SRC_RESEARCH | src.research | preserve |
| automation_scheduler/contrastive_embedding_diagnostics.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/correlation_structure_diagnostics.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/cross_asset_embedding_router.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/cross_asset_intelligence_router.py | 0 | 3 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/cross_asset_manifold_router.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/cross_book_line_comparator.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/data_availability_tiers.py | 2 | 5 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/data_intelligence_registry.py | 0 | 3 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/data_paths.py | 4 | 5 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/data_source_registry.py | 2 | 12 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/data_source_research_lanes.py | 2 | 1 | MIGRATE_TO_SRC_RESEARCH | src.research | preserve |
| automation_scheduler/deepseek_daily_report.py | 1 | 3 | MIGRATE_TO_SRC_AI | src.ai | preserve |
| automation_scheduler/deepseek_data_pull_check.py | 0 | 1 | MIGRATE_TO_SRC_AI | src.ai | preserve |
| automation_scheduler/deepseek_disagreement_queue.py | 0 | 1 | MIGRATE_TO_SRC_AI | src.ai | preserve |
| automation_scheduler/deepseek_profit_lab.py | 0 | 3 | MIGRATE_TO_SRC_AI | src.ai | preserve |
| automation_scheduler/deepseek_prompt_contracts.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/deepseek_response_validator.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/deepseek_reviewer.py | 0 | 3 | MIGRATE_TO_SRC_AI | src.ai | preserve |
| automation_scheduler/derived_feature_backfill_report.py | 0 | 2 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/derived_feature_planner.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/drawdown_controls.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/dynamical_systems_diagnostics.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/ev_line_shopper.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/experiment_history_store.py | 0 | 7 | MIGRATE_TO_SRC_RESEARCH | src.research | preserve |
| automation_scheduler/experiment_report_exporter.py | 0 | 3 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/exposure_limits.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/extreme_randomness_diagnostics.py | 2 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/extreme_randomness_report.py | 2 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/extreme_signal_red_team.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/feature_ablation_lab.py | 1 | 6 | MIGRATE_TO_SRC_RESEARCH | src.research | preserve |
| automation_scheduler/field_scorecard.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/football_availability_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/football_data_availability.py | 0 | 1 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/football_impact_calibration.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/football_impact_common.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/football_impact_red_team.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/football_impact_report.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/football_impact_schema.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/football_incentive_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/football_market_relevance.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/football_matchup_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/football_personnel_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/football_play_drive_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/football_role_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/golf_approach_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/golf_availability_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/golf_course_fit_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/golf_data_availability.py | 0 | 1 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/golf_field_tournament_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/golf_impact_calibration.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/golf_impact_common.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/golf_impact_readiness.py | 2 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/golf_impact_red_team.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/golf_impact_report.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/golf_incentive_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/golf_market_relevance.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/golf_off_tee_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/golf_short_game_putting_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/golf_strokes_gained_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/golf_weather_wave_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/graph_relationship_mapper.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/hard_gate_policy.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/historical_backtest_bridge.py | 0 | 2 | MIGRATE_TO_SRC_BACKTESTING | src.backtesting | preserve |
| automation_scheduler/historical_data_sources.py | 1 | 2 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/historical_line_movement.py | 0 | 5 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/historical_odds_importers.py | 0 | 4 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/historical_odds_sqlite.py | 0 | 8 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/hockey_availability_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/hockey_data_availability.py | 0 | 1 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/hockey_goalie_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/hockey_impact_calibration.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/hockey_impact_common.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/hockey_impact_readiness.py | 2 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/hockey_impact_red_team.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/hockey_impact_report.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/hockey_incentive_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/hockey_line_pair_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/hockey_market_relevance.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/hockey_matchup_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/hockey_possession_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/hockey_skater_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/hockey_special_teams_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/hockey_transition_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/information_theory_diagnostics.py | 0 | 1 | MIGRATE_TO_SRC_RESEARCH | src.research | preserve |
| automation_scheduler/injury_weather_adapter_contract.py | 0 | 1 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/institutional_cross_asset_adapters.py | 2 | 1 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/institutional_cross_asset_calibration.py | 1 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/institutional_cross_asset_lab.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/institutional_cross_asset_reports.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/institutional_cross_asset_scores.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/institutional_deepseek_review.py | 1 | 3 | MIGRATE_TO_SRC_AI | src.ai | preserve |
| automation_scheduler/institutional_risk_engine.py | 1 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/intelligence_readiness_report.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/kalshi_adapter_contract.py | 0 | 3 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/kalshi_monitor.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/kalshi_readonly_readiness.py | 0 | 6 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/kalshi_scoring.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/kelly_staking.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/later/__init__.py | 11 | 47 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/later/auto_execution_policy.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/later/execution_audit_log.py | 0 | 1 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/later/execution_guardrails.py | 0 | 1 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/later/execution_readiness_check.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/line_movement_data_quality_dashboard.py | 1 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/line_movement_import_contract.py | 1 | 3 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/line_movement_readiness.py | 1 | 3 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/liquidity_context_scoring.py | 1 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/liquidity_risk.py | 1 | 6 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/local_sports_history_audit.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/manifold_calibration.py | 1 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/manifold_cluster_registry.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/manifold_feature_builder.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/manifold_review_queue.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/market_clock.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/market_feature_packs.py | 0 | 2 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/market_identity_resolver.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/market_state_graph.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/market_state_manifold.py | 1 | 2 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/market_structure.py | 0 | 8 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/micro_outcome_calibration.py | 2 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/middle_opportunity_detector.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/middles/__init__.py | 11 | 47 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/middles/alt_line_middle.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/middles/key_number_middle.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/middles/middle_ev_simulator.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/middles/prop_middle.py | 0 | 2 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/middles/push_corridor_middle.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/middles/spread_middle.py | 1 | 2 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/middles/team_total_middle.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/middles/total_middle.py | 1 | 3 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/model_data_field_catalog.py | 1 | 6 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/model_input_coverage.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/model_performance_report.py | 0 | 3 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/model_recheck_runner.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/ncaaf_collegefootballdata_adapter.py | 0 | 2 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/news_event_monitor.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/news_events_adapter_contract.py | 0 | 1 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/nfl_coaching_adapters.py | 0 | 2 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/nfl_coaching_feature_builders.py | 0 | 3 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/nfl_coaching_sources.py | 0 | 5 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/nfl_cutoff_week_features.py | 0 | 2 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/nfl_historical_pattern_lab.py | 0 | 2 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/nfl_open_data_adapters.py | 0 | 2 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/nfl_open_data_backfill.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/nfl_open_data_feature_builders.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/nfl_open_data_feature_readiness.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/nfl_open_data_field_catalog.py | 0 | 3 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/nfl_open_data_source_exhaustion.py | 0 | 1 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/nfl_open_data_sources.py | 0 | 2 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/no_vig_pricing.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/odds_line_monitor.py | 0 | 2 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/odds_math.py | 0 | 3 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/open_sports_history_backfill.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/open_sports_history_import.py | 0 | 5 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/open_sports_history_sources.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/opportunity_scoring.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/ops_workflow.py | 0 | 3 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/outcome_migration.py | 1 | 5 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/outcome_store.py | 1 | 9 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/owner_approval_gate.py | 1 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/paper_decision_ledger.py | 0 | 22 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/paper_trade_ledger.py | 0 | 17 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/pattern_calibration.py | 2 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/pattern_review_queue.py | 3 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/performance_metrics.py | 1 | 3 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/player_prop_monitor.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/player_props_adapter_contract.py | 0 | 1 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/prediction_market_manifold_mapper.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/prediction_market_outcome_candidates.py | 0 | 6 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/provider_allowlist.py | 4 | 3 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/random_baseline_comparison.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/random_matrix_risk.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/report_writer.py | 0 | 2 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/representation_feature_builder.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/response_compactor.py | 2 | 18 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/review_queue.py | 8 | 25 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/risk_limit_guard.py | 1 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/risk_of_ruin.py | 1 | 2 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/run_context.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/scheduler_config.py | 3 | 19 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/scheduler_runner.py | 0 | 13 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/secret_safety.py | 2 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/security_event_types.py | 2 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/security_policy.py | 2 | 2 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/security_readiness_report.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/session_risk_rules.py | 1 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/snapshot_store.py | 0 | 1 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/soccer_data_availability.py | 0 | 1 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/soccer_goalkeeper_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/soccer_impact_calibration.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/soccer_impact_common.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/soccer_impact_readiness.py | 2 | 0 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/soccer_impact_red_team.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/soccer_impact_report.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/soccer_incentive_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/soccer_lineup_availability_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/soccer_market_relevance.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/soccer_matchup_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/soccer_player_role_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/soccer_possession_value_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/soccer_pressing_transition_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/soccer_referee_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/soccer_set_piece_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/soccer_tactical_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/source_event_link_resolver.py | 1 | 2 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/source_quality_scoring.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/sport_feature_packs.py | 0 | 3 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/sportsbook_adapter_contract.py | 0 | 3 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/sportsbook_manifold_mapper.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/stake_confidence.py | 0 | 2 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/stake_sizing_simulator.py | 0 | 2 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/stock_fundamentals_adapter_contract.py | 0 | 1 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/stock_monitor.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/stock_price_adapter_contract.py | 0 | 1 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/strategy_context_buckets.py | 2 | 0 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/strategy_disagreement.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/strategy_maturity.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/strategy_promotion.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/strategy_readiness_report.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/strategy_registry.py | 0 | 2 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/strategy_router.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/strategy_score_aggregator.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/streamlit_dashboard_data.py | 1 | 43 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/synthetic_line_movement_sandbox.py | 0 | 1 | MIGRATE_TO_SRC_BROKERAGE | src.brokerage | preserve |
| automation_scheduler/system_health.py | 1 | 2 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/tail_event_classifier.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/technical_signal_fields.py | 1 | 12 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/tennis_availability_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/tennis_data_availability.py | 0 | 1 | MIGRATE_TO_SRC_DATA | src.data | preserve |
| automation_scheduler/tennis_format_markov_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/tennis_impact_calibration.py | 0 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/tennis_impact_common.py | 0 | 0 | DELETE_READY_AFTER_PROOF | delete_batch | delete |
| automation_scheduler/tennis_impact_readiness.py | 2 | 1 | MIGRATE_TO_SRC_SERVICES | src.services | preserve |
| automation_scheduler/tennis_impact_red_team.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/tennis_impact_report.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/tennis_incentive_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/tennis_market_relevance.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/tennis_matchup_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/tennis_pressure_tiebreak_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/tennis_return_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/tennis_serve_impact.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/tennis_surface_context.py | 0 | 1 | MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER | src.market_intelligence.later | preserve |
| automation_scheduler/topological_red_team.py | 0 | 1 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
| automation_scheduler/tracy_widom_research.py | 0 | 1 | MIGRATE_TO_SRC_RESEARCH | src.research | preserve |
| automation_scheduler/universality_research_lanes.py | 0 | 1 | MIGRATE_TO_SRC_RESEARCH | src.research | preserve |
| automation_scheduler/zero_dte_fixture_template.py | 1 | 15 | COMPATIBILITY_WRAPPER_ONLY | compatibility wrapper | preserve |
