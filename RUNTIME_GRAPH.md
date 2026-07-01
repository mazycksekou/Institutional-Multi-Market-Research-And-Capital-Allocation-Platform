# Runtime Graph

| path | runtime | runtime_importers |
| --- | --- | --- |
| src/services/scheduler_config.py | 54 | src/ai/deepseek_daily_report.py, src/ai/deepseek_data_pull_check.py, src/ai/deepseek_disagreement_queue.py, src/ai/deepseek_profit_lab.py, src/ai/deepseek_response_validator.py |
| src/security/policy.py | 51 | src/ai/deepseek_response_validator.py, src/analytics/advanced_red_team_provider_policy.py, src/analytics/advanced_red_team_report.py, src/analytics/advanced_shape_diagnostics.py, src/analytics/bayesian_structural_baseline.py |
| src/data/data_paths.py | 46 | src/ai/deepseek_daily_report.py, src/ai/deepseek_data_pull_check.py, src/ai/deepseek_disagreement_queue.py, src/ai/deepseek_profit_lab.py, src/ai/institutional_deepseek_review.py |
| src/security/secret_safety.py | 21 | src/ai/deepseek_response_validator.py, src/analytics/advanced_red_team_report.py, src/analytics/advanced_shape_diagnostics.py, src/analytics/strategy_readiness_report.py, src/analytics/topological_red_team.py |
| src/core/math_utils.py | 17 | src/api/model_card_service.py, src/core/backtester.py, src/core/clv.py, src/core/cross_book_line_comparator.py, src/core/ev_line_shopper.py |
| src/market_intelligence/baseball_impact_common.py | 17 | src/analytics/baseball_impact_calibration.py, src/analytics/baseball_impact_red_team.py, src/analytics/baseball_impact_report.py, src/market_intelligence/baseball_availability_context.py, src/market_intelligence/baseball_batter_impact.py |
| src/market_intelligence/soccer_impact_common.py | 17 | src/analytics/soccer_impact_calibration.py, src/analytics/soccer_impact_red_team.py, src/analytics/soccer_impact_report.py, src/market_intelligence/soccer_data_availability.py, src/market_intelligence/soccer_goalkeeper_context.py |
| src/brokerage/contracts.py | 16 | src/brokerage/__init__.py, src/brokerage/_execution_core.py, src/brokerage/accounts.py, src/brokerage/client_factory.py, src/brokerage/credentials.py |
| src/market_intelligence/_shared.py | 16 | src/market_intelligence/catalysts.py, src/market_intelligence/confidence.py, src/market_intelligence/flow.py, src/market_intelligence/liquidity.py, src/market_intelligence/manifold.py |
| src/market_intelligence/combat_impact_common.py | 16 | src/analytics/combat_impact_calibration.py, src/analytics/combat_impact_red_team.py, src/analytics/combat_impact_report.py, src/market_intelligence/combat_availability_context.py, src/market_intelligence/combat_damage_durability_context.py |
| src/market_intelligence/golf_impact_common.py | 16 | src/analytics/golf_impact_calibration.py, src/analytics/golf_impact_red_team.py, src/analytics/golf_impact_report.py, src/market_intelligence/golf_approach_impact.py, src/market_intelligence/golf_availability_context.py |
| src/market_intelligence/hockey_impact_common.py | 16 | src/analytics/hockey_impact_calibration.py, src/analytics/hockey_impact_red_team.py, src/analytics/hockey_impact_report.py, src/market_intelligence/hockey_availability_context.py, src/market_intelligence/hockey_data_availability.py |
| src/providers/validation.py | 16 | src/providers/__init__.py, src/providers/base.py, src/providers/injury_weather_adapter_contract.py, src/providers/news_events_adapter_contract.py, src/providers/player_props_adapter_contract.py |
| src/market_intelligence/tennis_impact_common.py | 15 | src/analytics/tennis_impact_calibration.py, src/analytics/tennis_impact_red_team.py, src/analytics/tennis_impact_report.py, src/market_intelligence/tennis_availability_context.py, src/market_intelligence/tennis_data_availability.py |
| src/connectors/errors.py | 14 | src/connectors/__init__.py, src/connectors/market_data/adapter.py, src/connectors/market_data/read_only.py, src/connectors/odds_data/adapter.py, src/connectors/odds_data/live_client.py |
| src/providers/contracts.py | 14 | src/providers/__init__.py, src/providers/base.py, src/providers/health.py, src/providers/prediction_markets/adapters.py, src/providers/prediction_markets/contracts.py |
| src/analytics/institutional/__init__.py | 13 | src/analytics/institutional/alternative_investments.py, src/analytics/institutional/credit_risk_models.py, src/analytics/institutional/derivatives_hedging.py, src/analytics/institutional/execution_cost_models.py, src/analytics/institutional/factor_risk_models.py |
| src/analytics/institutional/alternative_investments.py | 13 | src/analytics/institutional/model_router.py |
| src/analytics/institutional/credit_risk_models.py | 13 | src/analytics/institutional/model_router.py |
| src/analytics/institutional/derivatives_hedging.py | 13 | src/analytics/institutional/model_router.py |
| src/analytics/institutional/execution_cost_models.py | 13 | src/analytics/institutional/model_router.py |
| src/analytics/institutional/factor_risk_models.py | 13 | src/analytics/institutional/model_router.py |
| src/analytics/institutional/fixed_income_rates.py | 13 | src/analytics/institutional/model_router.py |
| src/analytics/institutional/liability_retirement_models.py | 13 | src/analytics/institutional/model_router.py |
| src/analytics/institutional/macro_regime_models.py | 13 | src/analytics/institutional/model_router.py |
| src/analytics/institutional/model_governance.py | 13 | src/analytics/institutional/model_router.py |
| src/analytics/institutional/model_router.py | 13 |  |
| src/analytics/institutional/performance_attribution.py | 13 | src/analytics/institutional/model_router.py |
| src/analytics/institutional/portfolio_construction.py | 13 | src/analytics/institutional/model_router.py |
| src/analytics/institutional/tax_aware_models.py | 13 | src/analytics/institutional/model_router.py |
| src/brokerage/approval.py | 13 | src/brokerage/__init__.py, src/brokerage/activation.py, src/brokerage/approval_evidence.py, src/brokerage/client_factory.py, src/brokerage/credential_loader.py |
| src/market_intelligence/football_impact_schema.py | 12 | src/analytics/football_impact_calibration.py, src/analytics/football_impact_report.py, src/market_intelligence/football_availability_context.py, src/market_intelligence/football_data_availability.py, src/market_intelligence/football_impact_common.py |
| src/market_intelligence/basketball_player_impact_common.py | 11 | src/analytics/basketball_player_impact_calibration.py, src/analytics/basketball_player_impact_red_team.py, src/market_intelligence/basketball_incentive_context.py, src/market_intelligence/basketball_lineup_matchup_context.py, src/market_intelligence/basketball_market_relevance.py |
| src/providers/health.py | 11 | src/ai/deepseek_profit_lab.py, src/providers/__init__.py, src/providers/base.py, src/providers/prediction_markets/adapters.py, src/providers/sportsbooks/adapters.py |
| src/providers/policy/allowlist.py | 11 | src/analytics/advanced_red_team_provider_policy.py, src/brokerage/readiness_support.py, src/providers/policy/__init__.py, src/providers/policy/write_firewall.py, src/security/ai_provider_security.py |
| src/api/schemas/automation.py | 9 | main.py, src/api/automation_data_source_routes.py, src/api/automation_deepseek_routes.py, src/api/automation_institutional_lab_routes.py, src/api/automation_manifold_routes.py |
| src/brokerage/orders.py | 9 | src/brokerage/__init__.py, src/brokerage/_execution_core.py, src/brokerage/dry_run.py, src/brokerage/dry_run_ledger.py, src/brokerage/live_submit.py |
| src/market_intelligence/middle_opportunity_detector.py | 9 | src/market_intelligence/middles/alt_line_middle.py, src/market_intelligence/middles/key_number_middle.py, src/market_intelligence/middles/prop_middle.py, src/market_intelligence/middles/push_corridor_middle.py, src/market_intelligence/middles/spread_middle.py |
| src/market_intelligence/report.py | 9 | src/market_intelligence/__init__.py, src/market_intelligence/crypto.py, src/market_intelligence/futures.py, src/market_intelligence/impact.py, src/market_intelligence/manifold.py |
| src/providers/policy/secret_policy.py | 9 | src/providers/policy/__init__.py, src/providers/policy/write_firewall.py, src/providers/registry.py, src/services/odds_runtime_bridge.py, src/services/prediction_market_runtime_bridge.py |
| src/providers/registry.py | 9 | src/providers/__init__.py, src/providers/kalshi_readonly_readiness.py, src/services/automation_scheduler_facade.py, src/services/cadence_controller.py, src/services/prediction_market_runtime_bridge.py |
| src/providers/sportsbooks/contracts.py | 9 | src/providers/sportsbooks/__init__.py, src/providers/sportsbooks/adapters.py, src/services/odds_runtime_bridge.py |
| src/services/ledger_service.py | 9 | src/ai/institutional_deepseek_review.py, src/brokerage/readiness.py, src/market_intelligence/institutional_cross_asset_lab.py, src/security/ai_provider_security.py, src/security/owner_approval_gate.py |
| src/analytics/review_queue.py | 8 | src/ai/deepseek_profit_lab.py, src/analytics/calibration.py, src/analytics/calibration_collector.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/providers/institutional_cross_asset_adapters.py |
| src/brokerage/kill_switch.py | 8 | src/brokerage/__init__.py, src/brokerage/activation.py, src/brokerage/credential_loader.py, src/brokerage/deployment_policy.py, src/brokerage/deployment_readiness.py |
| src/core/opportunity_scanner.py | 8 | src/api/market_utility_routes.py, src/market_intelligence/arbitrage/exchange_arbitrage.py, src/market_intelligence/arbitrage/prediction_market_arbitrage.py, src/market_intelligence/arbitrage/three_way_arbitrage.py, src/market_intelligence/arbitrage/two_way_arbitrage.py |
| src/market_intelligence/manifold_feature_builder.py | 8 | src/analytics/intelligence_readiness_report.py, src/analytics/manifold_calibration.py, src/market_intelligence/cross_asset_embedding_router.py, src/market_intelligence/manifold.py, src/market_intelligence/manifold_cluster_registry.py |
| src/market_intelligence/targets.py | 8 | src/market_intelligence/__init__.py, src/market_intelligence/crypto.py, src/market_intelligence/futures.py, src/market_intelligence/impact.py, src/market_intelligence/manifold.py |
| src/providers/base.py | 8 | src/providers/__init__.py, src/providers/prediction_markets/adapters.py, src/providers/sportsbooks/adapters.py, src/providers/zero_dte_stocks/provider.py, src/services/scheduler_runner.py |
| src/providers/normalization.py | 8 | src/providers/__init__.py, src/providers/base.py, src/providers/prediction_markets/contracts.py, src/providers/sportsbooks/contracts.py, src/providers/zero_dte_stocks/contracts.py |

