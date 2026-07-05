# Repository Discovery Dependency Graph

## Per-file dependency summary

## `api_server.py`

- imports_from: `none`
- imported_by: `tests/support/action_imports.py`
- runtime_callers: `none`
- test_callers: `tests/support/action_imports.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `main`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `main.py`

- imports_from: `src.analytics.model_governance, src.analytics.model_governance.model_inventory, src.api.automation_core_routes, src.api.automation_data_source_routes, src.api.automation_deepseek_routes, src.api.automation_institutional_lab_routes, src.api.automation_manifold_routes, src.api.automation_review_outcomes_routes, src.api.automation_run_once_routes, src.api.automation_small_account_routes, src.api.automation_sport_impact_routes, src.api.bet_csv_routes, src.api.betting_action_routes, src.api.betting_metadata_routes, src.api.debug_routes, src.api.governance_routes, src.api.market_metadata_routes, src.api.market_utility_routes, src.api.model_backtest_routes, src.api.model_card_service, src.api.performance_routes, src.api.provider_status_routes, src.api.quant_routes, src.api.schemas.automation, src.api.schemas.bet_csv, src.api.schemas.performance, src.api.schemas.quant, src.api.stock_analysis_routes, src.api.system_routes, src.core.market_pricing, src.core.model_probability, src.core.quant_engine, src.market_intelligence.multi_sport_model_registry, src.providers.compat, src.providers.provider_router, src.services.action_betting_service, src.services.automation_scheduler_facade, src.services.bet_csv_service, src.services.bet_decision_engine, src.services.bet_log, src.services.screenshot_intake`
- imported_by: `api_server.py`
- runtime_callers: `api_server.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `api_server.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `scripts/analyze_json_data.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `scripts/daily_data_hygiene.py`

- imports_from: `scripts.r2_archive_pipeline, src.storage.archive_manifest`
- imported_by: `tests/test_phase10k8zfe2_daily_data_hygiene_scheduler.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zfe2_daily_data_hygiene_scheduler.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `reports/daily_data_hygiene`

## `scripts/init_sports_master_db.py`

- imports_from: `src.core.math_utils`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `scripts/ops_check.py`

- imports_from: `src.services.ops_workflow, src.services.repo_inventory`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `scripts/r2_archive_pipeline.py`

- imports_from: `src.storage.archive_manifest, src.storage.r2_archive_adapter`
- imported_by: `scripts/daily_data_hygiene.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `scripts/daily_data_hygiene.py`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `scripts/smoke_test.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/__init__.py`

- imports_from: `none`
- imported_by: `tests/test_phase10k5_core_arbitrage_engine.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k5_core_arbitrage_engine.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/__init__.py`

- imports_from: `src.ai.contracts, src.ai.disabled_client, src.ai.prompt_policy, src.ai.readiness`
- imported_by: `tests/test_phase10k8zi6_ai_llm_boundary_audit.py, tests/test_phase10k8zi7_ai_boundary_scaffold.py, tests/test_phase10k8zi9_ai_boundary_checkpoint.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zi6_ai_llm_boundary_audit.py, tests/test_phase10k8zi7_ai_boundary_scaffold.py, tests/test_phase10k8zi9_ai_boundary_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/contracts.py`

- imports_from: `none`
- imported_by: `src/ai/__init__.py, src/ai/readiness.py, tests/test_phase10k8zi7_ai_boundary_scaffold.py`
- runtime_callers: `src/ai/__init__.py, src/ai/readiness.py`
- test_callers: `tests/test_phase10k8zi7_ai_boundary_scaffold.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/deepseek_daily_report.py`

- imports_from: `src.ai.deepseek_response_validator, src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/ai/deepseek_profit_lab.py`
- runtime_callers: `src/ai/deepseek_profit_lab.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/deepseek_data_pull_check.py`

- imports_from: `src.data, src.data.data_paths, src.market_intelligence.prediction_market_outcome_candidates, src.providers.kalshi_readonly_readiness, src.services.scheduler_config`
- imported_by: `tests/test_deepseek_data_pull_check_contract.py`
- runtime_callers: `none`
- test_callers: `tests/test_deepseek_data_pull_check_contract.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/deepseek_disagreement_queue.py`

- imports_from: `src.ai.deepseek_response_validator, src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/ai/deepseek_profit_lab.py, src/services/automation_scheduler_facade.py`
- runtime_callers: `src/ai/deepseek_profit_lab.py, src/services/automation_scheduler_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/deepseek_profit_lab.py`

- imports_from: `src.ai.deepseek_daily_report, src.ai.deepseek_disagreement_queue, src.ai.deepseek_prompt_contracts, src.ai.deepseek_response_validator, src.analytics.calibration, src.analytics.review_queue, src.data.data_paths, src.providers.health, src.security.ai_provider_security, src.services.execution_service, src.services.outcome_store, src.services.scheduler_config, src.services.security_readiness`
- imported_by: `src/services/automation_scheduler_facade.py, tests/test_deepseek_profit_lab.py`
- runtime_callers: `src/services/automation_scheduler_facade.py`
- test_callers: `tests/test_deepseek_profit_lab.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/deepseek_prompt_contracts.py`

- imports_from: `none`
- imported_by: `src/ai/deepseek_profit_lab.py`
- runtime_callers: `src/ai/deepseek_profit_lab.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/deepseek_response_validator.py`

- imports_from: `src.security.policy, src.security.secret_safety, src.services.scheduler_config`
- imported_by: `src/ai/deepseek_daily_report.py, src/ai/deepseek_disagreement_queue.py, src/ai/deepseek_profit_lab.py`
- runtime_callers: `src/ai/deepseek_daily_report.py, src/ai/deepseek_disagreement_queue.py, src/ai/deepseek_profit_lab.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/deepseek_reviewer.py`

- imports_from: `src.services.scheduler_config`
- imported_by: `src/analytics/calibration_collector.py, src/services/automation_scheduler_facade.py`
- runtime_callers: `src/analytics/calibration_collector.py, src/services/automation_scheduler_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/disabled_client.py`

- imports_from: `none`
- imported_by: `src/ai/__init__.py, tests/test_phase10k8zi7_ai_boundary_scaffold.py`
- runtime_callers: `src/ai/__init__.py`
- test_callers: `tests/test_phase10k8zi7_ai_boundary_scaffold.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/evaluation/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/institutional_deepseek_review.py`

- imports_from: `src.data.data_paths, src.providers.institutional_cross_asset_adapters, src.services.ledger_service`
- imported_by: `src/market_intelligence/institutional_cross_asset_lab.py, src/services/automation_scheduler_facade.py`
- runtime_callers: `src/market_intelligence/institutional_cross_asset_lab.py, src/services/automation_scheduler_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/llm/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/models/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/policy/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/prompt_policy.py`

- imports_from: `none`
- imported_by: `src/ai/__init__.py, tests/test_phase10k8zi7_ai_boundary_scaffold.py`
- runtime_callers: `src/ai/__init__.py`
- test_callers: `tests/test_phase10k8zi7_ai_boundary_scaffold.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/prompts/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/ai/readiness.py`

- imports_from: `src.ai.contracts`
- imported_by: `src/ai/__init__.py, tests/test_phase10k8zi7_ai_boundary_scaffold.py`
- runtime_callers: `src/ai/__init__.py`
- test_callers: `tests/test_phase10k8zi7_ai_boundary_scaffold.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/__init__.py`

- imports_from: `src.analytics.attribution, src.analytics.contracts, src.analytics.governance, src.analytics.performance, src.analytics.reports`
- imported_by: `tests/test_phase10k8zhn_analytics_foundation.py, tests/test_phase10k8zhp_legacy_analytics_research_owner_map.py, tests/test_phase10k8zhq_analytics_research_checkpoint.py, tests/test_phase10k8zhz_analytics_research_wrapper_delete_proof.py, tests/test_phase10k8zi1_analytics_research_compatibility_test_retirement.py, tests/test_phase10k8zi4_final_analytics_research_delete_readiness.py, tests/test_phase10k8zi5_analytics_research_wrapper_deletion.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zhn_analytics_foundation.py, tests/test_phase10k8zhp_legacy_analytics_research_owner_map.py, tests/test_phase10k8zhq_analytics_research_checkpoint.py, tests/test_phase10k8zhz_analytics_research_wrapper_delete_proof.py, tests/test_phase10k8zi1_analytics_research_compatibility_test_retirement.py, tests/test_phase10k8zi4_final_analytics_research_delete_readiness.py, tests/test_phase10k8zi5_analytics_research_wrapper_deletion.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zhp_legacy_analytics_research_owner_map.py, tests/test_phase10k8zhz_analytics_research_wrapper_delete_proof.py, tests/test_phase10k8zi1_analytics_research_compatibility_test_retirement.py, tests/test_phase10k8zi5_analytics_research_wrapper_deletion.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/advanced_red_team_provider_policy.py`

- imports_from: `src.providers.policy.allowlist, src.security.policy`
- imported_by: `src/analytics/advanced_shape_diagnostics.py`
- runtime_callers: `src/analytics/advanced_shape_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/advanced_red_team_report.py`

- imports_from: `src.analytics.advanced_shape_diagnostics, src.data.data_paths, src.security.policy, src.security.secret_safety, src.services.scheduler_config`
- imported_by: `tests/test_advanced_red_team.py`
- runtime_callers: `none`
- test_callers: `tests/test_advanced_red_team.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/advanced_shape_diagnostics.py`

- imports_from: `src.analytics.advanced_red_team_provider_policy, src.analytics.bayesian_structural_baseline, src.analytics.dynamical_systems_diagnostics, src.analytics.information_theory_diagnostics, src.analytics.topological_red_team, src.core.conformal_uncertainty, src.research.causal_discovery_research, src.research.contrastive_embedding_diagnostics, src.security.policy, src.security.secret_safety`
- imported_by: `src/analytics/advanced_red_team_report.py, src/research/contrastive_embedding_diagnostics.py`
- runtime_callers: `src/analytics/advanced_red_team_report.py, src/research/contrastive_embedding_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/attribution.py`

- imports_from: `src.analytics.contracts`
- imported_by: `src/analytics/__init__.py`
- runtime_callers: `src/analytics/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/baseball_impact_calibration.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/baseball_impact_red_team.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/baseball_impact_report.py`

- imports_from: `src.analytics.baseball_impact_calibration, src.analytics.baseball_impact_red_team, src.market_intelligence.baseball_availability_context, src.market_intelligence.baseball_batter_impact, src.market_intelligence.baseball_bullpen_context, src.market_intelligence.baseball_data_availability, src.market_intelligence.baseball_defense_baserunning_context, src.market_intelligence.baseball_impact_common, src.market_intelligence.baseball_incentive_context, src.market_intelligence.baseball_lineup_context, src.market_intelligence.baseball_market_relevance, src.market_intelligence.baseball_matchup_context, src.market_intelligence.baseball_park_weather_umpire_context, src.market_intelligence.baseball_pitcher_impact, src.market_intelligence.baseball_run_value_impact`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/basketball_player_impact_calibration.py`

- imports_from: `src.market_intelligence.basketball_player_impact_common`
- imported_by: `src/market_intelligence/basketball_player_impact.py`
- runtime_callers: `src/market_intelligence/basketball_player_impact.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/basketball_player_impact_red_team.py`

- imports_from: `src.market_intelligence.basketball_player_impact_common`
- imported_by: `src/market_intelligence/basketball_player_impact.py`
- runtime_callers: `src/market_intelligence/basketball_player_impact.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/bayesian_structural_baseline.py`

- imports_from: `src.security.policy`
- imported_by: `src/analytics/advanced_shape_diagnostics.py`
- runtime_callers: `src/analytics/advanced_shape_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/calibration.py`

- imports_from: `src.analytics.review_queue, src.brokerage.paper_decision_ledger, src.data.data_paths, src.services.outcome_store, src.services.scheduler_config`
- imported_by: `src/ai/deepseek_profit_lab.py, src/analytics/calibration_collector.py, src/backtesting/backtesting_engine.py, src/services/automation_scheduler_facade.py, src/services/scheduler_runner.py`
- runtime_callers: `src/ai/deepseek_profit_lab.py, src/analytics/calibration_collector.py, src/backtesting/backtesting_engine.py, src/services/automation_scheduler_facade.py, src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/calibration_collector.py`

- imports_from: `src.ai.deepseek_reviewer, src.analytics.calibration, src.analytics.review_queue, src.brokerage.paper_decision_ledger, src.data.data_paths, src.services.outcome_store, src.services.prediction_market_runtime_bridge, src.services.scheduler_config, src.services.scheduler_runner, src.services.settlement_service`
- imported_by: `src/services/automation_scheduler_facade.py, src/services/collector_scheduled_runner.py, src/services/streamlit_dashboard_facade.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- runtime_callers: `src/services/automation_scheduler_facade.py, src/services/collector_scheduled_runner.py, src/services/streamlit_dashboard_facade.py`
- test_callers: `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py, src/services/streamlit_dashboard_facade.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/calibration_tracker.py`

- imports_from: `none`
- imported_by: `src/backtesting/backtesting_engine.py`
- runtime_callers: `src/backtesting/backtesting_engine.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/combat_impact_calibration.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/combat_impact_red_team.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/combat_impact_report.py`

- imports_from: `src.analytics.combat_impact_calibration, src.analytics.combat_impact_red_team, src.market_intelligence.combat_availability_context, src.market_intelligence.combat_damage_durability_context, src.market_intelligence.combat_data_availability, src.market_intelligence.combat_grappling_control_impact, src.market_intelligence.combat_impact_common, src.market_intelligence.combat_impact_readiness, src.market_intelligence.combat_incentive_context, src.market_intelligence.combat_market_relevance, src.market_intelligence.combat_matchup_context, src.market_intelligence.combat_pace_cardio_context, src.market_intelligence.combat_phase_control_context, src.market_intelligence.combat_ruleset_referee_judging_context, src.market_intelligence.combat_striking_impact`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/contracts.py`

- imports_from: `none`
- imported_by: `src/analytics/__init__.py, src/analytics/attribution.py, src/analytics/governance.py, src/analytics/performance.py`
- runtime_callers: `src/analytics/__init__.py, src/analytics/attribution.py, src/analytics/governance.py, src/analytics/performance.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/derived_feature_backfill_report.py`

- imports_from: `src.data, src.data.data_paths, src.market_intelligence.nfl_coaching_feature_builders, src.market_intelligence.nfl_cutoff_week_features, src.providers.nfl_open_data_feature_builders, src.services.scheduler_config`
- imported_by: `tests/test_open_sports_history_derived_features.py`
- runtime_callers: `none`
- test_callers: `tests/test_open_sports_history_derived_features.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/dynamical_systems_diagnostics.py`

- imports_from: `src.security.policy`
- imported_by: `src/analytics/advanced_shape_diagnostics.py`
- runtime_callers: `src/analytics/advanced_shape_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/extreme_signal_red_team.py`

- imports_from: `src.research.extreme_randomness_diagnostics, src.security.policy`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/field_scorecard.py`

- imports_from: `src.services.scheduler_config`
- imported_by: `tests/test_field_scorecard.py`
- runtime_callers: `none`
- test_callers: `tests/test_field_scorecard.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/football_impact_calibration.py`

- imports_from: `src.market_intelligence.football_impact_schema`
- imported_by: `src/analytics/football_impact_report.py`
- runtime_callers: `src/analytics/football_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/football_impact_red_team.py`

- imports_from: `src.market_intelligence.football_impact_common`
- imported_by: `src/analytics/football_impact_report.py`
- runtime_callers: `src/analytics/football_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/football_impact_report.py`

- imports_from: `src.analytics.football_impact_calibration, src.analytics.football_impact_red_team, src.market_intelligence.football_availability_context, src.market_intelligence.football_data_availability, src.market_intelligence.football_impact_schema, src.market_intelligence.football_incentive_context, src.market_intelligence.football_market_relevance, src.market_intelligence.football_matchup_context, src.market_intelligence.football_personnel_context, src.market_intelligence.football_play_drive_impact, src.market_intelligence.football_role_impact`
- imported_by: `tests/test_football_impact_intelligence.py`
- runtime_callers: `none`
- test_callers: `tests/test_football_impact_intelligence.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/golf_impact_calibration.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/golf_impact_red_team.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/golf_impact_report.py`

- imports_from: `src.analytics.golf_impact_calibration, src.analytics.golf_impact_red_team, src.market_intelligence.golf_approach_impact, src.market_intelligence.golf_availability_context, src.market_intelligence.golf_course_fit_context, src.market_intelligence.golf_data_availability, src.market_intelligence.golf_field_tournament_context, src.market_intelligence.golf_impact_common, src.market_intelligence.golf_impact_readiness, src.market_intelligence.golf_incentive_context, src.market_intelligence.golf_market_relevance, src.market_intelligence.golf_off_tee_impact, src.market_intelligence.golf_short_game_putting_context, src.market_intelligence.golf_strokes_gained_impact, src.market_intelligence.golf_weather_wave_context`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/governance.py`

- imports_from: `src.analytics.contracts`
- imported_by: `src/analytics/__init__.py, src/analytics/model_governance/__init__.py, tests/test_governance_health.py, tests/test_phase10k8zhv_analytics_downstream_redirection.py`
- runtime_callers: `src/analytics/__init__.py, src/analytics/model_governance/__init__.py`
- test_callers: `tests/test_governance_health.py, tests/test_phase10k8zhv_analytics_downstream_redirection.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `data/governance_audit, data/performance_reports`

## `src/analytics/hockey_impact_calibration.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/hockey_impact_red_team.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/hockey_impact_report.py`

- imports_from: `src.analytics.hockey_impact_calibration, src.analytics.hockey_impact_red_team, src.market_intelligence.hockey_availability_context, src.market_intelligence.hockey_data_availability, src.market_intelligence.hockey_goalie_impact, src.market_intelligence.hockey_impact_common, src.market_intelligence.hockey_impact_readiness, src.market_intelligence.hockey_incentive_context, src.market_intelligence.hockey_line_pair_context, src.market_intelligence.hockey_market_relevance, src.market_intelligence.hockey_matchup_context, src.market_intelligence.hockey_possession_impact, src.market_intelligence.hockey_skater_impact, src.market_intelligence.hockey_special_teams_context, src.market_intelligence.hockey_transition_context`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/information_theory_diagnostics.py`

- imports_from: `src.security.policy`
- imported_by: `src/analytics/advanced_shape_diagnostics.py`
- runtime_callers: `src/analytics/advanced_shape_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/__init__.py`

- imports_from: `none`
- imported_by: `src/analytics/institutional/alternative_investments.py, src/analytics/institutional/credit_risk_models.py, src/analytics/institutional/derivatives_hedging.py, src/analytics/institutional/execution_cost_models.py, src/analytics/institutional/factor_risk_models.py, src/analytics/institutional/fixed_income_rates.py, src/analytics/institutional/liability_retirement_models.py, src/analytics/institutional/macro_regime_models.py, src/analytics/institutional/model_governance.py, src/analytics/institutional/model_router.py, src/analytics/institutional/performance_attribution.py, src/analytics/institutional/portfolio_construction.py, src/analytics/institutional/tax_aware_models.py, tests/test_institutional_model_router.py`
- runtime_callers: `src/analytics/institutional/alternative_investments.py, src/analytics/institutional/credit_risk_models.py, src/analytics/institutional/derivatives_hedging.py, src/analytics/institutional/execution_cost_models.py, src/analytics/institutional/factor_risk_models.py, src/analytics/institutional/fixed_income_rates.py, src/analytics/institutional/liability_retirement_models.py, src/analytics/institutional/macro_regime_models.py, src/analytics/institutional/model_governance.py, src/analytics/institutional/model_router.py, src/analytics/institutional/performance_attribution.py, src/analytics/institutional/portfolio_construction.py, src/analytics/institutional/tax_aware_models.py`
- test_callers: `tests/test_institutional_model_router.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/alternative_investments.py`

- imports_from: `src.analytics.institutional`
- imported_by: `src/analytics/institutional/model_router.py, tests/test_institutional_alternative_investments.py`
- runtime_callers: `src/analytics/institutional/model_router.py`
- test_callers: `tests/test_institutional_alternative_investments.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/credit_risk_models.py`

- imports_from: `src.analytics.institutional`
- imported_by: `src/analytics/institutional/model_router.py, tests/test_institutional_credit_risk_models.py`
- runtime_callers: `src/analytics/institutional/model_router.py`
- test_callers: `tests/test_institutional_credit_risk_models.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/derivatives_hedging.py`

- imports_from: `src.analytics.institutional`
- imported_by: `src/analytics/institutional/model_router.py, tests/test_institutional_derivatives_hedging.py`
- runtime_callers: `src/analytics/institutional/model_router.py`
- test_callers: `tests/test_institutional_derivatives_hedging.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/execution_cost_models.py`

- imports_from: `src.analytics.institutional`
- imported_by: `src/analytics/institutional/model_router.py, tests/test_institutional_execution_cost_models.py`
- runtime_callers: `src/analytics/institutional/model_router.py`
- test_callers: `tests/test_institutional_execution_cost_models.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/factor_risk_models.py`

- imports_from: `src.analytics.institutional`
- imported_by: `src/analytics/institutional/model_router.py, tests/test_institutional_factor_risk_models.py`
- runtime_callers: `src/analytics/institutional/model_router.py`
- test_callers: `tests/test_institutional_factor_risk_models.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/fixed_income_rates.py`

- imports_from: `src.analytics.institutional`
- imported_by: `src/analytics/institutional/model_router.py, tests/test_institutional_fixed_income_rates.py`
- runtime_callers: `src/analytics/institutional/model_router.py`
- test_callers: `tests/test_institutional_fixed_income_rates.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/liability_retirement_models.py`

- imports_from: `src.analytics.institutional`
- imported_by: `src/analytics/institutional/model_router.py, tests/test_institutional_liability_retirement_models.py`
- runtime_callers: `src/analytics/institutional/model_router.py`
- test_callers: `tests/test_institutional_liability_retirement_models.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/macro_regime_models.py`

- imports_from: `src.analytics.institutional`
- imported_by: `src/analytics/institutional/model_router.py, tests/test_institutional_macro_regime_models.py`
- runtime_callers: `src/analytics/institutional/model_router.py`
- test_callers: `tests/test_institutional_macro_regime_models.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/model_governance.py`

- imports_from: `src.analytics.institutional`
- imported_by: `src/analytics/institutional/model_router.py, tests/test_institutional_model_governance.py`
- runtime_callers: `src/analytics/institutional/model_router.py`
- test_callers: `tests/test_institutional_model_governance.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/model_router.py`

- imports_from: `src.analytics.institutional, src.analytics.institutional.alternative_investments, src.analytics.institutional.credit_risk_models, src.analytics.institutional.derivatives_hedging, src.analytics.institutional.execution_cost_models, src.analytics.institutional.factor_risk_models, src.analytics.institutional.fixed_income_rates, src.analytics.institutional.liability_retirement_models, src.analytics.institutional.macro_regime_models, src.analytics.institutional.model_governance, src.analytics.institutional.performance_attribution, src.analytics.institutional.portfolio_construction, src.analytics.institutional.tax_aware_models`
- imported_by: `tests/test_institutional_model_router.py`
- runtime_callers: `none`
- test_callers: `tests/test_institutional_model_router.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/performance_attribution.py`

- imports_from: `src.analytics.institutional`
- imported_by: `src/analytics/institutional/model_router.py, tests/test_institutional_performance_attribution.py`
- runtime_callers: `src/analytics/institutional/model_router.py`
- test_callers: `tests/test_institutional_performance_attribution.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/portfolio_construction.py`

- imports_from: `src.analytics.institutional`
- imported_by: `src/analytics/institutional/model_router.py, tests/test_institutional_portfolio_construction.py`
- runtime_callers: `src/analytics/institutional/model_router.py`
- test_callers: `tests/test_institutional_portfolio_construction.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional/tax_aware_models.py`

- imports_from: `src.analytics.institutional`
- imported_by: `src/analytics/institutional/model_router.py, tests/test_institutional_tax_aware_models.py`
- runtime_callers: `src/analytics/institutional/model_router.py`
- test_callers: `tests/test_institutional_tax_aware_models.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional_cross_asset_calibration.py`

- imports_from: `src.market_intelligence.institutional_cross_asset_scores`
- imported_by: `src/market_intelligence/institutional_cross_asset_lab.py, tests/test_institutional_cross_asset_calibration.py`
- runtime_callers: `src/market_intelligence/institutional_cross_asset_lab.py`
- test_callers: `tests/test_institutional_cross_asset_calibration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/institutional_cross_asset_reports.py`

- imports_from: `src.data.data_paths, src.providers.institutional_cross_asset_adapters, src.services.scheduler_config`
- imported_by: `src/market_intelligence/institutional_cross_asset_lab.py, src/services/streamlit_dashboard_facade.py`
- runtime_callers: `src/market_intelligence/institutional_cross_asset_lab.py, src/services/streamlit_dashboard_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/streamlit_dashboard_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/intelligence_readiness_report.py`

- imports_from: `src.data.data_paths, src.market_intelligence.data_intelligence_registry, src.market_intelligence.manifold_feature_builder, src.security.policy, src.services.outcome_store, src.services.security_readiness`
- imported_by: `src/services/automation_scheduler_facade.py, tests/test_data_intelligence_stack.py`
- runtime_callers: `src/services/automation_scheduler_facade.py`
- test_callers: `tests/test_data_intelligence_stack.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/manifold_calibration.py`

- imports_from: `src.brokerage.paper_decision_ledger, src.data.data_paths, src.market_intelligence.manifold_feature_builder, src.services.outcome_store, src.services.scheduler_config`
- imported_by: `src/market_intelligence/cross_asset_manifold_router.py, src/market_intelligence/market_state_manifold.py, tests/test_market_state_manifold.py`
- runtime_callers: `src/market_intelligence/cross_asset_manifold_router.py, src/market_intelligence/market_state_manifold.py`
- test_callers: `tests/test_market_state_manifold.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/manifold_review_queue.py`

- imports_from: `src.data.data_paths, src.market_intelligence.manifold, src.services.scheduler_config`
- imported_by: `src/market_intelligence/cross_asset_manifold_router.py`
- runtime_callers: `src/market_intelligence/cross_asset_manifold_router.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/micro_outcome_calibration.py`

- imports_from: `src.services.scheduler_config`
- imported_by: `src/research/pattern_calibration.py, src/services/automation_scheduler_facade.py`
- runtime_callers: `src/research/pattern_calibration.py, src/services/automation_scheduler_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/__init__.py`

- imports_from: `src.analytics.governance, src.analytics.model_governance.governance_config, src.analytics.model_governance.model_inventory, src.analytics.reports`
- imported_by: `main.py, src/analytics/model_governance/promotion_gate.py, src/analytics/model_governance/research_evidence_gate.py, src/analytics/model_governance/review_queue_gate.py, tests/test_phase10k8zhv_analytics_downstream_redirection.py, tests/test_phase10k8zhz_analytics_research_wrapper_delete_proof.py, tests/test_phase10k8zi5_analytics_research_wrapper_deletion.py`
- runtime_callers: `src/analytics/model_governance/promotion_gate.py, src/analytics/model_governance/research_evidence_gate.py, src/analytics/model_governance/review_queue_gate.py`
- test_callers: `tests/test_phase10k8zhv_analytics_downstream_redirection.py, tests/test_phase10k8zhz_analytics_research_wrapper_delete_proof.py, tests/test_phase10k8zi5_analytics_research_wrapper_deletion.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zhz_analytics_research_wrapper_delete_proof.py, tests/test_phase10k8zi5_analytics_research_wrapper_deletion.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `data/governance_audit, data/performance_reports`

## `src/analytics/model_governance/activation_tiers.py`

- imports_from: `none`
- imported_by: `src/analytics/model_governance/model_card.py, src/analytics/model_governance/model_inventory.py, src/analytics/model_governance/promotion_gate.py, src/analytics/model_governance/review_queue_gate.py, tests/test_activation_tiers.py`
- runtime_callers: `src/analytics/model_governance/model_card.py, src/analytics/model_governance/model_inventory.py, src/analytics/model_governance/promotion_gate.py, src/analytics/model_governance/review_queue_gate.py`
- test_callers: `tests/test_activation_tiers.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/alert_gate.py`

- imports_from: `none`
- imported_by: `tests/test_alert_gate.py`
- runtime_callers: `none`
- test_callers: `tests/test_alert_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/backtest_gate.py`

- imports_from: `none`
- imported_by: `tests/test_backtest_gate.py`
- runtime_callers: `none`
- test_callers: `tests/test_backtest_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/calibration_gate.py`

- imports_from: `none`
- imported_by: `tests/test_calibration_gate.py`
- runtime_callers: `none`
- test_callers: `tests/test_calibration_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/champion_challenger.py`

- imports_from: `none`
- imported_by: `tests/test_champion_challenger.py`
- runtime_callers: `none`
- test_callers: `tests/test_champion_challenger.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/cross_book_gate.py`

- imports_from: `none`
- imported_by: `src/services/scheduler_runner.py, tests/test_cross_book_gate.py`
- runtime_callers: `src/services/scheduler_runner.py`
- test_callers: `tests/test_cross_book_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/data_lineage.py`

- imports_from: `none`
- imported_by: `src/services/scheduler_runner.py, tests/test_data_lineage.py`
- runtime_callers: `src/services/scheduler_runner.py`
- test_callers: `tests/test_data_lineage.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/data_quality_monitor.py`

- imports_from: `none`
- imported_by: `src/services/scheduler_runner.py, tests/test_data_quality_monitor.py`
- runtime_callers: `src/services/scheduler_runner.py`
- test_callers: `tests/test_data_quality_monitor.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/execution_later_gate.py`

- imports_from: `src.analytics.model_governance.governance_config`
- imported_by: `tests/test_execution_later_gate.py`
- runtime_callers: `none`
- test_callers: `tests/test_execution_later_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/governance_audit_log.py`

- imports_from: `none`
- imported_by: `tests/test_governance_audit_log.py`
- runtime_callers: `none`
- test_callers: `tests/test_governance_audit_log.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `data/governance_audit`

## `src/analytics/model_governance/governance_config.py`

- imports_from: `none`
- imported_by: `src/analytics/model_governance/__init__.py, src/analytics/model_governance/execution_later_gate.py, tests/test_governance_config.py`
- runtime_callers: `src/analytics/model_governance/__init__.py, src/analytics/model_governance/execution_later_gate.py`
- test_callers: `tests/test_governance_config.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/human_approval_gate.py`

- imports_from: `none`
- imported_by: `tests/test_human_approval_gate.py`
- runtime_callers: `none`
- test_callers: `tests/test_human_approval_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/input_quality_gate.py`

- imports_from: `none`
- imported_by: `tests/test_input_quality_gate.py`
- runtime_callers: `none`
- test_callers: `tests/test_input_quality_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/kelly_gate.py`

- imports_from: `none`
- imported_by: `tests/test_kelly_gate.py`
- runtime_callers: `none`
- test_callers: `tests/test_kelly_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/model_card.py`

- imports_from: `src.analytics.model_governance.activation_tiers`
- imported_by: `src/analytics/model_governance/promotion_gate.py, tests/test_model_card.py`
- runtime_callers: `src/analytics/model_governance/promotion_gate.py`
- test_callers: `tests/test_model_card.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/model_drift_monitor.py`

- imports_from: `none`
- imported_by: `tests/test_model_drift_monitor.py`
- runtime_callers: `none`
- test_callers: `tests/test_model_drift_monitor.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/model_inventory.py`

- imports_from: `src.analytics.model_governance.activation_tiers`
- imported_by: `main.py, src/analytics/model_governance/__init__.py, src/analytics/model_governance/model_router_registry.py, src/services/system_health.py, tests/test_model_inventory.py`
- runtime_callers: `src/analytics/model_governance/__init__.py, src/analytics/model_governance/model_router_registry.py, src/services/system_health.py`
- test_callers: `tests/test_model_inventory.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/model_router.py`

- imports_from: `none`
- imported_by: `src/analytics/model_governance/model_router_registry.py, tests/test_model_router.py`
- runtime_callers: `src/analytics/model_governance/model_router_registry.py`
- test_callers: `tests/test_model_router.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/model_router_registry.py`

- imports_from: `src.analytics.model_governance.model_inventory, src.analytics.model_governance.model_router`
- imported_by: `tests/test_model_router_registry.py`
- runtime_callers: `none`
- test_callers: `tests/test_model_router_registry.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/promotion_gate.py`

- imports_from: `src.analytics.model_governance, src.analytics.model_governance.activation_tiers, src.analytics.model_governance.model_card`
- imported_by: `tests/test_promotion_gate.py`
- runtime_callers: `none`
- test_callers: `tests/test_promotion_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/research_evidence_gate.py`

- imports_from: `src.analytics.model_governance`
- imported_by: `tests/test_research_evidence_gate.py`
- runtime_callers: `none`
- test_callers: `tests/test_research_evidence_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/review_queue_gate.py`

- imports_from: `src.analytics.model_governance, src.analytics.model_governance.activation_tiers`
- imported_by: `tests/test_review_queue_gate.py`
- runtime_callers: `none`
- test_callers: `tests/test_review_queue_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/risk_gate.py`

- imports_from: `none`
- imported_by: `tests/test_risk_gate.py`
- runtime_callers: `none`
- test_callers: `tests/test_risk_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/settlement_liquidity_gate.py`

- imports_from: `none`
- imported_by: `src/services/scheduler_runner.py, tests/test_settlement_liquidity_gate.py`
- runtime_callers: `src/services/scheduler_runner.py`
- test_callers: `tests/test_settlement_liquidity_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/status_classifier.py`

- imports_from: `none`
- imported_by: `tests/test_status_classifier.py`
- runtime_callers: `none`
- test_callers: `tests/test_status_classifier.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_governance/walk_forward_gate.py`

- imports_from: `none`
- imported_by: `tests/test_walk_forward_gate.py`
- runtime_callers: `none`
- test_callers: `tests/test_walk_forward_gate.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/model_performance_report.py`

- imports_from: `src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/backtesting/backtesting_engine.py`
- runtime_callers: `src/backtesting/backtesting_engine.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/pattern_review_queue.py`

- imports_from: `src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/services/automation_scheduler_facade.py, src/services/runtime_shared.py, src/services/streamlit_dashboard_facade.py`
- runtime_callers: `src/services/automation_scheduler_facade.py, src/services/runtime_shared.py, src/services/streamlit_dashboard_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py, src/services/streamlit_dashboard_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/performance.py`

- imports_from: `src.analytics.contracts`
- imported_by: `src/analytics/__init__.py`
- runtime_callers: `src/analytics/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/performance_metrics.py`

- imports_from: `none`
- imported_by: `src/backtesting/backtesting_engine.py, src/services/streamlit_dashboard_facade.py`
- runtime_callers: `src/backtesting/backtesting_engine.py, src/services/streamlit_dashboard_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/streamlit_dashboard_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/random_baseline_comparison.py`

- imports_from: `src.security.policy`
- imported_by: `src/research/extreme_randomness_diagnostics.py`
- runtime_callers: `src/research/extreme_randomness_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/report_writer.py`

- imports_from: `src.services.scheduler_config`
- imported_by: `src/services/scheduler_runner.py`
- runtime_callers: `src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/reports.py`

- imports_from: `none`
- imported_by: `src/analytics/__init__.py, src/analytics/model_governance/__init__.py, tests/test_governance_report.py, tests/test_model_validation_report.py, tests/test_phase10k8zhr_analytics_migration_batch_1.py, tests/test_phase10k8zhv_analytics_downstream_redirection.py`
- runtime_callers: `src/analytics/__init__.py, src/analytics/model_governance/__init__.py`
- test_callers: `tests/test_governance_report.py, tests/test_model_validation_report.py, tests/test_phase10k8zhr_analytics_migration_batch_1.py, tests/test_phase10k8zhv_analytics_downstream_redirection.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/review_queue.py`

- imports_from: `src.core.market_clock, src.market_intelligence.opportunity_scoring, src.services.cadence_controller, src.services.scheduler_config`
- imported_by: `src/ai/deepseek_profit_lab.py, src/analytics/calibration.py, src/analytics/calibration_collector.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/providers/institutional_cross_asset_adapters.py, src/services/automation_scheduler_facade.py, src/services/scheduler_runner.py, src/services/system_health.py`
- runtime_callers: `src/ai/deepseek_profit_lab.py, src/analytics/calibration.py, src/analytics/calibration_collector.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/providers/institutional_cross_asset_adapters.py, src/services/automation_scheduler_facade.py, src/services/scheduler_runner.py, src/services/system_health.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/soccer_impact_calibration.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/soccer_impact_red_team.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/soccer_impact_report.py`

- imports_from: `src.analytics.soccer_impact_calibration, src.analytics.soccer_impact_red_team, src.market_intelligence.soccer_data_availability, src.market_intelligence.soccer_goalkeeper_context, src.market_intelligence.soccer_impact_common, src.market_intelligence.soccer_impact_readiness, src.market_intelligence.soccer_incentive_context, src.market_intelligence.soccer_lineup_availability_context, src.market_intelligence.soccer_market_relevance, src.market_intelligence.soccer_matchup_context, src.market_intelligence.soccer_player_role_impact, src.market_intelligence.soccer_possession_value_impact, src.market_intelligence.soccer_pressing_transition_context, src.market_intelligence.soccer_referee_context, src.market_intelligence.soccer_set_piece_context, src.market_intelligence.soccer_tactical_context`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/strategy_readiness_report.py`

- imports_from: `src.core.strategy_registry, src.security.hard_gate_policy, src.security.policy, src.security.secret_safety`
- imported_by: `src/services/automation_scheduler_facade.py`
- runtime_callers: `src/services/automation_scheduler_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/tennis_impact_calibration.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/tennis_impact_red_team.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/tennis_impact_report.py`

- imports_from: `src.analytics.tennis_impact_calibration, src.analytics.tennis_impact_red_team, src.market_intelligence.tennis_availability_context, src.market_intelligence.tennis_data_availability, src.market_intelligence.tennis_format_markov_context, src.market_intelligence.tennis_impact_common, src.market_intelligence.tennis_impact_readiness, src.market_intelligence.tennis_incentive_context, src.market_intelligence.tennis_market_relevance, src.market_intelligence.tennis_matchup_context, src.market_intelligence.tennis_pressure_tiebreak_context, src.market_intelligence.tennis_return_impact, src.market_intelligence.tennis_serve_impact, src.market_intelligence.tennis_surface_context`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/analytics/topological_red_team.py`

- imports_from: `src.security.policy, src.security.secret_safety`
- imported_by: `src/analytics/advanced_shape_diagnostics.py`
- runtime_callers: `src/analytics/advanced_shape_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/automation_core_routes.py`

- imports_from: `none`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/automation_data_source_routes.py`

- imports_from: `src.api.schemas.automation`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/automation_deepseek_routes.py`

- imports_from: `src.api.schemas.automation`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/automation_institutional_lab_routes.py`

- imports_from: `src.api.schemas.automation, src.services.execution_service`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/automation_manifold_routes.py`

- imports_from: `src.api.schemas.automation`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/automation_review_outcomes_routes.py`

- imports_from: `src.api.automation_security, src.api.schemas.automation`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/automation_run_once_routes.py`

- imports_from: `src.api.schemas.automation`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/automation_security.py`

- imports_from: `src.services.execution_support`
- imported_by: `src/api/automation_review_outcomes_routes.py, tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- runtime_callers: `src/api/automation_review_outcomes_routes.py`
- test_callers: `tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- script_callers: `none`
- api_callers: `src/api/automation_review_outcomes_routes.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/automation_small_account_routes.py`

- imports_from: `src.api.schemas.automation`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/automation_sport_impact_routes.py`

- imports_from: `src.api.schemas.automation`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/bet_csv_routes.py`

- imports_from: `src.api.schemas.bet_csv, src.services.bet_csv_service`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/betting_action_routes.py`

- imports_from: `src.api.schemas.betting_actions, src.services.action_betting_service`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/betting_metadata_routes.py`

- imports_from: `none`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/debug_routes.py`

- imports_from: `none`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/governance_routes.py`

- imports_from: `none`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/market_metadata_routes.py`

- imports_from: `src.providers.compat`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/market_utility_routes.py`

- imports_from: `src.core.opportunity_scanner`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/model_backtest_routes.py`

- imports_from: `src.services.model_backtest_service`
- imported_by: `main.py, tests/test_phase10k8zhi_legacy_full_gate_remediation.py, tests/test_phase10k8zhm_data_backtesting_checkpoint.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zhi_legacy_full_gate_remediation.py, tests/test_phase10k8zhm_data_backtesting_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zhi_legacy_full_gate_remediation.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/model_card_service.py`

- imports_from: `src.core.backtester, src.core.math_utils, src.providers.provider_router, src.sports.nba_features`
- imported_by: `main.py, tests/test_phase10k8zhe_api_layer_ownership_audit.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zhe_api_layer_ownership_audit.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/performance_routes.py`

- imports_from: `src.api.schemas.performance`
- imported_by: `main.py, tests/test_phase10k8zhm_data_backtesting_checkpoint.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zhm_data_backtesting_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/provider_status_routes.py`

- imports_from: `src.services.automation_scheduler_facade`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/quant_routes.py`

- imports_from: `src.api.schemas.quant`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/schemas/__init__.py`

- imports_from: `none`
- imported_by: `tests/support/action_imports.py`
- runtime_callers: `none`
- test_callers: `tests/support/action_imports.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/schemas/automation.py`

- imports_from: `none`
- imported_by: `main.py, src/api/automation_data_source_routes.py, src/api/automation_deepseek_routes.py, src/api/automation_institutional_lab_routes.py, src/api/automation_manifold_routes.py, src/api/automation_review_outcomes_routes.py, src/api/automation_run_once_routes.py, src/api/automation_small_account_routes.py, src/api/automation_sport_impact_routes.py`
- runtime_callers: `src/api/automation_data_source_routes.py, src/api/automation_deepseek_routes.py, src/api/automation_institutional_lab_routes.py, src/api/automation_manifold_routes.py, src/api/automation_review_outcomes_routes.py, src/api/automation_run_once_routes.py, src/api/automation_small_account_routes.py, src/api/automation_sport_impact_routes.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `src/api/automation_data_source_routes.py, src/api/automation_deepseek_routes.py, src/api/automation_institutional_lab_routes.py, src/api/automation_manifold_routes.py, src/api/automation_review_outcomes_routes.py, src/api/automation_run_once_routes.py, src/api/automation_small_account_routes.py, src/api/automation_sport_impact_routes.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/schemas/bet_csv.py`

- imports_from: `none`
- imported_by: `main.py, src/api/bet_csv_routes.py`
- runtime_callers: `src/api/bet_csv_routes.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `src/api/bet_csv_routes.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/schemas/betting_actions.py`

- imports_from: `none`
- imported_by: `src/api/betting_action_routes.py, tests/test_analyze_event.py`
- runtime_callers: `src/api/betting_action_routes.py`
- test_callers: `tests/test_analyze_event.py`
- script_callers: `none`
- api_callers: `src/api/betting_action_routes.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/schemas/performance.py`

- imports_from: `none`
- imported_by: `main.py, src/api/performance_routes.py`
- runtime_callers: `src/api/performance_routes.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `src/api/performance_routes.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/schemas/quant.py`

- imports_from: `none`
- imported_by: `main.py, src/api/quant_routes.py`
- runtime_callers: `src/api/quant_routes.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `src/api/quant_routes.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/stock_analysis_routes.py`

- imports_from: `none`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/api/system_routes.py`

- imports_from: `none`
- imported_by: `main.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/__init__.py`

- imports_from: `src.backtesting.contracts, src.backtesting.datasets, src.backtesting.leakage, src.backtesting.replay, src.backtesting.simulation`
- imported_by: `tests/test_phase10k8zhm_data_backtesting_checkpoint.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zhm_data_backtesting_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/backtest_dataset_builder.py`

- imports_from: `src.backtesting.backtest_leakage, src.backtesting.backtest_schema`
- imported_by: `src/backtesting/dataset_builder.py`
- runtime_callers: `src/backtesting/dataset_builder.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/backtest_leakage.py`

- imports_from: `src.backtesting.backtest_schema`
- imported_by: `src/backtesting/backtest_dataset_builder.py, src/backtesting/backtesting_engine.py`
- runtime_callers: `src/backtesting/backtest_dataset_builder.py, src/backtesting/backtesting_engine.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/backtest_schema.py`

- imports_from: `none`
- imported_by: `src/backtesting/backtest_dataset_builder.py, src/backtesting/backtest_leakage.py, src/backtesting/backtest_strategy_bankroll.py, src/backtesting/backtesting_engine.py`
- runtime_callers: `src/backtesting/backtest_dataset_builder.py, src/backtesting/backtest_leakage.py, src/backtesting/backtest_strategy_bankroll.py, src/backtesting/backtesting_engine.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/backtest_strategy_bankroll.py`

- imports_from: `src.backtesting.backtest_schema`
- imported_by: `src/backtesting/backtesting_engine.py`
- runtime_callers: `src/backtesting/backtesting_engine.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/backtest_strategy_profiles.py`

- imports_from: `src.data`
- imported_by: `src/backtesting/backtesting_engine.py, src/backtesting/strategy_profiles.py`
- runtime_callers: `src/backtesting/backtesting_engine.py, src/backtesting/strategy_profiles.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/backtesting_engine.py`

- imports_from: `src.analytics.calibration, src.analytics.calibration_tracker, src.analytics.model_performance_report, src.analytics.performance_metrics, src.backtesting.backtest_leakage, src.backtesting.backtest_schema, src.backtesting.backtest_strategy_bankroll, src.backtesting.backtest_strategy_profiles, src.brokerage.paper_trade_ledger, src.data.data_paths, src.market_intelligence.clv_tracker, src.services.scheduler_config`
- imported_by: `src/backtesting/engine.py`
- runtime_callers: `src/backtesting/engine.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/bankroll_state.py`

- imports_from: `src.data.data_paths`
- imported_by: `tests/test_bankroll_state.py`
- runtime_callers: `none`
- test_callers: `tests/test_bankroll_state.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/contracts.py`

- imports_from: `src.backtesting.datasets`
- imported_by: `src/backtesting/__init__.py, src/backtesting/datasets.py, src/backtesting/replay.py, src/backtesting/simulation.py`
- runtime_callers: `src/backtesting/__init__.py, src/backtesting/datasets.py, src/backtesting/replay.py, src/backtesting/simulation.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/dataset_builder.py`

- imports_from: `src.backtesting.backtest_dataset_builder, src.backtesting.leakage`
- imported_by: `src/services/streamlit_dashboard_data.py, tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- runtime_callers: `src/services/streamlit_dashboard_data.py`
- test_callers: `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/datasets.py`

- imports_from: `src.backtesting.contracts`
- imported_by: `src/backtesting/__init__.py, src/backtesting/contracts.py, src/backtesting/simulation.py, tests/test_phase10k8zhk_backtesting_foundation.py`
- runtime_callers: `src/backtesting/__init__.py, src/backtesting/contracts.py, src/backtesting/simulation.py`
- test_callers: `tests/test_phase10k8zhk_backtesting_foundation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/engine.py`

- imports_from: `src.backtesting.backtesting_engine`
- imported_by: `src/backtesting/historical_bridge.py, src/services/scheduler_runner.py, src/services/streamlit_dashboard_data.py, tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- runtime_callers: `src/backtesting/historical_bridge.py, src/services/scheduler_runner.py, src/services/streamlit_dashboard_data.py`
- test_callers: `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/historical_bridge.py`

- imports_from: `src.backtesting.engine, src.data, src.data.historical_odds`
- imported_by: `src/data/historical_odds.py, src/services/streamlit_dashboard_data.py`
- runtime_callers: `src/data/historical_odds.py, src/services/streamlit_dashboard_data.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/leakage.py`

- imports_from: `none`
- imported_by: `src/backtesting/__init__.py, src/backtesting/dataset_builder.py, tests/test_phase10k8zhk_backtesting_foundation.py`
- runtime_callers: `src/backtesting/__init__.py, src/backtesting/dataset_builder.py`
- test_callers: `tests/test_phase10k8zhk_backtesting_foundation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/replay.py`

- imports_from: `src.backtesting.contracts`
- imported_by: `src/backtesting/__init__.py, tests/test_phase10k8zhk_backtesting_foundation.py`
- runtime_callers: `src/backtesting/__init__.py`
- test_callers: `tests/test_phase10k8zhk_backtesting_foundation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/simulation.py`

- imports_from: `src.backtesting.contracts, src.backtesting.datasets`
- imported_by: `src/backtesting/__init__.py, tests/test_phase10k8zhk_backtesting_foundation.py`
- runtime_callers: `src/backtesting/__init__.py`
- test_callers: `tests/test_phase10k8zhk_backtesting_foundation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/backtesting/strategy_profiles.py`

- imports_from: `src.backtesting.backtest_strategy_profiles`
- imported_by: `src/services/streamlit_dashboard_data.py, tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- runtime_callers: `src/services/streamlit_dashboard_data.py`
- test_callers: `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/__init__.py`

- imports_from: `src.brokerage.accounts, src.brokerage.activation, src.brokerage.adapter, src.brokerage.adapter_readiness, src.brokerage.approval, src.brokerage.approval_audit, src.brokerage.approval_evidence, src.brokerage.client_factory, src.brokerage.contracts, src.brokerage.credential_loader, src.brokerage.credential_readiness, src.brokerage.credentials, src.brokerage.deployment_policy, src.brokerage.deployment_readiness, src.brokerage.dry_run, src.brokerage.dry_run_ledger, src.brokerage.execution, src.brokerage.kill_switch, src.brokerage.kill_switch_policy, src.brokerage.ledger, src.brokerage.live_ledger, src.brokerage.live_reconciliation, src.brokerage.live_submit, src.brokerage.monitoring, src.brokerage.operator, src.brokerage.orders, src.brokerage.positions, src.brokerage.readiness, src.brokerage.reconciliation, src.brokerage.rollback, src.brokerage.sandbox, src.brokerage.sandbox_activation, src.brokerage.sandbox_adapter, src.brokerage.sandbox_enablement, src.brokerage.sandbox_proof, src.brokerage.sandbox_submit, src.brokerage.settlement, src.brokerage.submit_readiness`
- imported_by: `tests/test_phase10k8zib_unified_brokerage_boundary.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zie_execution_scheduler_wrapper_deletion.py, tests/test_phase10k8zif_execution_boundary_checkpoint.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py, tests/test_phase10k8zik_execution_remediation_checkpoint.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8ziw_final_execution_blocker_audit.py, tests/test_phase10k8zj0_final_execution_blocker_deletion.py, tests/test_phase10k8zj1_execution_cleanup_checkpoint.py, tests/test_phase10k8zk3_final_production_readiness_checkpoint.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zib_unified_brokerage_boundary.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zie_execution_scheduler_wrapper_deletion.py, tests/test_phase10k8zif_execution_boundary_checkpoint.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py, tests/test_phase10k8zik_execution_remediation_checkpoint.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8ziw_final_execution_blocker_audit.py, tests/test_phase10k8zj0_final_execution_blocker_deletion.py, tests/test_phase10k8zj1_execution_cleanup_checkpoint.py, tests/test_phase10k8zk3_final_production_readiness_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zie_execution_scheduler_wrapper_deletion.py, tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/_execution_core.py`

- imports_from: `src.brokerage.contracts, src.brokerage.ledger, src.brokerage.orders, src.brokerage.readiness`
- imported_by: `src/brokerage/execution.py, src/brokerage/execution/__init__.py`
- runtime_callers: `src/brokerage/execution.py, src/brokerage/execution/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/accounts.py`

- imports_from: `src.brokerage.contracts`
- imported_by: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py`
- test_callers: `tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/activation.py`

- imports_from: `src.brokerage.approval, src.brokerage.kill_switch`
- imported_by: `src/brokerage/__init__.py, src/brokerage/sandbox_enablement.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/sandbox_enablement.py`
- test_callers: `tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/adapter.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py`
- runtime_callers: `src/brokerage/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/adapter_readiness.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py, src/brokerage/deployment_policy.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py, tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/deployment_policy.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py`
- test_callers: `tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/approval.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py, src/brokerage/activation.py, src/brokerage/approval_evidence.py, src/brokerage/client_factory.py, src/brokerage/credential_loader.py, src/brokerage/live_ledger.py, src/brokerage/live_reconciliation.py, src/brokerage/live_submit.py, src/brokerage/operator.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_proof.py, src/brokerage/sandbox_submit.py, src/brokerage/submit_readiness.py, tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjj_activation_gate_verification.py, tests/test_phase10k8zjm_live_submit_readiness_verification.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjv_operator_approval_interface.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py, tests/test_phase10k8zk4_architecture_invariants.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/activation.py, src/brokerage/approval_evidence.py, src/brokerage/client_factory.py, src/brokerage/credential_loader.py, src/brokerage/live_ledger.py, src/brokerage/live_reconciliation.py, src/brokerage/live_submit.py, src/brokerage/operator.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_proof.py, src/brokerage/sandbox_submit.py, src/brokerage/submit_readiness.py`
- test_callers: `tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjj_activation_gate_verification.py, tests/test_phase10k8zjm_live_submit_readiness_verification.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjv_operator_approval_interface.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py, tests/test_phase10k8zk4_architecture_invariants.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/approval_audit.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- runtime_callers: `src/brokerage/__init__.py`
- test_callers: `tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/approval_evidence.py`

- imports_from: `src.brokerage.approval`
- imported_by: `src/brokerage/__init__.py, src/brokerage/deployment_policy.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py, tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjq_sandbox_activation_composition.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/deployment_policy.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py`
- test_callers: `tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjq_sandbox_activation_composition.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/client_factory.py`

- imports_from: `src.brokerage.approval, src.brokerage.contracts`
- imported_by: `src/brokerage/__init__.py, src/brokerage/live_ledger.py, src/brokerage/live_reconciliation.py, src/brokerage/live_submit.py, src/brokerage/sandbox_proof.py, src/brokerage/submit_readiness.py, tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjm_live_submit_readiness_verification.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py, tests/test_phase10k8zk4_architecture_invariants.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/live_ledger.py, src/brokerage/live_reconciliation.py, src/brokerage/live_submit.py, src/brokerage/sandbox_proof.py, src/brokerage/submit_readiness.py`
- test_callers: `tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjm_live_submit_readiness_verification.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py, tests/test_phase10k8zk4_architecture_invariants.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/contracts.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py, src/brokerage/_execution_core.py, src/brokerage/accounts.py, src/brokerage/client_factory.py, src/brokerage/credentials.py, src/brokerage/dry_run.py, src/brokerage/dry_run_ledger.py, src/brokerage/ledger.py, src/brokerage/live_reconciliation.py, src/brokerage/live_submit.py, src/brokerage/orders.py, src/brokerage/positions.py, src/brokerage/readiness.py, src/brokerage/reconciliation.py, src/brokerage/sandbox_submit.py, src/brokerage/submit_readiness.py, tests/test_phase10k8zib_unified_brokerage_boundary.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/_execution_core.py, src/brokerage/accounts.py, src/brokerage/client_factory.py, src/brokerage/credentials.py, src/brokerage/dry_run.py, src/brokerage/dry_run_ledger.py, src/brokerage/ledger.py, src/brokerage/live_reconciliation.py, src/brokerage/live_submit.py, src/brokerage/orders.py, src/brokerage/positions.py, src/brokerage/readiness.py, src/brokerage/reconciliation.py, src/brokerage/sandbox_submit.py, src/brokerage/submit_readiness.py`
- test_callers: `tests/test_phase10k8zib_unified_brokerage_boundary.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/credential_loader.py`

- imports_from: `src.brokerage.approval, src.brokerage.kill_switch`
- imported_by: `src/brokerage/__init__.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py`
- runtime_callers: `src/brokerage/__init__.py`
- test_callers: `tests/test_phase10k8zk2_final_live_trading_disabled_proof.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/credential_readiness.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py, src/brokerage/deployment_policy.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py, tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk2_credential_sdk_network_freeze.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/deployment_policy.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py`
- test_callers: `tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk2_credential_sdk_network_freeze.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/credentials.py`

- imports_from: `src.brokerage.contracts`
- imported_by: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py`
- test_callers: `tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/deployment_policy.py`

- imports_from: `src.brokerage.adapter_readiness, src.brokerage.approval_evidence, src.brokerage.credential_readiness, src.brokerage.kill_switch, src.brokerage.monitoring, src.brokerage.rollback`
- imported_by: `src/brokerage/__init__.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- runtime_callers: `src/brokerage/__init__.py`
- test_callers: `tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/deployment_readiness.py`

- imports_from: `src.brokerage.kill_switch, src.brokerage.monitoring, src.brokerage.rollback`
- imported_by: `src/brokerage/__init__.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py`
- test_callers: `tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/dry_run.py`

- imports_from: `src.brokerage.contracts, src.brokerage.ledger, src.brokerage.orders`
- imported_by: `src/brokerage/__init__.py, src/brokerage/dry_run_ledger.py, src/brokerage/sandbox_proof.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/dry_run_ledger.py, src/brokerage/sandbox_proof.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/dry_run_ledger.py`

- imports_from: `src.brokerage.contracts, src.brokerage.dry_run, src.brokerage.orders`
- imported_by: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/execution.py`

- imports_from: `src.brokerage._execution_core`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/execution/__init__.py`

- imports_from: `src.brokerage._execution_core`
- imported_by: `src/brokerage/__init__.py, tests/test_phase10k8zib_unified_brokerage_boundary.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zie_execution_scheduler_wrapper_deletion.py, tests/test_phase10k8zif_execution_boundary_checkpoint.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- runtime_callers: `src/brokerage/__init__.py`
- test_callers: `tests/test_phase10k8zib_unified_brokerage_boundary.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zie_execution_scheduler_wrapper_deletion.py, tests/test_phase10k8zif_execution_boundary_checkpoint.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zie_execution_scheduler_wrapper_deletion.py, tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/kill_switch.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py, src/brokerage/activation.py, src/brokerage/credential_loader.py, src/brokerage/deployment_policy.py, src/brokerage/deployment_readiness.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py, tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjj_activation_gate_verification.py, tests/test_phase10k8zjn_monitoring_rollback_readiness.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/activation.py, src/brokerage/credential_loader.py, src/brokerage/deployment_policy.py, src/brokerage/deployment_readiness.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py`
- test_callers: `tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjj_activation_gate_verification.py, tests/test_phase10k8zjn_monitoring_rollback_readiness.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/kill_switch_policy.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- runtime_callers: `src/brokerage/__init__.py`
- test_callers: `tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/later/__init__.py`

- imports_from: `src.brokerage.later.auto_execution_policy, src.brokerage.later.execution_audit_log, src.brokerage.later.execution_guardrails, src.brokerage.later.execution_readiness_check`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/later/auto_execution_policy.py`

- imports_from: `none`
- imported_by: `src/brokerage/later/__init__.py`
- runtime_callers: `src/brokerage/later/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/later/execution_audit_log.py`

- imports_from: `src.services.scheduler_config`
- imported_by: `src/brokerage/later/__init__.py`
- runtime_callers: `src/brokerage/later/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/later/execution_guardrails.py`

- imports_from: `none`
- imported_by: `src/brokerage/later/__init__.py`
- runtime_callers: `src/brokerage/later/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/later/execution_readiness_check.py`

- imports_from: `none`
- imported_by: `src/brokerage/later/__init__.py`
- runtime_callers: `src/brokerage/later/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/ledger.py`

- imports_from: `src.brokerage.contracts`
- imported_by: `src/brokerage/__init__.py, src/brokerage/_execution_core.py, src/brokerage/dry_run.py, src/brokerage/paper_decision_ledger.py, src/brokerage/paper_trade_ledger.py, src/brokerage/submit_readiness.py, tests/test_phase10k8zib_unified_brokerage_boundary.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8zjm_live_submit_readiness_verification.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/_execution_core.py, src/brokerage/dry_run.py, src/brokerage/paper_decision_ledger.py, src/brokerage/paper_trade_ledger.py, src/brokerage/submit_readiness.py`
- test_callers: `tests/test_phase10k8zib_unified_brokerage_boundary.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8zjm_live_submit_readiness_verification.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/live_ledger.py`

- imports_from: `src.brokerage.approval, src.brokerage.client_factory`
- imported_by: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py`
- test_callers: `tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/live_reconciliation.py`

- imports_from: `src.brokerage.approval, src.brokerage.client_factory, src.brokerage.contracts, src.brokerage.reconciliation`
- imported_by: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py`
- test_callers: `tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/live_submit.py`

- imports_from: `src.brokerage.approval, src.brokerage.client_factory, src.brokerage.contracts, src.brokerage.orders`
- imported_by: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py, src/brokerage/submit_readiness.py, tests/test_phase10k8zjm_live_submit_readiness_verification.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py, tests/test_phase10k8zk4_architecture_invariants.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py, src/brokerage/submit_readiness.py`
- test_callers: `tests/test_phase10k8zjm_live_submit_readiness_verification.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py, tests/test_phase10k8zk4_architecture_invariants.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/live_trading/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/monitoring.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py, src/brokerage/deployment_policy.py, src/brokerage/deployment_readiness.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py, tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/deployment_policy.py, src/brokerage/deployment_readiness.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py`
- test_callers: `tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/operator.py`

- imports_from: `src.brokerage.approval`
- imported_by: `src/brokerage/__init__.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- runtime_callers: `src/brokerage/__init__.py`
- test_callers: `tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/order_gateway/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/orders.py`

- imports_from: `src.brokerage.contracts`
- imported_by: `src/brokerage/__init__.py, src/brokerage/_execution_core.py, src/brokerage/dry_run.py, src/brokerage/dry_run_ledger.py, src/brokerage/live_submit.py, src/brokerage/readiness.py, src/brokerage/sandbox_submit.py, src/brokerage/submit_readiness.py, src/services/decision_engine.py, tests/test_phase10k8zib_unified_brokerage_boundary.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8zjm_live_submit_readiness_verification.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/_execution_core.py, src/brokerage/dry_run.py, src/brokerage/dry_run_ledger.py, src/brokerage/live_submit.py, src/brokerage/readiness.py, src/brokerage/sandbox_submit.py, src/brokerage/submit_readiness.py, src/services/decision_engine.py`
- test_callers: `tests/test_phase10k8zib_unified_brokerage_boundary.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8zjm_live_submit_readiness_verification.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py, tests/test_phase10k8zk2_final_live_trading_disabled_proof.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/paper_decision_ledger.py`

- imports_from: `src.brokerage.ledger, src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/analytics/calibration.py, src/analytics/calibration_collector.py, src/analytics/manifold_calibration.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/providers/institutional_cross_asset_adapters.py, src/services/scheduler_runner.py, tests/test_phase10k8zic_execution_ownership_migration.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8ziw_final_execution_blocker_audit.py, tests/test_phase10k8zix_final_execution_blocker_canonicalization.py, tests/test_phase10k8ziz_final_execution_blocker_delete_proof.py, tests/test_phase10k8zj1_execution_cleanup_checkpoint.py`
- runtime_callers: `src/analytics/calibration.py, src/analytics/calibration_collector.py, src/analytics/manifold_calibration.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/providers/institutional_cross_asset_adapters.py, src/services/scheduler_runner.py`
- test_callers: `tests/test_phase10k8zic_execution_ownership_migration.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8ziw_final_execution_blocker_audit.py, tests/test_phase10k8zix_final_execution_blocker_canonicalization.py, tests/test_phase10k8ziz_final_execution_blocker_delete_proof.py, tests/test_phase10k8zj1_execution_cleanup_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/paper_trade_ledger.py`

- imports_from: `src.brokerage.ledger, src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/backtesting/backtesting_engine.py, src/services/system_health.py, tests/test_phase10k8zic_execution_ownership_migration.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8ziw_final_execution_blocker_audit.py, tests/test_phase10k8zix_final_execution_blocker_canonicalization.py, tests/test_phase10k8ziz_final_execution_blocker_delete_proof.py, tests/test_phase10k8zj1_execution_cleanup_checkpoint.py`
- runtime_callers: `src/backtesting/backtesting_engine.py, src/services/system_health.py`
- test_callers: `tests/test_phase10k8zic_execution_ownership_migration.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8ziw_final_execution_blocker_audit.py, tests/test_phase10k8zix_final_execution_blocker_canonicalization.py, tests/test_phase10k8ziz_final_execution_blocker_delete_proof.py, tests/test_phase10k8zj1_execution_cleanup_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/paper_trading/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/positions.py`

- imports_from: `src.brokerage.contracts`
- imported_by: `src/brokerage/__init__.py, src/brokerage/readiness.py, src/brokerage/reconciliation.py, tests/test_phase10k8zib_unified_brokerage_boundary.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/readiness.py, src/brokerage/reconciliation.py`
- test_callers: `tests/test_phase10k8zib_unified_brokerage_boundary.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/readiness.py`

- imports_from: `src.brokerage.contracts, src.brokerage.orders, src.brokerage.positions, src.brokerage.readiness_support, src.providers.policy.write_firewall, src.research.maturity, src.services.ledger_service`
- imported_by: `src/brokerage/__init__.py, src/brokerage/_execution_core.py, src/core/strategy_promotion.py, src/core/strategy_score_aggregator.py, src/services/decision_engine.py, tests/test_phase10k8zgb_provider_write_firewall_runtime_blocker.py, tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py, tests/test_phase10k8zib_unified_brokerage_boundary.py, tests/test_phase10k8zic_execution_ownership_migration.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zif_execution_boundary_checkpoint.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8ziw_final_execution_blocker_audit.py, tests/test_phase10k8zix_final_execution_blocker_canonicalization.py, tests/test_phase10k8ziz_final_execution_blocker_delete_proof.py, tests/test_phase10k8zj0_final_execution_blocker_deletion.py, tests/test_phase10k8zj1_execution_cleanup_checkpoint.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py, tests/test_security_framework.py, tests/test_strategy_framework.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/_execution_core.py, src/core/strategy_promotion.py, src/core/strategy_score_aggregator.py, src/services/decision_engine.py`
- test_callers: `tests/test_phase10k8zgb_provider_write_firewall_runtime_blocker.py, tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py, tests/test_phase10k8zib_unified_brokerage_boundary.py, tests/test_phase10k8zic_execution_ownership_migration.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zif_execution_boundary_checkpoint.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8ziw_final_execution_blocker_audit.py, tests/test_phase10k8zix_final_execution_blocker_canonicalization.py, tests/test_phase10k8ziz_final_execution_blocker_delete_proof.py, tests/test_phase10k8zj0_final_execution_blocker_deletion.py, tests/test_phase10k8zj1_execution_cleanup_checkpoint.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py, tests/test_security_framework.py, tests/test_strategy_framework.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/readiness_support.py`

- imports_from: `src.providers.policy.allowlist, src.services.runtime_shared`
- imported_by: `src/brokerage/readiness.py, tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- runtime_callers: `src/brokerage/readiness.py`
- test_callers: `tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/reconciliation.py`

- imports_from: `src.brokerage.contracts, src.brokerage.positions`
- imported_by: `src/brokerage/__init__.py, src/brokerage/live_reconciliation.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/live_reconciliation.py`
- test_callers: `tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/risk_controls/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/rollback.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py, src/brokerage/deployment_policy.py, src/brokerage/deployment_readiness.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py, tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjn_monitoring_rollback_readiness.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/deployment_policy.py, src/brokerage/deployment_readiness.py, src/brokerage/sandbox_activation.py, src/brokerage/sandbox_enablement.py, src/brokerage/sandbox_proof.py`
- test_callers: `tests/test_phase10k8z0_deployment_governance.py, tests/test_phase10k8zjn_monitoring_rollback_readiness.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py, tests/test_phase10k8zjx_sandbox_enablement_layer.py, tests/test_phase10k8zk2_production_activation_readiness_ledger.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/sandbox.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py, src/brokerage/sandbox_submit.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/sandbox_submit.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/sandbox_activation.py`

- imports_from: `src.brokerage.adapter_readiness, src.brokerage.approval, src.brokerage.approval_evidence, src.brokerage.credential_readiness, src.brokerage.deployment_readiness, src.brokerage.kill_switch, src.brokerage.monitoring, src.brokerage.rollback`
- imported_by: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py`
- runtime_callers: `src/brokerage/__init__.py, src/brokerage/sandbox_proof.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/sandbox_adapter.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- runtime_callers: `src/brokerage/__init__.py`
- test_callers: `tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/sandbox_enablement.py`

- imports_from: `src.brokerage.activation, src.brokerage.adapter_readiness, src.brokerage.approval_evidence, src.brokerage.credential_readiness, src.brokerage.deployment_readiness, src.brokerage.kill_switch, src.brokerage.monitoring, src.brokerage.rollback`
- imported_by: `src/brokerage/__init__.py, tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- runtime_callers: `src/brokerage/__init__.py`
- test_callers: `tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/sandbox_proof.py`

- imports_from: `src.brokerage.accounts, src.brokerage.adapter_readiness, src.brokerage.approval, src.brokerage.approval_evidence, src.brokerage.client_factory, src.brokerage.credential_readiness, src.brokerage.credentials, src.brokerage.deployment_readiness, src.brokerage.dry_run, src.brokerage.dry_run_ledger, src.brokerage.kill_switch, src.brokerage.live_ledger, src.brokerage.live_reconciliation, src.brokerage.live_submit, src.brokerage.monitoring, src.brokerage.rollback, src.brokerage.sandbox_activation`
- imported_by: `src/brokerage/__init__.py`
- runtime_callers: `src/brokerage/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/sandbox_submit.py`

- imports_from: `src.brokerage.approval, src.brokerage.contracts, src.brokerage.orders, src.brokerage.sandbox`
- imported_by: `src/brokerage/__init__.py`
- runtime_callers: `src/brokerage/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/settlement.py`

- imports_from: `none`
- imported_by: `src/brokerage/__init__.py, src/market_intelligence/arbitrage/arbitrage_risk_filters.py, src/services/settlement_service.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zil_settlement_canonicalization.py, tests/test_phase10k8zio_execution_helper_final_delete_readiness.py, tests/test_phase10k8zip_execution_helper_canonicalization_checkpoint.py, tests/test_settlement_rule_checker.py`
- runtime_callers: `src/brokerage/__init__.py, src/market_intelligence/arbitrage/arbitrage_risk_filters.py, src/services/settlement_service.py`
- test_callers: `tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zil_settlement_canonicalization.py, tests/test_phase10k8zio_execution_helper_final_delete_readiness.py, tests/test_phase10k8zip_execution_helper_canonicalization_checkpoint.py, tests/test_settlement_rule_checker.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/brokerage/submit_readiness.py`

- imports_from: `src.brokerage.approval, src.brokerage.client_factory, src.brokerage.contracts, src.brokerage.ledger, src.brokerage.live_submit, src.brokerage.orders`
- imported_by: `src/brokerage/__init__.py, tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py`
- runtime_callers: `src/brokerage/__init__.py`
- test_callers: `tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/__init__.py`

- imports_from: `src.connectors.contracts, src.connectors.errors, src.connectors.market_data, src.connectors.models, src.connectors.odds_data, src.connectors.policy, src.connectors.registry`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/contracts.py`

- imports_from: `none`
- imported_by: `src/connectors/__init__.py, src/connectors/policy.py, src/connectors/registry.py`
- runtime_callers: `src/connectors/__init__.py, src/connectors/policy.py, src/connectors/registry.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/errors.py`

- imports_from: `none`
- imported_by: `src/connectors/__init__.py, src/connectors/market_data/adapter.py, src/connectors/market_data/read_only.py, src/connectors/odds_data/adapter.py, src/connectors/odds_data/live_client.py, src/connectors/odds_data/read_only.py, src/connectors/odds_data/transport.py, src/connectors/prediction_market_data/adapter.py, src/connectors/prediction_market_data/disabled_client.py, src/connectors/prediction_market_data/read_only.py, src/connectors/prediction_market_data/signing.py, src/connectors/prediction_market_data/transport.py, src/services/odds_runtime_bridge.py, src/services/prediction_market_runtime_bridge.py, tests/test_kalshi_readonly_adapter.py, tests/test_phase10k8zfy_prediction_market_connector_batch_1.py, tests/test_phase10k8zfz_odds_data_connector_batch_2.py, tests/test_phase10k8zg0_market_data_connector_batch_3.py, tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py, tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py, tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py, tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py, tests/test_phase10k8zgm_odds_historical_test_redirection.py, tests/test_phase10k8zgn_odds_proof_history_cleanup.py, tests/test_phase10k8zgo_odds_compatibility_test_retirement.py, tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py, tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py, tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py, tests/test_phase10k8zgy_prediction_market_shell_deletion.py, tests/test_sharp_sportsbook_adapter.py`
- runtime_callers: `src/connectors/__init__.py, src/connectors/market_data/adapter.py, src/connectors/market_data/read_only.py, src/connectors/odds_data/adapter.py, src/connectors/odds_data/live_client.py, src/connectors/odds_data/read_only.py, src/connectors/odds_data/transport.py, src/connectors/prediction_market_data/adapter.py, src/connectors/prediction_market_data/disabled_client.py, src/connectors/prediction_market_data/read_only.py, src/connectors/prediction_market_data/signing.py, src/connectors/prediction_market_data/transport.py, src/services/odds_runtime_bridge.py, src/services/prediction_market_runtime_bridge.py`
- test_callers: `tests/test_kalshi_readonly_adapter.py, tests/test_phase10k8zfy_prediction_market_connector_batch_1.py, tests/test_phase10k8zfz_odds_data_connector_batch_2.py, tests/test_phase10k8zg0_market_data_connector_batch_3.py, tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py, tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py, tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py, tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py, tests/test_phase10k8zgm_odds_historical_test_redirection.py, tests/test_phase10k8zgn_odds_proof_history_cleanup.py, tests/test_phase10k8zgo_odds_compatibility_test_retirement.py, tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py, tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py, tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py, tests/test_phase10k8zgy_prediction_market_shell_deletion.py, tests/test_sharp_sportsbook_adapter.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgo_odds_compatibility_test_retirement.py, tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py, tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py, tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/feeds/__init__.py`

- imports_from: `src.connectors.feeds.contracts`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/feeds/contracts.py`

- imports_from: `none`
- imported_by: `src/connectors/feeds/__init__.py`
- runtime_callers: `src/connectors/feeds/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/market_data/__init__.py`

- imports_from: `src.connectors.market_data.adapter, src.connectors.market_data.client, src.connectors.market_data.contracts, src.connectors.market_data.models, src.connectors.market_data.payloads`
- imported_by: `src/connectors/__init__.py, tests/test_phase10k8zg0_market_data_connector_batch_3.py, tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py`
- runtime_callers: `src/connectors/__init__.py`
- test_callers: `tests/test_phase10k8zg0_market_data_connector_batch_3.py, tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/market_data/adapter.py`

- imports_from: `src.connectors.errors, src.connectors.market_data.client, src.connectors.market_data.contracts, src.connectors.market_data.payloads`
- imported_by: `src/connectors/market_data/__init__.py`
- runtime_callers: `src/connectors/market_data/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/market_data/client.py`

- imports_from: `src.connectors.market_data.read_only`
- imported_by: `src/connectors/market_data/__init__.py, src/connectors/market_data/adapter.py`
- runtime_callers: `src/connectors/market_data/__init__.py, src/connectors/market_data/adapter.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/market_data/contracts.py`

- imports_from: `none`
- imported_by: `src/connectors/market_data/__init__.py, src/connectors/market_data/adapter.py`
- runtime_callers: `src/connectors/market_data/__init__.py, src/connectors/market_data/adapter.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/market_data/models.py`

- imports_from: `none`
- imported_by: `src/connectors/market_data/__init__.py, src/connectors/market_data/payloads.py, src/connectors/market_data/read_only.py, src/providers/zero_dte_stocks/normalization.py, src/providers/zero_dte_stocks/provider.py`
- runtime_callers: `src/connectors/market_data/__init__.py, src/connectors/market_data/payloads.py, src/connectors/market_data/read_only.py, src/providers/zero_dte_stocks/normalization.py, src/providers/zero_dte_stocks/provider.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/market_data/payloads.py`

- imports_from: `src.connectors.market_data.models`
- imported_by: `src/connectors/market_data/__init__.py, src/connectors/market_data/adapter.py, src/connectors/market_data/read_only.py`
- runtime_callers: `src/connectors/market_data/__init__.py, src/connectors/market_data/adapter.py, src/connectors/market_data/read_only.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/market_data/read_only.py`

- imports_from: `src.connectors.errors, src.connectors.market_data.models, src.connectors.market_data.payloads`
- imported_by: `src/connectors/market_data/client.py`
- runtime_callers: `src/connectors/market_data/client.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/models.py`

- imports_from: `none`
- imported_by: `src/connectors/__init__.py`
- runtime_callers: `src/connectors/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/__init__.py`

- imports_from: `src.connectors.odds_data.adapter, src.connectors.odds_data.auth, src.connectors.odds_data.client, src.connectors.odds_data.configuration, src.connectors.odds_data.contracts, src.connectors.odds_data.disabled_client, src.connectors.odds_data.live_client, src.connectors.odds_data.models, src.connectors.odds_data.payloads, src.connectors.odds_data.readiness, src.connectors.odds_data.source_profile, src.connectors.odds_data.transport`
- imported_by: `src/connectors/__init__.py, src/providers/provider_router.py, src/services/odds_runtime_bridge.py, tests/test_phase10k8zfz_odds_data_connector_batch_2.py, tests/test_phase10k8zg0_market_data_connector_batch_3.py, tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py, tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py, tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py, tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py, tests/test_phase10k8zgm_odds_historical_test_redirection.py, tests/test_phase10k8zgn_odds_proof_history_cleanup.py, tests/test_phase10k8zgo_odds_compatibility_test_retirement.py, tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_sharp_sportsbook_adapter.py, tests/test_sportsbook_odds_provider.py`
- runtime_callers: `src/connectors/__init__.py, src/providers/provider_router.py, src/services/odds_runtime_bridge.py`
- test_callers: `tests/test_phase10k8zfz_odds_data_connector_batch_2.py, tests/test_phase10k8zg0_market_data_connector_batch_3.py, tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py, tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py, tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py, tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py, tests/test_phase10k8zgm_odds_historical_test_redirection.py, tests/test_phase10k8zgn_odds_proof_history_cleanup.py, tests/test_phase10k8zgo_odds_compatibility_test_retirement.py, tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_sharp_sportsbook_adapter.py, tests/test_sportsbook_odds_provider.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgo_odds_compatibility_test_retirement.py, tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/adapter.py`

- imports_from: `src.connectors.errors, src.connectors.odds_data.client, src.connectors.odds_data.models, src.connectors.odds_data.payloads`
- imported_by: `src/connectors/odds_data/__init__.py`
- runtime_callers: `src/connectors/odds_data/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/auth.py`

- imports_from: `none`
- imported_by: `src/connectors/odds_data/__init__.py, tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- runtime_callers: `src/connectors/odds_data/__init__.py`
- test_callers: `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/client.py`

- imports_from: `src.connectors.odds_data.read_only`
- imported_by: `src/connectors/odds_data/__init__.py, src/connectors/odds_data/adapter.py`
- runtime_callers: `src/connectors/odds_data/__init__.py, src/connectors/odds_data/adapter.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/configuration.py`

- imports_from: `none`
- imported_by: `src/connectors/odds_data/__init__.py, tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- runtime_callers: `src/connectors/odds_data/__init__.py`
- test_callers: `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/contracts.py`

- imports_from: `none`
- imported_by: `src/connectors/odds_data/__init__.py`
- runtime_callers: `src/connectors/odds_data/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/disabled_client.py`

- imports_from: `src.connectors.odds_data.live_client`
- imported_by: `src/connectors/odds_data/__init__.py, tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- runtime_callers: `src/connectors/odds_data/__init__.py`
- test_callers: `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/live_client.py`

- imports_from: `src.connectors.errors, src.connectors.odds_data.readiness, src.connectors.odds_data.source_profile`
- imported_by: `src/connectors/odds_data/__init__.py, src/connectors/odds_data/disabled_client.py, tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- runtime_callers: `src/connectors/odds_data/__init__.py, src/connectors/odds_data/disabled_client.py`
- test_callers: `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/models.py`

- imports_from: `none`
- imported_by: `src/connectors/odds_data/__init__.py, src/connectors/odds_data/adapter.py, src/connectors/odds_data/payloads.py, src/connectors/odds_data/read_only.py`
- runtime_callers: `src/connectors/odds_data/__init__.py, src/connectors/odds_data/adapter.py, src/connectors/odds_data/payloads.py, src/connectors/odds_data/read_only.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/payloads.py`

- imports_from: `src.connectors.odds_data.models`
- imported_by: `src/connectors/odds_data/__init__.py, src/connectors/odds_data/adapter.py, src/connectors/odds_data/read_only.py`
- runtime_callers: `src/connectors/odds_data/__init__.py, src/connectors/odds_data/adapter.py, src/connectors/odds_data/read_only.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/read_only.py`

- imports_from: `src.connectors.errors, src.connectors.odds_data.models, src.connectors.odds_data.payloads`
- imported_by: `src/connectors/odds_data/client.py`
- runtime_callers: `src/connectors/odds_data/client.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/readiness.py`

- imports_from: `none`
- imported_by: `src/connectors/odds_data/__init__.py, src/connectors/odds_data/live_client.py, tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- runtime_callers: `src/connectors/odds_data/__init__.py, src/connectors/odds_data/live_client.py`
- test_callers: `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/source_profile.py`

- imports_from: `none`
- imported_by: `src/connectors/odds_data/__init__.py, src/connectors/odds_data/live_client.py, tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- runtime_callers: `src/connectors/odds_data/__init__.py, src/connectors/odds_data/live_client.py`
- test_callers: `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/odds_data/transport.py`

- imports_from: `src.connectors.errors`
- imported_by: `src/connectors/odds_data/__init__.py, tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- runtime_callers: `src/connectors/odds_data/__init__.py`
- test_callers: `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/policy.py`

- imports_from: `src.connectors.contracts`
- imported_by: `src/connectors/__init__.py`
- runtime_callers: `src/connectors/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/__init__.py`

- imports_from: `src.connectors.prediction_market_data.adapter, src.connectors.prediction_market_data.auth, src.connectors.prediction_market_data.client, src.connectors.prediction_market_data.configuration, src.connectors.prediction_market_data.contracts, src.connectors.prediction_market_data.disabled_client, src.connectors.prediction_market_data.models, src.connectors.prediction_market_data.payloads, src.connectors.prediction_market_data.readiness, src.connectors.prediction_market_data.signing, src.connectors.prediction_market_data.transport`
- imported_by: `src/services/prediction_market_runtime_bridge.py, tests/test_kalshi_readonly_adapter.py, tests/test_phase10k8zfy_prediction_market_connector_batch_1.py, tests/test_phase10k8zg0_market_data_connector_batch_3.py, tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py, tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py, tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py, tests/test_phase10k8zgy_prediction_market_shell_deletion.py`
- runtime_callers: `src/services/prediction_market_runtime_bridge.py`
- test_callers: `tests/test_kalshi_readonly_adapter.py, tests/test_phase10k8zfy_prediction_market_connector_batch_1.py, tests/test_phase10k8zg0_market_data_connector_batch_3.py, tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py, tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py, tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py, tests/test_phase10k8zgy_prediction_market_shell_deletion.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/adapter.py`

- imports_from: `src.connectors.errors, src.connectors.prediction_market_data.client, src.connectors.prediction_market_data.models, src.connectors.prediction_market_data.payloads`
- imported_by: `src/connectors/prediction_market_data/__init__.py`
- runtime_callers: `src/connectors/prediction_market_data/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/auth.py`

- imports_from: `none`
- imported_by: `src/connectors/prediction_market_data/__init__.py, tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- runtime_callers: `src/connectors/prediction_market_data/__init__.py`
- test_callers: `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/client.py`

- imports_from: `src.connectors.prediction_market_data.read_only`
- imported_by: `src/connectors/prediction_market_data/__init__.py, src/connectors/prediction_market_data/adapter.py`
- runtime_callers: `src/connectors/prediction_market_data/__init__.py, src/connectors/prediction_market_data/adapter.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/configuration.py`

- imports_from: `none`
- imported_by: `src/connectors/prediction_market_data/__init__.py, tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- runtime_callers: `src/connectors/prediction_market_data/__init__.py`
- test_callers: `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/contracts.py`

- imports_from: `none`
- imported_by: `src/connectors/prediction_market_data/__init__.py`
- runtime_callers: `src/connectors/prediction_market_data/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/disabled_client.py`

- imports_from: `src.connectors.errors`
- imported_by: `src/connectors/prediction_market_data/__init__.py, tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- runtime_callers: `src/connectors/prediction_market_data/__init__.py`
- test_callers: `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/models.py`

- imports_from: `none`
- imported_by: `src/connectors/prediction_market_data/__init__.py, src/connectors/prediction_market_data/adapter.py, src/connectors/prediction_market_data/payloads.py, src/connectors/prediction_market_data/read_only.py`
- runtime_callers: `src/connectors/prediction_market_data/__init__.py, src/connectors/prediction_market_data/adapter.py, src/connectors/prediction_market_data/payloads.py, src/connectors/prediction_market_data/read_only.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/payloads.py`

- imports_from: `src.connectors.prediction_market_data.models`
- imported_by: `src/connectors/prediction_market_data/__init__.py, src/connectors/prediction_market_data/adapter.py, src/connectors/prediction_market_data/read_only.py`
- runtime_callers: `src/connectors/prediction_market_data/__init__.py, src/connectors/prediction_market_data/adapter.py, src/connectors/prediction_market_data/read_only.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/read_only.py`

- imports_from: `src.connectors.errors, src.connectors.prediction_market_data.models, src.connectors.prediction_market_data.payloads`
- imported_by: `src/connectors/prediction_market_data/client.py`
- runtime_callers: `src/connectors/prediction_market_data/client.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/readiness.py`

- imports_from: `none`
- imported_by: `src/connectors/prediction_market_data/__init__.py, tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- runtime_callers: `src/connectors/prediction_market_data/__init__.py`
- test_callers: `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/signing.py`

- imports_from: `src.connectors.errors`
- imported_by: `src/connectors/prediction_market_data/__init__.py, tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- runtime_callers: `src/connectors/prediction_market_data/__init__.py`
- test_callers: `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/prediction_market_data/transport.py`

- imports_from: `src.connectors.errors`
- imported_by: `src/connectors/prediction_market_data/__init__.py, tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- runtime_callers: `src/connectors/prediction_market_data/__init__.py`
- test_callers: `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/registry.py`

- imports_from: `src.connectors.contracts`
- imported_by: `src/connectors/__init__.py`
- runtime_callers: `src/connectors/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/web_scraping/__init__.py`

- imports_from: `src.connectors.web_scraping.contracts`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/connectors/web_scraping/contracts.py`

- imports_from: `none`
- imported_by: `src/connectors/web_scraping/__init__.py`
- runtime_callers: `src/connectors/web_scraping/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/__init__.py`

- imports_from: `none`
- imported_by: `tests/test_phase10k5_core_arbitrage_engine.py, tests/test_phase10k8zfg_safe_migration_batch_1.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k5_core_arbitrage_engine.py, tests/test_phase10k8zfg_safe_migration_batch_1.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/backtester.py`

- imports_from: `src.core.calibrator, src.core.clv, src.core.math_utils, src.sports.nba_features`
- imported_by: `src/api/model_card_service.py, src/services/model_backtest_service.py, tests/test_phase10k8zhi_legacy_full_gate_remediation.py, tests/test_phase10k8zhm_data_backtesting_checkpoint.py`
- runtime_callers: `src/api/model_card_service.py, src/services/model_backtest_service.py`
- test_callers: `tests/test_phase10k8zhi_legacy_full_gate_remediation.py, tests/test_phase10k8zhm_data_backtesting_checkpoint.py`
- script_callers: `none`
- api_callers: `src/api/model_card_service.py`
- facade_callers: `tests/test_phase10k8zhi_legacy_full_gate_remediation.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/balance_sheet_risk.py`

- imports_from: `none`
- imported_by: `src/services/automation_scheduler_facade.py, src/services/runtime_shared.py`
- runtime_callers: `src/services/automation_scheduler_facade.py, src/services/runtime_shared.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/budget_gates.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/calibrator.py`

- imports_from: `none`
- imported_by: `src/core/backtester.py`
- runtime_callers: `src/core/backtester.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/clv.py`

- imports_from: `src.core.math_utils`
- imported_by: `src/core/backtester.py, src/core/market_pricing.py, src/core/risk_engine.py, src/market_intelligence/clv_tracker.py, src/services/bet_log.py`
- runtime_callers: `src/core/backtester.py, src/core/market_pricing.py, src/core/risk_engine.py, src/market_intelligence/clv_tracker.py, src/services/bet_log.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/conformal_uncertainty.py`

- imports_from: `src.security.policy`
- imported_by: `src/analytics/advanced_shape_diagnostics.py`
- runtime_callers: `src/analytics/advanced_shape_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/cross_book_line_comparator.py`

- imports_from: `src.core.math_utils, src.data, src.market_intelligence.bookmaker_normalizer`
- imported_by: `src/core/ev_line_shopper.py, src/services/scheduler_runner.py`
- runtime_callers: `src/core/ev_line_shopper.py, src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/drawdown_controls.py`

- imports_from: `none`
- imported_by: `tests/test_drawdown_controls.py`
- runtime_callers: `none`
- test_callers: `tests/test_drawdown_controls.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/entity_resolver.py`

- imports_from: `none`
- imported_by: `src/services/enrichment_service.py, src/services/odds_runtime_bridge.py, src/services/prediction_market_runtime_bridge.py, src/services/screenshot_intake.py`
- runtime_callers: `src/services/enrichment_service.py, src/services/odds_runtime_bridge.py, src/services/prediction_market_runtime_bridge.py, src/services/screenshot_intake.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/ev_line_shopper.py`

- imports_from: `src.core.cross_book_line_comparator, src.core.math_utils, src.core.no_vig_pricing, src.data, src.market_intelligence.bookmaker_normalizer, src.market_intelligence.clv_tracker`
- imported_by: `src/services/scheduler_runner.py`
- runtime_callers: `src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/execution.py`

- imports_from: `none`
- imported_by: `src/core/game_theory.py, src/core/market_impact.py, src/core/quant_engine.py, src/services/decision_engine.py, tests/test_phase10k8zh7_execution_game_theory_foundation.py`
- runtime_callers: `src/core/game_theory.py, src/core/market_impact.py, src/core/quant_engine.py, src/services/decision_engine.py`
- test_callers: `tests/test_phase10k8zh7_execution_game_theory_foundation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/exposure_limits.py`

- imports_from: `src.core.risk_engine`
- imported_by: `tests/test_exposure_limits.py`
- runtime_callers: `none`
- test_callers: `tests/test_exposure_limits.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/game_theory.py`

- imports_from: `src.core.execution, src.core.market_impact`
- imported_by: `src/core/quant_engine.py, src/services/decision_engine.py, tests/test_phase10k8zh7_execution_game_theory_foundation.py`
- runtime_callers: `src/core/quant_engine.py, src/services/decision_engine.py`
- test_callers: `tests/test_phase10k8zh7_execution_game_theory_foundation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/institutional_risk_engine.py`

- imports_from: `src.market_intelligence.institutional_cross_asset_scores`
- imported_by: `src/market_intelligence/institutional_cross_asset_lab.py`
- runtime_callers: `src/market_intelligence/institutional_cross_asset_lab.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/kelly_staking.py`

- imports_from: `src.core.math_utils`
- imported_by: `tests/test_kelly_staking.py`
- runtime_callers: `none`
- test_callers: `tests/test_kelly_staking.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/liquidity_context_scoring.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/liquidity_risk.py`

- imports_from: `src.services.scheduler_config`
- imported_by: `src/market_intelligence/arbitrage/arbitrage_risk_filters.py`
- runtime_callers: `src/market_intelligence/arbitrage/arbitrage_risk_filters.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/market_clock.py`

- imports_from: `none`
- imported_by: `src/analytics/review_queue.py, tests/test_market_clock.py`
- runtime_callers: `src/analytics/review_queue.py`
- test_callers: `tests/test_market_clock.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/market_impact.py`

- imports_from: `src.core.execution`
- imported_by: `src/core/game_theory.py, src/core/quant_engine.py, src/services/decision_engine.py, tests/test_phase10k8zh7_execution_game_theory_foundation.py`
- runtime_callers: `src/core/game_theory.py, src/core/quant_engine.py, src/services/decision_engine.py`
- test_callers: `tests/test_phase10k8zh7_execution_game_theory_foundation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/market_pricing.py`

- imports_from: `src.core.clv, src.core.math_utils, src.core.pricing`
- imported_by: `main.py, src/services/bet_decision_engine.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py, tests/test_price_event.py`
- runtime_callers: `src/services/bet_decision_engine.py`
- test_callers: `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py, tests/test_price_event.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/market_structure.py`

- imports_from: `src.providers.kalshi_scoring`
- imported_by: `src/services/scheduler_runner.py`
- runtime_callers: `src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/math_utils.py`

- imports_from: `none`
- imported_by: `scripts/init_sports_master_db.py, src/api/model_card_service.py, src/core/backtester.py, src/core/clv.py, src/core/cross_book_line_comparator.py, src/core/ev_line_shopper.py, src/core/kelly_staking.py, src/core/market_pricing.py, src/core/no_vig_pricing.py, src/core/opportunity_scanner.py, src/core/portfolio.py, src/core/pricing.py, src/core/probability.py, src/core/quant_engine.py, src/core/risk_engine.py, src/providers/sportsbooks/adapters.py, src/services/bet_log.py, src/sports/nba_features.py, tests/test_phase10k5_core_arbitrage_engine.py, tests/test_phase10k8zfg_safe_migration_batch_1.py, tests/test_phase10k8zh1_core_math_foundation_batch.py, tests/test_phase10k8zhi_legacy_full_gate_remediation.py`
- runtime_callers: `src/api/model_card_service.py, src/core/backtester.py, src/core/clv.py, src/core/cross_book_line_comparator.py, src/core/ev_line_shopper.py, src/core/kelly_staking.py, src/core/market_pricing.py, src/core/no_vig_pricing.py, src/core/opportunity_scanner.py, src/core/portfolio.py, src/core/pricing.py, src/core/probability.py, src/core/quant_engine.py, src/core/risk_engine.py, src/providers/sportsbooks/adapters.py, src/services/bet_log.py, src/sports/nba_features.py`
- test_callers: `tests/test_phase10k5_core_arbitrage_engine.py, tests/test_phase10k8zfg_safe_migration_batch_1.py, tests/test_phase10k8zh1_core_math_foundation_batch.py, tests/test_phase10k8zhi_legacy_full_gate_remediation.py`
- script_callers: `scripts/init_sports_master_db.py`
- api_callers: `src/api/model_card_service.py`
- facade_callers: `tests/test_phase10k8zhi_legacy_full_gate_remediation.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/model_probability.py`

- imports_from: `src.core.probability`
- imported_by: `main.py, tests/test_model_probability.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- runtime_callers: `none`
- test_callers: `tests/test_model_probability.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/no_vig_pricing.py`

- imports_from: `src.core.math_utils`
- imported_by: `src/core/ev_line_shopper.py`
- runtime_callers: `src/core/ev_line_shopper.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/opportunity_scanner.py`

- imports_from: `src.core.math_utils`
- imported_by: `src/api/market_utility_routes.py, src/market_intelligence/arbitrage/exchange_arbitrage.py, src/market_intelligence/arbitrage/prediction_market_arbitrage.py, src/market_intelligence/arbitrage/three_way_arbitrage.py, src/market_intelligence/arbitrage/two_way_arbitrage.py, src/market_intelligence/arbitrage_detector.py, src/market_intelligence/middle_opportunity_detector.py, src/market_intelligence/middles/middle_ev_simulator.py`
- runtime_callers: `src/api/market_utility_routes.py, src/market_intelligence/arbitrage/exchange_arbitrage.py, src/market_intelligence/arbitrage/prediction_market_arbitrage.py, src/market_intelligence/arbitrage/three_way_arbitrage.py, src/market_intelligence/arbitrage/two_way_arbitrage.py, src/market_intelligence/arbitrage_detector.py, src/market_intelligence/middle_opportunity_detector.py, src/market_intelligence/middles/middle_ev_simulator.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `src/api/market_utility_routes.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/portfolio.py`

- imports_from: `src.core.math_utils`
- imported_by: `src/core/quant_engine.py, src/services/decision_engine.py, tests/test_phase10k8zh6_portfolio_foundation.py`
- runtime_callers: `src/core/quant_engine.py, src/services/decision_engine.py`
- test_callers: `tests/test_phase10k8zh6_portfolio_foundation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/pricing.py`

- imports_from: `src.core.math_utils`
- imported_by: `src/core/market_pricing.py, src/core/probability.py, src/core/quant_engine.py, src/services/decision_engine.py, tests/test_phase10k8zh4_core_pricing_extraction.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- runtime_callers: `src/core/market_pricing.py, src/core/probability.py, src/core/quant_engine.py, src/services/decision_engine.py`
- test_callers: `tests/test_phase10k8zh4_core_pricing_extraction.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/probability.py`

- imports_from: `src.core.math_utils, src.core.pricing`
- imported_by: `src/core/model_probability.py, src/core/quant_engine.py, tests/test_phase10k8zh5_core_probability_extraction.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- runtime_callers: `src/core/model_probability.py, src/core/quant_engine.py`
- test_callers: `tests/test_phase10k8zh5_core_probability_extraction.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/quant_engine.py`

- imports_from: `src.core.execution, src.core.game_theory, src.core.market_impact, src.core.math_utils, src.core.portfolio, src.core.pricing, src.core.probability, src.core.risk, src.core.risk_engine`
- imported_by: `main.py, src/market_intelligence/multi_sport_model_registry.py, src/services/bet_decision_engine.py, src/services/streamlit_dashboard_data.py, tests/test_evaluate_lines.py, tests/test_phase10k8f_paper_only_fixture_evaluation_helper.py, tests/test_phase10k8g_paper_only_evaluation_readiness_adapter.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py, tests/test_quant_engine_foundation.py`
- runtime_callers: `src/market_intelligence/multi_sport_model_registry.py, src/services/bet_decision_engine.py, src/services/streamlit_dashboard_data.py`
- test_callers: `tests/test_evaluate_lines.py, tests/test_phase10k8f_paper_only_fixture_evaluation_helper.py, tests/test_phase10k8g_paper_only_evaluation_readiness_adapter.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py, tests/test_quant_engine_foundation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/random_matrix_risk.py`

- imports_from: `src.security.policy`
- imported_by: `src/research/correlation_structure_diagnostics.py, src/research/extreme_randomness_diagnostics.py`
- runtime_callers: `src/research/correlation_structure_diagnostics.py, src/research/extreme_randomness_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/risk.py`

- imports_from: `none`
- imported_by: `src/core/quant_engine.py, src/core/risk_engine.py, src/services/decision_engine.py, tests/test_phase10k8zh2_risk_foundation_batch.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py, tests/test_phase10k8zhi_legacy_full_gate_remediation.py`
- runtime_callers: `src/core/quant_engine.py, src/core/risk_engine.py, src/services/decision_engine.py`
- test_callers: `tests/test_phase10k8zh2_risk_foundation_batch.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py, tests/test_phase10k8zhi_legacy_full_gate_remediation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py, tests/test_phase10k8zhi_legacy_full_gate_remediation.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/risk_engine.py`

- imports_from: `src.core.clv, src.core.math_utils, src.core.risk`
- imported_by: `src/core/exposure_limits.py, src/core/quant_engine.py, src/core/stake_sizing_simulator.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- runtime_callers: `src/core/exposure_limits.py, src/core/quant_engine.py, src/core/stake_sizing_simulator.py`
- test_callers: `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/risk_of_ruin.py`

- imports_from: `none`
- imported_by: `tests/test_risk_of_ruin.py`
- runtime_callers: `none`
- test_callers: `tests/test_risk_of_ruin.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/session_risk_rules.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/settings.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `data/agent_state.json, data/alert_ledger.jsonl, data/exposure_ledger.jsonl, data/live_agent.log, data/provider_cache.json, models/compressed/model_registry.json`

## `src/core/stake_confidence.py`

- imports_from: `none`
- imported_by: `tests/test_kelly_staking.py, tests/test_stake_confidence.py`
- runtime_callers: `none`
- test_callers: `tests/test_kelly_staking.py, tests/test_stake_confidence.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/stake_sizing_simulator.py`

- imports_from: `src.core.risk_engine`
- imported_by: `tests/test_institutional_cross_asset_lab.py, tests/test_stake_sizing_simulator.py`
- runtime_callers: `none`
- test_callers: `tests/test_institutional_cross_asset_lab.py, tests/test_stake_sizing_simulator.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/status_codes.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/strategy_context_buckets.py`

- imports_from: `src.security.policy, src.security.secret_safety`
- imported_by: `src/core/strategy_maturity.py, src/core/strategy_promotion.py, src/core/strategy_router.py`
- runtime_callers: `src/core/strategy_maturity.py, src/core/strategy_promotion.py, src/core/strategy_router.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/strategy_disagreement.py`

- imports_from: `src.data.data_paths, src.security.policy, src.security.secret_safety, src.services.scheduler_config`
- imported_by: `src/core/strategy_score_aggregator.py, tests/test_strategy_framework.py`
- runtime_callers: `src/core/strategy_score_aggregator.py`
- test_callers: `tests/test_strategy_framework.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/strategy_maturity.py`

- imports_from: `src.core.strategy_context_buckets, src.core.strategy_registry, src.security.policy`
- imported_by: `src/core/strategy_router.py`
- runtime_callers: `src/core/strategy_router.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/strategy_promotion.py`

- imports_from: `src.brokerage.readiness, src.core.strategy_context_buckets, src.core.strategy_registry, src.security.policy, src.security.secret_safety`
- imported_by: `tests/test_strategy_framework.py`
- runtime_callers: `none`
- test_callers: `tests/test_strategy_framework.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/strategy_registry.py`

- imports_from: `src.security.policy`
- imported_by: `src/analytics/strategy_readiness_report.py, src/core/strategy_maturity.py, src/core/strategy_promotion.py, src/core/strategy_router.py, src/core/strategy_score_aggregator.py`
- runtime_callers: `src/analytics/strategy_readiness_report.py, src/core/strategy_maturity.py, src/core/strategy_promotion.py, src/core/strategy_router.py, src/core/strategy_score_aggregator.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/strategy_router.py`

- imports_from: `src.core.strategy_context_buckets, src.core.strategy_maturity, src.core.strategy_registry, src.security.policy, src.security.secret_safety`
- imported_by: `src/core/strategy_score_aggregator.py`
- runtime_callers: `src/core/strategy_score_aggregator.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/core/strategy_score_aggregator.py`

- imports_from: `src.brokerage.readiness, src.core.strategy_disagreement, src.core.strategy_registry, src.core.strategy_router, src.security.policy, src.security.secret_safety`
- imported_by: `tests/test_strategy_framework.py`
- runtime_callers: `none`
- test_callers: `tests/test_strategy_framework.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/data/__init__.py`

- imports_from: `src.data.contracts, src.data.local_loader, src.data.metadata, src.data.source_registry, src.data.validation`
- imported_by: `src/ai/deepseek_data_pull_check.py, src/analytics/derived_feature_backfill_report.py, src/backtesting/backtest_strategy_profiles.py, src/backtesting/historical_bridge.py, src/core/cross_book_line_comparator.py, src/core/ev_line_shopper.py, src/data/historical_odds.py, src/data/historical_sources.py, src/data/line_movement.py, src/market_intelligence/arbitrage/two_way_arbitrage.py, src/market_intelligence/arbitrage_detector.py, src/market_intelligence/middle_opportunity_detector.py, src/market_intelligence/model_input_coverage.py, src/market_intelligence/nfl_coaching_feature_builders.py, src/market_intelligence/nfl_coaching_sources.py, src/market_intelligence/nfl_cutoff_week_features.py, src/providers/ncaaf_collegefootballdata_adapter.py, src/providers/nfl_coaching_adapters.py, src/providers/nfl_open_data_adapters.py, src/providers/nfl_open_data_backfill.py, src/providers/nfl_open_data_feature_builders.py, src/providers/nfl_open_data_feature_readiness.py, src/research/feature_control.py, src/services/automation_scheduler_facade.py, src/services/ops_workflow.py, src/services/streamlit_dashboard_data.py, src/services/streamlit_dashboard_facade.py, tests/test_data_source_endpoints.py, tests/test_data_source_registry.py, tests/test_data_source_research_lanes.py, tests/test_historical_odds_sqlite.py, tests/test_nfl_historical_pattern_lab.py, tests/test_nfl_source_exhaustion.py, tests/test_odds_line_monitor.py, tests/test_open_sports_history_backfill.py, tests/test_open_sports_history_import.py, tests/test_open_sports_history_sources.py, tests/test_phase10k2_sports_snapshot_pipeline.py, tests/test_phase10k8o_dedicated_0dte_paper_fixture_template.py, tests/test_phase10k8p_dedicated_0dte_fixture_validation_adapter.py, tests/test_phase10k8q_dedicated_0dte_validation_readiness_payload.py, tests/test_phase10k8r_dedicated_0dte_validation_readiness_ui.py, tests/test_phase10k8s_dedicated_0dte_paper_evaluation_adapter.py, tests/test_phase10k8t_dedicated_0dte_evaluation_readiness_payload.py, tests/test_phase10k8u_dedicated_0dte_evaluation_ui.py, tests/test_phase10k8v_full_0dte_paper_pipeline_adapter.py, tests/test_phase10k8w_full_0dte_paper_pipeline_ui.py, tests/test_phase10k8x_controlled_0dte_paper_run_smoke_review.py, tests/test_phase10k8y_0dte_prediction_testing_readiness_review.py, tests/test_phase10k8za_0dte_data_field_formula_coverage_audit.py, tests/test_phase10k8zb_0dte_field_formula_gap_patch.py, tests/test_phase10k8ze_institutional_market_metric_catalog.py, tests/test_phase10k8zf1_compatibility_alias_migration.py, tests/test_phase10k8zf2_production_symbol_migration.py, tests/test_phase10k8zhj_data_foundation.py, tests/test_phase10k8zhm_data_backtesting_checkpoint.py, tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py, tests/test_synthetic_line_movement_sandbox.py`
- runtime_callers: `src/ai/deepseek_data_pull_check.py, src/analytics/derived_feature_backfill_report.py, src/backtesting/backtest_strategy_profiles.py, src/backtesting/historical_bridge.py, src/core/cross_book_line_comparator.py, src/core/ev_line_shopper.py, src/data/historical_odds.py, src/data/historical_sources.py, src/data/line_movement.py, src/market_intelligence/arbitrage/two_way_arbitrage.py, src/market_intelligence/arbitrage_detector.py, src/market_intelligence/middle_opportunity_detector.py, src/market_intelligence/model_input_coverage.py, src/market_intelligence/nfl_coaching_feature_builders.py, src/market_intelligence/nfl_coaching_sources.py, src/market_intelligence/nfl_cutoff_week_features.py, src/providers/ncaaf_collegefootballdata_adapter.py, src/providers/nfl_coaching_adapters.py, src/providers/nfl_open_data_adapters.py, src/providers/nfl_open_data_backfill.py, src/providers/nfl_open_data_feature_builders.py, src/providers/nfl_open_data_feature_readiness.py, src/research/feature_control.py, src/services/automation_scheduler_facade.py, src/services/ops_workflow.py, src/services/streamlit_dashboard_data.py, src/services/streamlit_dashboard_facade.py`
- test_callers: `tests/test_data_source_endpoints.py, tests/test_data_source_registry.py, tests/test_data_source_research_lanes.py, tests/test_historical_odds_sqlite.py, tests/test_nfl_historical_pattern_lab.py, tests/test_nfl_source_exhaustion.py, tests/test_odds_line_monitor.py, tests/test_open_sports_history_backfill.py, tests/test_open_sports_history_import.py, tests/test_open_sports_history_sources.py, tests/test_phase10k2_sports_snapshot_pipeline.py, tests/test_phase10k8o_dedicated_0dte_paper_fixture_template.py, tests/test_phase10k8p_dedicated_0dte_fixture_validation_adapter.py, tests/test_phase10k8q_dedicated_0dte_validation_readiness_payload.py, tests/test_phase10k8r_dedicated_0dte_validation_readiness_ui.py, tests/test_phase10k8s_dedicated_0dte_paper_evaluation_adapter.py, tests/test_phase10k8t_dedicated_0dte_evaluation_readiness_payload.py, tests/test_phase10k8u_dedicated_0dte_evaluation_ui.py, tests/test_phase10k8v_full_0dte_paper_pipeline_adapter.py, tests/test_phase10k8w_full_0dte_paper_pipeline_ui.py, tests/test_phase10k8x_controlled_0dte_paper_run_smoke_review.py, tests/test_phase10k8y_0dte_prediction_testing_readiness_review.py, tests/test_phase10k8za_0dte_data_field_formula_coverage_audit.py, tests/test_phase10k8zb_0dte_field_formula_gap_patch.py, tests/test_phase10k8ze_institutional_market_metric_catalog.py, tests/test_phase10k8zf1_compatibility_alias_migration.py, tests/test_phase10k8zf2_production_symbol_migration.py, tests/test_phase10k8zhj_data_foundation.py, tests/test_phase10k8zhm_data_backtesting_checkpoint.py, tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py, tests/test_synthetic_line_movement_sandbox.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py, src/services/streamlit_dashboard_facade.py, tests/test_phase10k8zf1_compatibility_alias_migration.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/data/contracts.py`

- imports_from: `none`
- imported_by: `src/data/__init__.py, src/data/historical_sources.py, src/data/local_loader.py, src/data/metadata.py, src/data/source_registry.py, src/data/validation.py`
- runtime_callers: `src/data/__init__.py, src/data/historical_sources.py, src/data/local_loader.py, src/data/metadata.py, src/data/source_registry.py, src/data/validation.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/data/data_paths.py`

- imports_from: `none`
- imported_by: `src/ai/deepseek_daily_report.py, src/ai/deepseek_data_pull_check.py, src/ai/deepseek_disagreement_queue.py, src/ai/deepseek_profit_lab.py, src/ai/institutional_deepseek_review.py, src/analytics/advanced_red_team_report.py, src/analytics/calibration.py, src/analytics/calibration_collector.py, src/analytics/derived_feature_backfill_report.py, src/analytics/institutional_cross_asset_reports.py, src/analytics/intelligence_readiness_report.py, src/analytics/manifold_calibration.py, src/analytics/manifold_review_queue.py, src/analytics/model_performance_report.py, src/analytics/pattern_review_queue.py, src/backtesting/backtesting_engine.py, src/backtesting/bankroll_state.py, src/brokerage/paper_decision_ledger.py, src/brokerage/paper_trade_ledger.py, src/core/strategy_disagreement.py, src/market_intelligence/clv_tracker.py, src/market_intelligence/institutional_cross_asset_lab.py, src/market_intelligence/local_sports_history_audit.py, src/market_intelligence/manifold_cluster_registry.py, src/market_intelligence/nfl_coaching_feature_builders.py, src/market_intelligence/nfl_coaching_sources.py, src/market_intelligence/nfl_cutoff_week_features.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/providers/institutional_cross_asset_adapters.py, src/providers/ncaaf_collegefootballdata_adapter.py, src/providers/nfl_coaching_adapters.py, src/providers/nfl_open_data_adapters.py, src/providers/nfl_open_data_backfill.py, src/providers/nfl_open_data_feature_builders.py, src/providers/nfl_open_data_feature_readiness.py, src/research/extreme_randomness_report.py, src/security/hard_gate_policy.py, src/security/owner_approval_gate.py, src/services/automation_scheduler_facade.py, src/services/collector_scheduled_runner.py, src/services/ops_workflow.py, src/services/outcome_store.py, src/services/scheduler_config.py, src/services/scheduler_runner.py, src/services/security_readiness.py, src/services/system_health.py`
- runtime_callers: `src/ai/deepseek_daily_report.py, src/ai/deepseek_data_pull_check.py, src/ai/deepseek_disagreement_queue.py, src/ai/deepseek_profit_lab.py, src/ai/institutional_deepseek_review.py, src/analytics/advanced_red_team_report.py, src/analytics/calibration.py, src/analytics/calibration_collector.py, src/analytics/derived_feature_backfill_report.py, src/analytics/institutional_cross_asset_reports.py, src/analytics/intelligence_readiness_report.py, src/analytics/manifold_calibration.py, src/analytics/manifold_review_queue.py, src/analytics/model_performance_report.py, src/analytics/pattern_review_queue.py, src/backtesting/backtesting_engine.py, src/backtesting/bankroll_state.py, src/brokerage/paper_decision_ledger.py, src/brokerage/paper_trade_ledger.py, src/core/strategy_disagreement.py, src/market_intelligence/clv_tracker.py, src/market_intelligence/institutional_cross_asset_lab.py, src/market_intelligence/local_sports_history_audit.py, src/market_intelligence/manifold_cluster_registry.py, src/market_intelligence/nfl_coaching_feature_builders.py, src/market_intelligence/nfl_coaching_sources.py, src/market_intelligence/nfl_cutoff_week_features.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/providers/institutional_cross_asset_adapters.py, src/providers/ncaaf_collegefootballdata_adapter.py, src/providers/nfl_coaching_adapters.py, src/providers/nfl_open_data_adapters.py, src/providers/nfl_open_data_backfill.py, src/providers/nfl_open_data_feature_builders.py, src/providers/nfl_open_data_feature_readiness.py, src/research/extreme_randomness_report.py, src/security/hard_gate_policy.py, src/security/owner_approval_gate.py, src/services/automation_scheduler_facade.py, src/services/collector_scheduled_runner.py, src/services/ops_workflow.py, src/services/outcome_store.py, src/services/scheduler_config.py, src/services/scheduler_runner.py, src/services/security_readiness.py, src/services/system_health.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/data/historical_odds.py`

- imports_from: `src.backtesting.historical_bridge, src.data, src.data.historical_sources, src.data.line_movement`
- imported_by: `src/backtesting/historical_bridge.py, src/data/line_movement.py, src/market_intelligence/feature_packs.py, src/research/feature_control.py, src/services/streamlit_dashboard_data.py, tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py, tests/test_streamlit_dashboard_data.py`
- runtime_callers: `src/backtesting/historical_bridge.py, src/data/line_movement.py, src/market_intelligence/feature_packs.py, src/research/feature_control.py, src/services/streamlit_dashboard_data.py`
- test_callers: `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py, tests/test_streamlit_dashboard_data.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `data/historical/uploads`

## `src/data/historical_sources.py`

- imports_from: `src.data, src.data.contracts, src.data.source_registry`
- imported_by: `src/data/historical_odds.py, src/services/streamlit_dashboard_data.py, tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- runtime_callers: `src/data/historical_odds.py, src/services/streamlit_dashboard_data.py`
- test_callers: `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/data/line_movement.py`

- imports_from: `src.data, src.data.historical_odds, src.services.streamlit_dashboard_data`
- imported_by: `src/data/historical_odds.py, src/services/streamlit_dashboard_data.py, tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py, tests/test_streamlit_dashboard_data.py`
- runtime_callers: `src/data/historical_odds.py, src/services/streamlit_dashboard_data.py`
- test_callers: `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py, tests/test_streamlit_dashboard_data.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/data/local_loader.py`

- imports_from: `src.data.contracts, src.data.validation`
- imported_by: `src/data/__init__.py`
- runtime_callers: `src/data/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/data/metadata.py`

- imports_from: `src.data.contracts`
- imported_by: `src/data/__init__.py`
- runtime_callers: `src/data/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/data/source_event_links.py`

- imports_from: `none`
- imported_by: `src/services/streamlit_dashboard_data.py, tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- runtime_callers: `src/services/streamlit_dashboard_data.py`
- test_callers: `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/data/source_registry.py`

- imports_from: `src.data.contracts`
- imported_by: `src/data/__init__.py, src/data/historical_sources.py`
- runtime_callers: `src/data/__init__.py, src/data/historical_sources.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/data/validation.py`

- imports_from: `src.data.contracts`
- imported_by: `src/data/__init__.py, src/data/local_loader.py, tests/test_phase10k8zhj_data_foundation.py`
- runtime_callers: `src/data/__init__.py, src/data/local_loader.py`
- test_callers: `tests/test_phase10k8zhj_data_foundation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/__init__.py`

- imports_from: `src.market_intelligence.catalysts, src.market_intelligence.confidence, src.market_intelligence.contracts, src.market_intelligence.crypto, src.market_intelligence.flow, src.market_intelligence.futures, src.market_intelligence.impact, src.market_intelligence.liquidity, src.market_intelligence.manifold, src.market_intelligence.no_trade, src.market_intelligence.options, src.market_intelligence.positioning, src.market_intelligence.prediction_markets, src.market_intelligence.regime, src.market_intelligence.report, src.market_intelligence.risk, src.market_intelligence.scoring, src.market_intelligence.sports, src.market_intelligence.targets`
- imported_by: `src/market_intelligence/feature_packs.py, src/market_intelligence/nfl_coaching_feature_builders.py, tests/test_phase10k8zl2_market_intelligence_foundation.py, tests/test_phase10k8zl6_market_intelligence_runtime_test_redirection.py, tests/test_phase10k8zl7_market_intelligence_scheduler_deletion.py, tests/test_phase10k8zl8_market_intelligence_absorption_checkpoint.py`
- runtime_callers: `src/market_intelligence/feature_packs.py, src/market_intelligence/nfl_coaching_feature_builders.py`
- test_callers: `tests/test_phase10k8zl2_market_intelligence_foundation.py, tests/test_phase10k8zl6_market_intelligence_runtime_test_redirection.py, tests/test_phase10k8zl7_market_intelligence_scheduler_deletion.py, tests/test_phase10k8zl8_market_intelligence_absorption_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/_shared.py`

- imports_from: `none`
- imported_by: `src/market_intelligence/catalysts.py, src/market_intelligence/confidence.py, src/market_intelligence/flow.py, src/market_intelligence/liquidity.py, src/market_intelligence/manifold.py, src/market_intelligence/no_trade.py, src/market_intelligence/options.py, src/market_intelligence/positioning.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/regime.py, src/market_intelligence/report.py, src/market_intelligence/risk.py, src/market_intelligence/scoring.py, src/market_intelligence/sports.py, src/market_intelligence/targets.py`
- runtime_callers: `src/market_intelligence/catalysts.py, src/market_intelligence/confidence.py, src/market_intelligence/flow.py, src/market_intelligence/liquidity.py, src/market_intelligence/manifold.py, src/market_intelligence/no_trade.py, src/market_intelligence/options.py, src/market_intelligence/positioning.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/regime.py, src/market_intelligence/report.py, src/market_intelligence/risk.py, src/market_intelligence/scoring.py, src/market_intelligence/sports.py, src/market_intelligence/targets.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/arbitrage/__init__.py`

- imports_from: `src.market_intelligence.arbitrage.arbitrage_risk_filters, src.market_intelligence.arbitrage.draw_market_arbitrage, src.market_intelligence.arbitrage.exchange_arbitrage, src.market_intelligence.arbitrage.prediction_market_arbitrage, src.market_intelligence.arbitrage.three_way_arbitrage, src.market_intelligence.arbitrage.two_way_arbitrage`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/arbitrage/arbitrage_risk_filters.py`

- imports_from: `src.brokerage.settlement, src.core.liquidity_risk`
- imported_by: `src/market_intelligence/arbitrage/__init__.py`
- runtime_callers: `src/market_intelligence/arbitrage/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/arbitrage/draw_market_arbitrage.py`

- imports_from: `src.market_intelligence.arbitrage.three_way_arbitrage`
- imported_by: `src/market_intelligence/arbitrage/__init__.py`
- runtime_callers: `src/market_intelligence/arbitrage/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/arbitrage/exchange_arbitrage.py`

- imports_from: `src.core.opportunity_scanner`
- imported_by: `src/market_intelligence/arbitrage/__init__.py`
- runtime_callers: `src/market_intelligence/arbitrage/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/arbitrage/prediction_market_arbitrage.py`

- imports_from: `src.core.opportunity_scanner`
- imported_by: `src/market_intelligence/arbitrage/__init__.py`
- runtime_callers: `src/market_intelligence/arbitrage/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/arbitrage/three_way_arbitrage.py`

- imports_from: `src.core.opportunity_scanner, src.market_intelligence.bookmaker_normalizer`
- imported_by: `src/market_intelligence/arbitrage/__init__.py, src/market_intelligence/arbitrage/draw_market_arbitrage.py`
- runtime_callers: `src/market_intelligence/arbitrage/__init__.py, src/market_intelligence/arbitrage/draw_market_arbitrage.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/arbitrage/two_way_arbitrage.py`

- imports_from: `src.core.opportunity_scanner, src.data, src.market_intelligence.bookmaker_normalizer`
- imported_by: `src/market_intelligence/arbitrage/__init__.py, tests/test_phase10k5_core_arbitrage_engine.py`
- runtime_callers: `src/market_intelligence/arbitrage/__init__.py`
- test_callers: `tests/test_phase10k5_core_arbitrage_engine.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/arbitrage_detector.py`

- imports_from: `src.core.opportunity_scanner, src.data, src.market_intelligence.bookmaker_normalizer`
- imported_by: `src/services/scheduler_runner.py`
- runtime_callers: `src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_availability_context.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_batter_impact.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_bullpen_context.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_data_availability.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py, src/market_intelligence/baseball_impact_readiness.py`
- runtime_callers: `src/analytics/baseball_impact_report.py, src/market_intelligence/baseball_impact_readiness.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_defense_baserunning_context.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_impact_common.py`

- imports_from: `src.security.policy, src.security.secret_safety`
- imported_by: `src/analytics/baseball_impact_calibration.py, src/analytics/baseball_impact_red_team.py, src/analytics/baseball_impact_report.py, src/market_intelligence/baseball_availability_context.py, src/market_intelligence/baseball_batter_impact.py, src/market_intelligence/baseball_bullpen_context.py, src/market_intelligence/baseball_data_availability.py, src/market_intelligence/baseball_defense_baserunning_context.py, src/market_intelligence/baseball_impact_readiness.py, src/market_intelligence/baseball_incentive_context.py, src/market_intelligence/baseball_lineup_context.py, src/market_intelligence/baseball_market_relevance.py, src/market_intelligence/baseball_matchup_context.py, src/market_intelligence/baseball_park_weather_umpire_context.py, src/market_intelligence/baseball_pitcher_impact.py, src/market_intelligence/baseball_run_value_impact.py`
- runtime_callers: `src/analytics/baseball_impact_calibration.py, src/analytics/baseball_impact_red_team.py, src/analytics/baseball_impact_report.py, src/market_intelligence/baseball_availability_context.py, src/market_intelligence/baseball_batter_impact.py, src/market_intelligence/baseball_bullpen_context.py, src/market_intelligence/baseball_data_availability.py, src/market_intelligence/baseball_defense_baserunning_context.py, src/market_intelligence/baseball_impact_readiness.py, src/market_intelligence/baseball_incentive_context.py, src/market_intelligence/baseball_lineup_context.py, src/market_intelligence/baseball_market_relevance.py, src/market_intelligence/baseball_matchup_context.py, src/market_intelligence/baseball_park_weather_umpire_context.py, src/market_intelligence/baseball_pitcher_impact.py, src/market_intelligence/baseball_run_value_impact.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_impact_readiness.py`

- imports_from: `src.market_intelligence.baseball_data_availability, src.market_intelligence.baseball_impact_common`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_incentive_context.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_lineup_context.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_market_relevance.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_matchup_context.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_park_weather_umpire_context.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_pitcher_impact.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/baseball_run_value_impact.py`

- imports_from: `src.market_intelligence.baseball_impact_common`
- imported_by: `src/analytics/baseball_impact_report.py`
- runtime_callers: `src/analytics/baseball_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/basketball_incentive_context.py`

- imports_from: `src.market_intelligence.basketball_player_impact_common`
- imported_by: `src/market_intelligence/basketball_player_impact.py`
- runtime_callers: `src/market_intelligence/basketball_player_impact.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/basketball_lineup_matchup_context.py`

- imports_from: `src.market_intelligence.basketball_player_impact_common`
- imported_by: `src/market_intelligence/basketball_player_impact.py`
- runtime_callers: `src/market_intelligence/basketball_player_impact.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/basketball_market_relevance.py`

- imports_from: `src.market_intelligence.basketball_player_impact_common`
- imported_by: `src/market_intelligence/basketball_player_impact.py`
- runtime_callers: `src/market_intelligence/basketball_player_impact.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/basketball_player_impact.py`

- imports_from: `src.analytics.basketball_player_impact_calibration, src.analytics.basketball_player_impact_red_team, src.market_intelligence.basketball_incentive_context, src.market_intelligence.basketball_lineup_matchup_context, src.market_intelligence.basketball_market_relevance, src.market_intelligence.basketball_player_impact_common, src.market_intelligence.basketball_possession_impact, src.market_intelligence.basketball_role_context, src.market_intelligence.basketball_tracking_opportunity, src.security.policy`
- imported_by: `tests/test_basketball_player_impact.py`
- runtime_callers: `none`
- test_callers: `tests/test_basketball_player_impact.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/basketball_player_impact_common.py`

- imports_from: `src.security.policy, src.security.secret_safety`
- imported_by: `src/analytics/basketball_player_impact_calibration.py, src/analytics/basketball_player_impact_red_team.py, src/market_intelligence/basketball_incentive_context.py, src/market_intelligence/basketball_lineup_matchup_context.py, src/market_intelligence/basketball_market_relevance.py, src/market_intelligence/basketball_player_impact.py, src/market_intelligence/basketball_player_impact_readiness.py, src/market_intelligence/basketball_possession_impact.py, src/market_intelligence/basketball_role_context.py, src/market_intelligence/basketball_tracking_opportunity.py`
- runtime_callers: `src/analytics/basketball_player_impact_calibration.py, src/analytics/basketball_player_impact_red_team.py, src/market_intelligence/basketball_incentive_context.py, src/market_intelligence/basketball_lineup_matchup_context.py, src/market_intelligence/basketball_market_relevance.py, src/market_intelligence/basketball_player_impact.py, src/market_intelligence/basketball_player_impact_readiness.py, src/market_intelligence/basketball_possession_impact.py, src/market_intelligence/basketball_role_context.py, src/market_intelligence/basketball_tracking_opportunity.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/basketball_player_impact_readiness.py`

- imports_from: `src.market_intelligence.basketball_player_impact_common`
- imported_by: `tests/test_basketball_player_impact.py`
- runtime_callers: `none`
- test_callers: `tests/test_basketball_player_impact.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/basketball_possession_impact.py`

- imports_from: `src.market_intelligence.basketball_player_impact_common`
- imported_by: `src/market_intelligence/basketball_player_impact.py`
- runtime_callers: `src/market_intelligence/basketball_player_impact.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/basketball_role_context.py`

- imports_from: `src.market_intelligence.basketball_player_impact_common`
- imported_by: `src/market_intelligence/basketball_player_impact.py`
- runtime_callers: `src/market_intelligence/basketball_player_impact.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/basketball_tracking_opportunity.py`

- imports_from: `src.market_intelligence.basketball_player_impact_common`
- imported_by: `src/market_intelligence/basketball_player_impact.py`
- runtime_callers: `src/market_intelligence/basketball_player_impact.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/bookmaker_normalizer.py`

- imports_from: `none`
- imported_by: `src/core/cross_book_line_comparator.py, src/core/ev_line_shopper.py, src/market_intelligence/arbitrage/three_way_arbitrage.py, src/market_intelligence/arbitrage/two_way_arbitrage.py, src/market_intelligence/arbitrage_detector.py, src/market_intelligence/middle_opportunity_detector.py`
- runtime_callers: `src/core/cross_book_line_comparator.py, src/core/ev_line_shopper.py, src/market_intelligence/arbitrage/three_way_arbitrage.py, src/market_intelligence/arbitrage/two_way_arbitrage.py, src/market_intelligence/arbitrage_detector.py, src/market_intelligence/middle_opportunity_detector.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/candlestick_manifold_detector.py`

- imports_from: `src.market_intelligence.market_state_manifold`
- imported_by: `src/market_intelligence/cross_asset_manifold_router.py`
- runtime_callers: `src/market_intelligence/cross_asset_manifold_router.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/candlestick_pattern_detector.py`

- imports_from: `src.services.scheduler_config`
- imported_by: `src/services/runtime_shared.py`
- runtime_callers: `src/services/runtime_shared.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/catalysts.py`

- imports_from: `src.market_intelligence._shared`
- imported_by: `src/market_intelligence/__init__.py`
- runtime_callers: `src/market_intelligence/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/clv_tracker.py`

- imports_from: `src.core.clv, src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/backtesting/backtesting_engine.py, src/core/ev_line_shopper.py, src/services/system_health.py`
- runtime_callers: `src/backtesting/backtesting_engine.py, src/core/ev_line_shopper.py, src/services/system_health.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_availability_context.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_damage_durability_context.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_data_availability.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_grappling_control_impact.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_impact_common.py`

- imports_from: `src.security.policy, src.security.secret_safety`
- imported_by: `src/analytics/combat_impact_calibration.py, src/analytics/combat_impact_red_team.py, src/analytics/combat_impact_report.py, src/market_intelligence/combat_availability_context.py, src/market_intelligence/combat_damage_durability_context.py, src/market_intelligence/combat_data_availability.py, src/market_intelligence/combat_grappling_control_impact.py, src/market_intelligence/combat_impact_readiness.py, src/market_intelligence/combat_incentive_context.py, src/market_intelligence/combat_market_relevance.py, src/market_intelligence/combat_matchup_context.py, src/market_intelligence/combat_pace_cardio_context.py, src/market_intelligence/combat_phase_control_context.py, src/market_intelligence/combat_ruleset_referee_judging_context.py, src/market_intelligence/combat_striking_impact.py`
- runtime_callers: `src/analytics/combat_impact_calibration.py, src/analytics/combat_impact_red_team.py, src/analytics/combat_impact_report.py, src/market_intelligence/combat_availability_context.py, src/market_intelligence/combat_damage_durability_context.py, src/market_intelligence/combat_data_availability.py, src/market_intelligence/combat_grappling_control_impact.py, src/market_intelligence/combat_impact_readiness.py, src/market_intelligence/combat_incentive_context.py, src/market_intelligence/combat_market_relevance.py, src/market_intelligence/combat_matchup_context.py, src/market_intelligence/combat_pace_cardio_context.py, src/market_intelligence/combat_phase_control_context.py, src/market_intelligence/combat_ruleset_referee_judging_context.py, src/market_intelligence/combat_striking_impact.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_impact_readiness.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_incentive_context.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_market_relevance.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_matchup_context.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_pace_cardio_context.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_phase_control_context.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_ruleset_referee_judging_context.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/combat_striking_impact.py`

- imports_from: `src.market_intelligence.combat_impact_common`
- imported_by: `src/analytics/combat_impact_report.py`
- runtime_callers: `src/analytics/combat_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/confidence.py`

- imports_from: `src.market_intelligence._shared`
- imported_by: `src/market_intelligence/__init__.py, src/market_intelligence/impact.py, src/market_intelligence/manifold.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- runtime_callers: `src/market_intelligence/__init__.py, src/market_intelligence/impact.py, src/market_intelligence/manifold.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/contracts.py`

- imports_from: `none`
- imported_by: `src/market_intelligence/__init__.py, src/market_intelligence/report.py`
- runtime_callers: `src/market_intelligence/__init__.py, src/market_intelligence/report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/cross_asset_embedding_router.py`

- imports_from: `src.market_intelligence.manifold, src.research.representation_feature_builder, src.security.policy`
- imported_by: `src/market_intelligence/cross_asset_intelligence_router.py`
- runtime_callers: `src/market_intelligence/cross_asset_intelligence_router.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/cross_asset_intelligence_router.py`

- imports_from: `src.market_intelligence.cross_asset_embedding_router, src.market_intelligence.graph_relationship_mapper, src.research, src.research.causal_scaffold, src.security.policy`
- imported_by: `tests/test_data_intelligence_stack.py`
- runtime_callers: `none`
- test_callers: `tests/test_data_intelligence_stack.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/cross_asset_manifold_router.py`

- imports_from: `src.analytics.manifold_calibration, src.analytics.manifold_review_queue, src.market_intelligence.candlestick_manifold_detector, src.market_intelligence.manifold_cluster_registry, src.market_intelligence.market_state_manifold, src.market_intelligence.prediction_market_manifold_mapper, src.providers.sportsbook_manifold_mapper, src.services.execution_service`
- imported_by: `src/market_intelligence/manifold.py, tests/test_market_state_manifold.py`
- runtime_callers: `src/market_intelligence/manifold.py`
- test_callers: `tests/test_market_state_manifold.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/crypto.py`

- imports_from: `src.market_intelligence.flow, src.market_intelligence.liquidity, src.market_intelligence.report, src.market_intelligence.targets`
- imported_by: `src/market_intelligence/__init__.py`
- runtime_callers: `src/market_intelligence/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/data_intelligence_registry.py`

- imports_from: `src.research, src.security.policy`
- imported_by: `src/analytics/intelligence_readiness_report.py`
- runtime_callers: `src/analytics/intelligence_readiness_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/feature_packs.py`

- imports_from: `src.data.historical_odds, src.market_intelligence, src.market_intelligence.market_feature_packs, src.market_intelligence.sport_feature_packs, src.market_intelligence.sports`
- imported_by: `src/research/calibration_strategy_filter.py, src/research/feature_ablation_lab.py, src/research/feature_control.py, src/services/streamlit_dashboard_data.py, tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- runtime_callers: `src/research/calibration_strategy_filter.py, src/research/feature_ablation_lab.py, src/research/feature_control.py, src/services/streamlit_dashboard_data.py`
- test_callers: `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/flow.py`

- imports_from: `src.market_intelligence._shared`
- imported_by: `src/market_intelligence/__init__.py, src/market_intelligence/crypto.py, src/market_intelligence/futures.py, src/market_intelligence/manifold.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- runtime_callers: `src/market_intelligence/__init__.py, src/market_intelligence/crypto.py, src/market_intelligence/futures.py, src/market_intelligence/manifold.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/football_availability_context.py`

- imports_from: `src.market_intelligence.football_impact_schema`
- imported_by: `src/analytics/football_impact_report.py`
- runtime_callers: `src/analytics/football_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/football_data_availability.py`

- imports_from: `src.market_intelligence.football_impact_schema`
- imported_by: `src/analytics/football_impact_report.py`
- runtime_callers: `src/analytics/football_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/football_impact_common.py`

- imports_from: `src.market_intelligence.football_impact_schema`
- imported_by: `src/analytics/football_impact_red_team.py`
- runtime_callers: `src/analytics/football_impact_red_team.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/football_impact_schema.py`

- imports_from: `src.security.policy, src.security.secret_safety`
- imported_by: `src/analytics/football_impact_calibration.py, src/analytics/football_impact_report.py, src/market_intelligence/football_availability_context.py, src/market_intelligence/football_data_availability.py, src/market_intelligence/football_impact_common.py, src/market_intelligence/football_incentive_context.py, src/market_intelligence/football_market_relevance.py, src/market_intelligence/football_matchup_context.py, src/market_intelligence/football_personnel_context.py, src/market_intelligence/football_play_drive_impact.py, src/market_intelligence/football_role_impact.py`
- runtime_callers: `src/analytics/football_impact_calibration.py, src/analytics/football_impact_report.py, src/market_intelligence/football_availability_context.py, src/market_intelligence/football_data_availability.py, src/market_intelligence/football_impact_common.py, src/market_intelligence/football_incentive_context.py, src/market_intelligence/football_market_relevance.py, src/market_intelligence/football_matchup_context.py, src/market_intelligence/football_personnel_context.py, src/market_intelligence/football_play_drive_impact.py, src/market_intelligence/football_role_impact.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/football_incentive_context.py`

- imports_from: `src.market_intelligence.football_impact_schema`
- imported_by: `src/analytics/football_impact_report.py`
- runtime_callers: `src/analytics/football_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/football_market_relevance.py`

- imports_from: `src.market_intelligence.football_impact_schema`
- imported_by: `src/analytics/football_impact_report.py`
- runtime_callers: `src/analytics/football_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/football_matchup_context.py`

- imports_from: `src.market_intelligence.football_impact_schema`
- imported_by: `src/analytics/football_impact_report.py`
- runtime_callers: `src/analytics/football_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/football_personnel_context.py`

- imports_from: `src.market_intelligence.football_impact_schema`
- imported_by: `src/analytics/football_impact_report.py`
- runtime_callers: `src/analytics/football_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/football_play_drive_impact.py`

- imports_from: `src.market_intelligence.football_impact_schema`
- imported_by: `src/analytics/football_impact_report.py`
- runtime_callers: `src/analytics/football_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/football_role_impact.py`

- imports_from: `src.market_intelligence.football_impact_schema`
- imported_by: `src/analytics/football_impact_report.py`
- runtime_callers: `src/analytics/football_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/futures.py`

- imports_from: `src.market_intelligence.flow, src.market_intelligence.report, src.market_intelligence.targets`
- imported_by: `src/market_intelligence/__init__.py`
- runtime_callers: `src/market_intelligence/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_approach_impact.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_availability_context.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_course_fit_context.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_data_availability.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_field_tournament_context.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_impact_common.py`

- imports_from: `src.security.policy, src.security.secret_safety`
- imported_by: `src/analytics/golf_impact_calibration.py, src/analytics/golf_impact_red_team.py, src/analytics/golf_impact_report.py, src/market_intelligence/golf_approach_impact.py, src/market_intelligence/golf_availability_context.py, src/market_intelligence/golf_course_fit_context.py, src/market_intelligence/golf_data_availability.py, src/market_intelligence/golf_field_tournament_context.py, src/market_intelligence/golf_impact_readiness.py, src/market_intelligence/golf_incentive_context.py, src/market_intelligence/golf_market_relevance.py, src/market_intelligence/golf_off_tee_impact.py, src/market_intelligence/golf_short_game_putting_context.py, src/market_intelligence/golf_strokes_gained_impact.py, src/market_intelligence/golf_weather_wave_context.py`
- runtime_callers: `src/analytics/golf_impact_calibration.py, src/analytics/golf_impact_red_team.py, src/analytics/golf_impact_report.py, src/market_intelligence/golf_approach_impact.py, src/market_intelligence/golf_availability_context.py, src/market_intelligence/golf_course_fit_context.py, src/market_intelligence/golf_data_availability.py, src/market_intelligence/golf_field_tournament_context.py, src/market_intelligence/golf_impact_readiness.py, src/market_intelligence/golf_incentive_context.py, src/market_intelligence/golf_market_relevance.py, src/market_intelligence/golf_off_tee_impact.py, src/market_intelligence/golf_short_game_putting_context.py, src/market_intelligence/golf_strokes_gained_impact.py, src/market_intelligence/golf_weather_wave_context.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_impact_readiness.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_incentive_context.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_market_relevance.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_off_tee_impact.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_short_game_putting_context.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_strokes_gained_impact.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/golf_weather_wave_context.py`

- imports_from: `src.market_intelligence.golf_impact_common`
- imported_by: `src/analytics/golf_impact_report.py`
- runtime_callers: `src/analytics/golf_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/graph_relationship_mapper.py`

- imports_from: `src.market_intelligence.market_state_graph, src.security.policy`
- imported_by: `src/market_intelligence/cross_asset_intelligence_router.py`
- runtime_callers: `src/market_intelligence/cross_asset_intelligence_router.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_availability_context.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_data_availability.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py, src/market_intelligence/hockey_impact_readiness.py`
- runtime_callers: `src/analytics/hockey_impact_report.py, src/market_intelligence/hockey_impact_readiness.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_goalie_impact.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_impact_common.py`

- imports_from: `src.security.policy, src.security.secret_safety`
- imported_by: `src/analytics/hockey_impact_calibration.py, src/analytics/hockey_impact_red_team.py, src/analytics/hockey_impact_report.py, src/market_intelligence/hockey_availability_context.py, src/market_intelligence/hockey_data_availability.py, src/market_intelligence/hockey_goalie_impact.py, src/market_intelligence/hockey_impact_readiness.py, src/market_intelligence/hockey_incentive_context.py, src/market_intelligence/hockey_line_pair_context.py, src/market_intelligence/hockey_market_relevance.py, src/market_intelligence/hockey_matchup_context.py, src/market_intelligence/hockey_possession_impact.py, src/market_intelligence/hockey_skater_impact.py, src/market_intelligence/hockey_special_teams_context.py, src/market_intelligence/hockey_transition_context.py`
- runtime_callers: `src/analytics/hockey_impact_calibration.py, src/analytics/hockey_impact_red_team.py, src/analytics/hockey_impact_report.py, src/market_intelligence/hockey_availability_context.py, src/market_intelligence/hockey_data_availability.py, src/market_intelligence/hockey_goalie_impact.py, src/market_intelligence/hockey_impact_readiness.py, src/market_intelligence/hockey_incentive_context.py, src/market_intelligence/hockey_line_pair_context.py, src/market_intelligence/hockey_market_relevance.py, src/market_intelligence/hockey_matchup_context.py, src/market_intelligence/hockey_possession_impact.py, src/market_intelligence/hockey_skater_impact.py, src/market_intelligence/hockey_special_teams_context.py, src/market_intelligence/hockey_transition_context.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_impact_readiness.py`

- imports_from: `src.market_intelligence.hockey_data_availability, src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_incentive_context.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_line_pair_context.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_market_relevance.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_matchup_context.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_possession_impact.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_skater_impact.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_special_teams_context.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/hockey_transition_context.py`

- imports_from: `src.market_intelligence.hockey_impact_common`
- imported_by: `src/analytics/hockey_impact_report.py`
- runtime_callers: `src/analytics/hockey_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/impact.py`

- imports_from: `src.market_intelligence.confidence, src.market_intelligence.report, src.market_intelligence.risk, src.market_intelligence.targets`
- imported_by: `src/market_intelligence/__init__.py`
- runtime_callers: `src/market_intelligence/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/institutional_cross_asset_lab.py`

- imports_from: `src.ai.institutional_deepseek_review, src.analytics.institutional_cross_asset_calibration, src.analytics.institutional_cross_asset_reports, src.core.institutional_risk_engine, src.data.data_paths, src.providers.institutional_cross_asset_adapters, src.services.execution_service, src.services.ledger_service, src.services.scheduler_config`
- imported_by: `src/services/automation_scheduler_facade.py`
- runtime_callers: `src/services/automation_scheduler_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/institutional_cross_asset_scores.py`

- imports_from: `none`
- imported_by: `src/analytics/institutional_cross_asset_calibration.py, src/core/institutional_risk_engine.py, src/providers/institutional_cross_asset_adapters.py`
- runtime_callers: `src/analytics/institutional_cross_asset_calibration.py, src/core/institutional_risk_engine.py, src/providers/institutional_cross_asset_adapters.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/liquidity.py`

- imports_from: `src.market_intelligence._shared`
- imported_by: `src/market_intelligence/__init__.py, src/market_intelligence/crypto.py, src/market_intelligence/manifold.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- runtime_callers: `src/market_intelligence/__init__.py, src/market_intelligence/crypto.py, src/market_intelligence/manifold.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/local_sports_history_audit.py`

- imports_from: `src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/services/streamlit_dashboard_facade.py`
- runtime_callers: `src/services/streamlit_dashboard_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/streamlit_dashboard_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/manifold.py`

- imports_from: `src.market_intelligence._shared, src.market_intelligence.confidence, src.market_intelligence.cross_asset_manifold_router, src.market_intelligence.flow, src.market_intelligence.liquidity, src.market_intelligence.manifold_feature_builder, src.market_intelligence.market_state_manifold, src.market_intelligence.prediction_markets, src.market_intelligence.report, src.market_intelligence.sports, src.market_intelligence.targets`
- imported_by: `src/analytics/manifold_review_queue.py, src/market_intelligence/__init__.py, src/market_intelligence/cross_asset_embedding_router.py, src/market_intelligence/market_state_graph.py, src/market_intelligence/prediction_market_manifold_mapper.py, tests/test_phase10k8zl4_prediction_market_intelligence_absorption.py`
- runtime_callers: `src/analytics/manifold_review_queue.py, src/market_intelligence/__init__.py, src/market_intelligence/cross_asset_embedding_router.py, src/market_intelligence/market_state_graph.py, src/market_intelligence/prediction_market_manifold_mapper.py`
- test_callers: `tests/test_phase10k8zl4_prediction_market_intelligence_absorption.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/manifold_cluster_registry.py`

- imports_from: `src.data.data_paths, src.market_intelligence.manifold_feature_builder, src.services.scheduler_config`
- imported_by: `src/market_intelligence/cross_asset_manifold_router.py, src/market_intelligence/market_state_manifold.py`
- runtime_callers: `src/market_intelligence/cross_asset_manifold_router.py, src/market_intelligence/market_state_manifold.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/manifold_feature_builder.py`

- imports_from: `src.services.scheduler_config`
- imported_by: `src/analytics/intelligence_readiness_report.py, src/analytics/manifold_calibration.py, src/market_intelligence/manifold.py, src/market_intelligence/manifold_cluster_registry.py, src/market_intelligence/market_state_manifold.py, src/research/representation_feature_builder.py`
- runtime_callers: `src/analytics/intelligence_readiness_report.py, src/analytics/manifold_calibration.py, src/market_intelligence/manifold.py, src/market_intelligence/manifold_cluster_registry.py, src/market_intelligence/market_state_manifold.py, src/research/representation_feature_builder.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/market_feature_packs.py`

- imports_from: `none`
- imported_by: `src/market_intelligence/feature_packs.py`
- runtime_callers: `src/market_intelligence/feature_packs.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/market_state_graph.py`

- imports_from: `src.market_intelligence.manifold`
- imported_by: `src/market_intelligence/graph_relationship_mapper.py`
- runtime_callers: `src/market_intelligence/graph_relationship_mapper.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/market_state_manifold.py`

- imports_from: `src.analytics.manifold_calibration, src.market_intelligence.manifold_cluster_registry, src.market_intelligence.manifold_feature_builder, src.services.execution_service`
- imported_by: `src/market_intelligence/candlestick_manifold_detector.py, src/market_intelligence/cross_asset_manifold_router.py, src/market_intelligence/manifold.py, src/providers/sportsbook_manifold_mapper.py`
- runtime_callers: `src/market_intelligence/candlestick_manifold_detector.py, src/market_intelligence/cross_asset_manifold_router.py, src/market_intelligence/manifold.py, src/providers/sportsbook_manifold_mapper.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/middle_opportunity_detector.py`

- imports_from: `src.core.opportunity_scanner, src.data, src.market_intelligence.bookmaker_normalizer`
- imported_by: `src/market_intelligence/middles/alt_line_middle.py, src/market_intelligence/middles/key_number_middle.py, src/market_intelligence/middles/prop_middle.py, src/market_intelligence/middles/push_corridor_middle.py, src/market_intelligence/middles/spread_middle.py, src/market_intelligence/middles/team_total_middle.py, src/market_intelligence/middles/total_middle.py, src/services/scheduler_runner.py`
- runtime_callers: `src/market_intelligence/middles/alt_line_middle.py, src/market_intelligence/middles/key_number_middle.py, src/market_intelligence/middles/prop_middle.py, src/market_intelligence/middles/push_corridor_middle.py, src/market_intelligence/middles/spread_middle.py, src/market_intelligence/middles/team_total_middle.py, src/market_intelligence/middles/total_middle.py, src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/middles/__init__.py`

- imports_from: `src.market_intelligence.middles.alt_line_middle, src.market_intelligence.middles.key_number_middle, src.market_intelligence.middles.middle_ev_simulator, src.market_intelligence.middles.prop_middle, src.market_intelligence.middles.push_corridor_middle, src.market_intelligence.middles.spread_middle, src.market_intelligence.middles.team_total_middle, src.market_intelligence.middles.total_middle`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/middles/alt_line_middle.py`

- imports_from: `src.market_intelligence.middle_opportunity_detector`
- imported_by: `src/market_intelligence/middles/__init__.py`
- runtime_callers: `src/market_intelligence/middles/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/middles/key_number_middle.py`

- imports_from: `src.market_intelligence.middle_opportunity_detector`
- imported_by: `src/market_intelligence/middles/__init__.py`
- runtime_callers: `src/market_intelligence/middles/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/middles/middle_ev_simulator.py`

- imports_from: `src.core.opportunity_scanner`
- imported_by: `src/market_intelligence/middles/__init__.py`
- runtime_callers: `src/market_intelligence/middles/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/middles/prop_middle.py`

- imports_from: `src.market_intelligence.middle_opportunity_detector`
- imported_by: `src/market_intelligence/middles/__init__.py`
- runtime_callers: `src/market_intelligence/middles/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/middles/push_corridor_middle.py`

- imports_from: `src.market_intelligence.middle_opportunity_detector`
- imported_by: `src/market_intelligence/middles/__init__.py`
- runtime_callers: `src/market_intelligence/middles/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/middles/spread_middle.py`

- imports_from: `src.market_intelligence.middle_opportunity_detector`
- imported_by: `src/market_intelligence/middles/__init__.py`
- runtime_callers: `src/market_intelligence/middles/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/middles/team_total_middle.py`

- imports_from: `src.market_intelligence.middle_opportunity_detector`
- imported_by: `src/market_intelligence/middles/__init__.py`
- runtime_callers: `src/market_intelligence/middles/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/middles/total_middle.py`

- imports_from: `src.market_intelligence.middle_opportunity_detector`
- imported_by: `src/market_intelligence/middles/__init__.py`
- runtime_callers: `src/market_intelligence/middles/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/model_input_coverage.py`

- imports_from: `src.data`
- imported_by: `src/services/automation_scheduler_facade.py, tests/test_model_input_coverage.py`
- runtime_callers: `src/services/automation_scheduler_facade.py`
- test_callers: `tests/test_model_input_coverage.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/multi_sport_model_registry.py`

- imports_from: `src.core.quant_engine`
- imported_by: `main.py, src/providers/ncaaf_collegefootballdata_adapter.py, src/services/model_recheck_runner.py, src/services/screenshot_intake.py, tests/test_afl_model_activation.py, tests/test_badminton_model_activation.py, tests/test_call_of_duty_esports_model_activation.py, tests/test_cs2_esports_model_activation.py, tests/test_darts_model_activation.py, tests/test_dota2_esports_model_activation.py, tests/test_formula_e_model_activation.py, tests/test_handball_model_activation.py, tests/test_indycar_model_activation.py, tests/test_lacrosse_model_activation.py, tests/test_league_of_legends_esports_model_activation.py, tests/test_live_smoke_payload_contract.py, tests/test_model_recheck_runner.py, tests/test_motogp_model_activation.py, tests/test_multi_sport_model_registry.py, tests/test_overwatch_esports_model_activation.py, tests/test_pickleball_model_activation.py, tests/test_rugby_model_activation.py, tests/test_screenshot_normalization_parity.py, tests/test_snooker_model_activation.py, tests/test_sport_analysis_endpoint.py, tests/test_sport_model_routing.py, tests/test_table_tennis_model_activation.py, tests/test_valorant_esports_model_activation.py, tests/test_volleyball_model_activation.py, tests/test_water_polo_model_activation.py`
- runtime_callers: `src/providers/ncaaf_collegefootballdata_adapter.py, src/services/model_recheck_runner.py, src/services/screenshot_intake.py`
- test_callers: `tests/test_afl_model_activation.py, tests/test_badminton_model_activation.py, tests/test_call_of_duty_esports_model_activation.py, tests/test_cs2_esports_model_activation.py, tests/test_darts_model_activation.py, tests/test_dota2_esports_model_activation.py, tests/test_formula_e_model_activation.py, tests/test_handball_model_activation.py, tests/test_indycar_model_activation.py, tests/test_lacrosse_model_activation.py, tests/test_league_of_legends_esports_model_activation.py, tests/test_live_smoke_payload_contract.py, tests/test_model_recheck_runner.py, tests/test_motogp_model_activation.py, tests/test_multi_sport_model_registry.py, tests/test_overwatch_esports_model_activation.py, tests/test_pickleball_model_activation.py, tests/test_rugby_model_activation.py, tests/test_screenshot_normalization_parity.py, tests/test_snooker_model_activation.py, tests/test_sport_analysis_endpoint.py, tests/test_sport_model_routing.py, tests/test_table_tennis_model_activation.py, tests/test_valorant_esports_model_activation.py, tests/test_volleyball_model_activation.py, tests/test_water_polo_model_activation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/news_event_monitor.py`

- imports_from: `none`
- imported_by: `tests/test_news_event_monitor.py`
- runtime_callers: `none`
- test_callers: `tests/test_news_event_monitor.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/nfl_coaching_feature_builders.py`

- imports_from: `src.data, src.data.data_paths, src.market_intelligence, src.market_intelligence.nfl_coaching_sources, src.providers.nfl_coaching_adapters, src.services.scheduler_config`
- imported_by: `src/analytics/derived_feature_backfill_report.py, tests/test_nfl_coaching_feature_builders.py`
- runtime_callers: `src/analytics/derived_feature_backfill_report.py`
- test_callers: `tests/test_nfl_coaching_feature_builders.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/nfl_coaching_sources.py`

- imports_from: `src.data, src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/market_intelligence/nfl_coaching_feature_builders.py, src/providers/nfl_coaching_adapters.py, src/services/streamlit_dashboard_facade.py`
- runtime_callers: `src/market_intelligence/nfl_coaching_feature_builders.py, src/providers/nfl_coaching_adapters.py, src/services/streamlit_dashboard_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/streamlit_dashboard_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/nfl_cutoff_week_features.py`

- imports_from: `src.data, src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/analytics/derived_feature_backfill_report.py, tests/test_nfl_cutoff_week_features.py`
- runtime_callers: `src/analytics/derived_feature_backfill_report.py`
- test_callers: `tests/test_nfl_cutoff_week_features.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/no_trade.py`

- imports_from: `src.market_intelligence._shared, src.market_intelligence.risk`
- imported_by: `src/market_intelligence/__init__.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- runtime_callers: `src/market_intelligence/__init__.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/opportunity_scoring.py`

- imports_from: `none`
- imported_by: `src/analytics/review_queue.py, src/services/alert_engine.py, src/services/scheduler_runner.py`
- runtime_callers: `src/analytics/review_queue.py, src/services/alert_engine.py, src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/options.py`

- imports_from: `src.market_intelligence._shared, src.market_intelligence.report`
- imported_by: `src/market_intelligence/__init__.py, tests/test_phase10k8zl5_options_0dte_gex_vanna_foundation.py`
- runtime_callers: `src/market_intelligence/__init__.py`
- test_callers: `tests/test_phase10k8zl5_options_0dte_gex_vanna_foundation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/player_prop_monitor.py`

- imports_from: `none`
- imported_by: `tests/test_player_prop_monitor.py`
- runtime_callers: `none`
- test_callers: `tests/test_player_prop_monitor.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/positioning.py`

- imports_from: `src.market_intelligence._shared`
- imported_by: `src/market_intelligence/__init__.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- runtime_callers: `src/market_intelligence/__init__.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/prediction_market_manifold_mapper.py`

- imports_from: `src.market_intelligence.manifold`
- imported_by: `src/market_intelligence/cross_asset_manifold_router.py`
- runtime_callers: `src/market_intelligence/cross_asset_manifold_router.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/prediction_market_outcome_candidates.py`

- imports_from: `src.analytics.review_queue, src.brokerage.paper_decision_ledger, src.data.data_paths, src.providers.kalshi_readonly_readiness, src.services.prediction_market_runtime_bridge, src.services.scheduler_config, src.services.settlement_service`
- imported_by: `src/ai/deepseek_data_pull_check.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- runtime_callers: `src/ai/deepseek_data_pull_check.py`
- test_callers: `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/prediction_markets.py`

- imports_from: `src.market_intelligence._shared, src.market_intelligence.confidence, src.market_intelligence.flow, src.market_intelligence.liquidity, src.market_intelligence.no_trade, src.market_intelligence.positioning, src.market_intelligence.report, src.market_intelligence.risk, src.market_intelligence.targets`
- imported_by: `src/market_intelligence/__init__.py, src/market_intelligence/manifold.py, tests/test_phase10k8zl4_prediction_market_intelligence_absorption.py`
- runtime_callers: `src/market_intelligence/__init__.py, src/market_intelligence/manifold.py`
- test_callers: `tests/test_phase10k8zl4_prediction_market_intelligence_absorption.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/regime.py`

- imports_from: `src.market_intelligence._shared`
- imported_by: `src/market_intelligence/__init__.py`
- runtime_callers: `src/market_intelligence/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/report.py`

- imports_from: `src.market_intelligence._shared, src.market_intelligence.contracts`
- imported_by: `src/market_intelligence/__init__.py, src/market_intelligence/crypto.py, src/market_intelligence/futures.py, src/market_intelligence/impact.py, src/market_intelligence/manifold.py, src/market_intelligence/options.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- runtime_callers: `src/market_intelligence/__init__.py, src/market_intelligence/crypto.py, src/market_intelligence/futures.py, src/market_intelligence/impact.py, src/market_intelligence/manifold.py, src/market_intelligence/options.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/response_compactor.py`

- imports_from: `src.security.secret_safety`
- imported_by: `tests/test_baseball_impact_intelligence.py, tests/test_basketball_player_impact.py, tests/test_combat_impact_intelligence.py, tests/test_data_intelligence_stack.py, tests/test_extreme_randomness_diagnostics.py, tests/test_football_impact_intelligence.py, tests/test_golf_impact_intelligence.py, tests/test_hockey_impact_intelligence.py, tests/test_kalshi_provider_shape_contract.py, tests/test_market_state_manifold.py, tests/test_pattern_calibration.py, tests/test_sharp_cross_book_review_queue.py, tests/test_soccer_impact_intelligence.py, tests/test_tennis_impact_intelligence.py`
- runtime_callers: `none`
- test_callers: `tests/test_baseball_impact_intelligence.py, tests/test_basketball_player_impact.py, tests/test_combat_impact_intelligence.py, tests/test_data_intelligence_stack.py, tests/test_extreme_randomness_diagnostics.py, tests/test_football_impact_intelligence.py, tests/test_golf_impact_intelligence.py, tests/test_hockey_impact_intelligence.py, tests/test_kalshi_provider_shape_contract.py, tests/test_market_state_manifold.py, tests/test_pattern_calibration.py, tests/test_sharp_cross_book_review_queue.py, tests/test_soccer_impact_intelligence.py, tests/test_tennis_impact_intelligence.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/risk.py`

- imports_from: `src.market_intelligence._shared`
- imported_by: `src/market_intelligence/__init__.py, src/market_intelligence/impact.py, src/market_intelligence/no_trade.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- runtime_callers: `src/market_intelligence/__init__.py, src/market_intelligence/impact.py, src/market_intelligence/no_trade.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/scoring.py`

- imports_from: `src.market_intelligence._shared`
- imported_by: `src/market_intelligence/__init__.py`
- runtime_callers: `src/market_intelligence/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_data_availability.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py, src/market_intelligence/soccer_impact_readiness.py`
- runtime_callers: `src/analytics/soccer_impact_report.py, src/market_intelligence/soccer_impact_readiness.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_goalkeeper_context.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_impact_common.py`

- imports_from: `src.security.policy, src.security.secret_safety`
- imported_by: `src/analytics/soccer_impact_calibration.py, src/analytics/soccer_impact_red_team.py, src/analytics/soccer_impact_report.py, src/market_intelligence/soccer_data_availability.py, src/market_intelligence/soccer_goalkeeper_context.py, src/market_intelligence/soccer_impact_readiness.py, src/market_intelligence/soccer_incentive_context.py, src/market_intelligence/soccer_lineup_availability_context.py, src/market_intelligence/soccer_market_relevance.py, src/market_intelligence/soccer_matchup_context.py, src/market_intelligence/soccer_player_role_impact.py, src/market_intelligence/soccer_possession_value_impact.py, src/market_intelligence/soccer_pressing_transition_context.py, src/market_intelligence/soccer_referee_context.py, src/market_intelligence/soccer_set_piece_context.py, src/market_intelligence/soccer_tactical_context.py`
- runtime_callers: `src/analytics/soccer_impact_calibration.py, src/analytics/soccer_impact_red_team.py, src/analytics/soccer_impact_report.py, src/market_intelligence/soccer_data_availability.py, src/market_intelligence/soccer_goalkeeper_context.py, src/market_intelligence/soccer_impact_readiness.py, src/market_intelligence/soccer_incentive_context.py, src/market_intelligence/soccer_lineup_availability_context.py, src/market_intelligence/soccer_market_relevance.py, src/market_intelligence/soccer_matchup_context.py, src/market_intelligence/soccer_player_role_impact.py, src/market_intelligence/soccer_possession_value_impact.py, src/market_intelligence/soccer_pressing_transition_context.py, src/market_intelligence/soccer_referee_context.py, src/market_intelligence/soccer_set_piece_context.py, src/market_intelligence/soccer_tactical_context.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_impact_readiness.py`

- imports_from: `src.market_intelligence.soccer_data_availability, src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_incentive_context.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_lineup_availability_context.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_market_relevance.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_matchup_context.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_player_role_impact.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_possession_value_impact.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_pressing_transition_context.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_referee_context.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_set_piece_context.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/soccer_tactical_context.py`

- imports_from: `src.market_intelligence.soccer_impact_common`
- imported_by: `src/analytics/soccer_impact_report.py`
- runtime_callers: `src/analytics/soccer_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/sport_feature_packs.py`

- imports_from: `none`
- imported_by: `src/market_intelligence/feature_packs.py`
- runtime_callers: `src/market_intelligence/feature_packs.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/sports.py`

- imports_from: `src.market_intelligence._shared, src.market_intelligence.confidence, src.market_intelligence.flow, src.market_intelligence.liquidity, src.market_intelligence.no_trade, src.market_intelligence.positioning, src.market_intelligence.report, src.market_intelligence.risk, src.market_intelligence.targets`
- imported_by: `src/market_intelligence/__init__.py, src/market_intelligence/feature_packs.py, src/market_intelligence/manifold.py, tests/test_baseball_impact_intelligence.py, tests/test_combat_impact_intelligence.py, tests/test_golf_impact_intelligence.py, tests/test_hockey_impact_intelligence.py, tests/test_phase10k8zl3_sports_intelligence_absorption.py, tests/test_soccer_impact_intelligence.py, tests/test_tennis_impact_intelligence.py`
- runtime_callers: `src/market_intelligence/__init__.py, src/market_intelligence/feature_packs.py, src/market_intelligence/manifold.py`
- test_callers: `tests/test_baseball_impact_intelligence.py, tests/test_combat_impact_intelligence.py, tests/test_golf_impact_intelligence.py, tests/test_hockey_impact_intelligence.py, tests/test_phase10k8zl3_sports_intelligence_absorption.py, tests/test_soccer_impact_intelligence.py, tests/test_tennis_impact_intelligence.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tail_event_classifier.py`

- imports_from: `src.security.policy`
- imported_by: `src/research/extreme_randomness_diagnostics.py`
- runtime_callers: `src/research/extreme_randomness_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/targets.py`

- imports_from: `src.market_intelligence._shared`
- imported_by: `src/market_intelligence/__init__.py, src/market_intelligence/crypto.py, src/market_intelligence/futures.py, src/market_intelligence/impact.py, src/market_intelligence/manifold.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- runtime_callers: `src/market_intelligence/__init__.py, src/market_intelligence/crypto.py, src/market_intelligence/futures.py, src/market_intelligence/impact.py, src/market_intelligence/manifold.py, src/market_intelligence/prediction_markets.py, src/market_intelligence/sports.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/technical_signal_fields.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tennis_availability_context.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tennis_data_availability.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tennis_format_markov_context.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tennis_impact_common.py`

- imports_from: `src.security.policy, src.security.secret_safety`
- imported_by: `src/analytics/tennis_impact_calibration.py, src/analytics/tennis_impact_red_team.py, src/analytics/tennis_impact_report.py, src/market_intelligence/tennis_availability_context.py, src/market_intelligence/tennis_data_availability.py, src/market_intelligence/tennis_format_markov_context.py, src/market_intelligence/tennis_impact_readiness.py, src/market_intelligence/tennis_incentive_context.py, src/market_intelligence/tennis_market_relevance.py, src/market_intelligence/tennis_matchup_context.py, src/market_intelligence/tennis_pressure_tiebreak_context.py, src/market_intelligence/tennis_return_impact.py, src/market_intelligence/tennis_serve_impact.py, src/market_intelligence/tennis_surface_context.py`
- runtime_callers: `src/analytics/tennis_impact_calibration.py, src/analytics/tennis_impact_red_team.py, src/analytics/tennis_impact_report.py, src/market_intelligence/tennis_availability_context.py, src/market_intelligence/tennis_data_availability.py, src/market_intelligence/tennis_format_markov_context.py, src/market_intelligence/tennis_impact_readiness.py, src/market_intelligence/tennis_incentive_context.py, src/market_intelligence/tennis_market_relevance.py, src/market_intelligence/tennis_matchup_context.py, src/market_intelligence/tennis_pressure_tiebreak_context.py, src/market_intelligence/tennis_return_impact.py, src/market_intelligence/tennis_serve_impact.py, src/market_intelligence/tennis_surface_context.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tennis_impact_readiness.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tennis_incentive_context.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tennis_market_relevance.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tennis_matchup_context.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tennis_pressure_tiebreak_context.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tennis_return_impact.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tennis_serve_impact.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/market_intelligence/tennis_surface_context.py`

- imports_from: `src.market_intelligence.tennis_impact_common`
- imported_by: `src/analytics/tennis_impact_report.py`
- runtime_callers: `src/analytics/tennis_impact_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/__init__.py`

- imports_from: `src.providers.aliases, src.providers.base, src.providers.categories, src.providers.compat, src.providers.contracts, src.providers.errors, src.providers.health, src.providers.normalization, src.providers.policy, src.providers.prediction_markets, src.providers.registry, src.providers.routing, src.providers.sportsbooks, src.providers.validation, src.providers.zero_dte_stocks`
- imported_by: `src/services/action_betting_service.py`
- runtime_callers: `src/services/action_betting_service.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/adapters/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/aliases.py`

- imports_from: `none`
- imported_by: `src/providers/__init__.py`
- runtime_callers: `src/providers/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/base.py`

- imports_from: `src.providers.contracts, src.providers.errors, src.providers.health, src.providers.normalization, src.providers.validation`
- imported_by: `src/providers/__init__.py, src/providers/prediction_markets/adapters.py, src/providers/sportsbooks/adapters.py, src/providers/zero_dte_stocks/provider.py, src/services/scheduler_runner.py, tests/test_phase10k8zft_provider_foundation_transport.py, tests/test_provider_adapter_base.py`
- runtime_callers: `src/providers/__init__.py, src/providers/prediction_markets/adapters.py, src/providers/sportsbooks/adapters.py, src/providers/zero_dte_stocks/provider.py, src/services/scheduler_runner.py`
- test_callers: `tests/test_phase10k8zft_provider_foundation_transport.py, tests/test_provider_adapter_base.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/categories.py`

- imports_from: `none`
- imported_by: `src/providers/__init__.py, src/providers/routing.py`
- runtime_callers: `src/providers/__init__.py, src/providers/routing.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/compat.py`

- imports_from: `none`
- imported_by: `main.py, src/api/market_metadata_routes.py, src/providers/__init__.py, src/providers/provider_router.py`
- runtime_callers: `src/api/market_metadata_routes.py, src/providers/__init__.py, src/providers/provider_router.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `src/api/market_metadata_routes.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/contracts.py`

- imports_from: `none`
- imported_by: `src/providers/__init__.py, src/providers/base.py, src/providers/health.py, src/providers/prediction_markets/adapters.py, src/providers/prediction_markets/contracts.py, src/providers/registry.py, src/providers/sportsbooks/adapters.py, src/providers/sportsbooks/contracts.py, src/providers/validation.py, src/providers/zero_dte_stocks/contracts.py, src/providers/zero_dte_stocks/provider.py, tests/test_phase10k8zfo_src_providers_skeleton.py, tests/test_phase10k8zft_provider_foundation_transport.py, tests/test_provider_adapter_base.py, tests/test_provider_contracts.py, tests/test_provider_health.py`
- runtime_callers: `src/providers/__init__.py, src/providers/base.py, src/providers/health.py, src/providers/prediction_markets/adapters.py, src/providers/prediction_markets/contracts.py, src/providers/registry.py, src/providers/sportsbooks/adapters.py, src/providers/sportsbooks/contracts.py, src/providers/validation.py, src/providers/zero_dte_stocks/contracts.py, src/providers/zero_dte_stocks/provider.py`
- test_callers: `tests/test_phase10k8zfo_src_providers_skeleton.py, tests/test_phase10k8zft_provider_foundation_transport.py, tests/test_provider_adapter_base.py, tests/test_provider_contracts.py, tests/test_provider_health.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/errors.py`

- imports_from: `none`
- imported_by: `src/providers/__init__.py, src/providers/base.py, src/providers/registry.py, src/providers/zero_dte_stocks/provider.py, tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py`
- runtime_callers: `src/providers/__init__.py, src/providers/base.py, src/providers/registry.py, src/providers/zero_dte_stocks/provider.py`
- test_callers: `tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/health.py`

- imports_from: `src.providers.contracts`
- imported_by: `src/ai/deepseek_profit_lab.py, src/providers/__init__.py, src/providers/base.py, src/providers/prediction_markets/adapters.py, src/providers/sportsbooks/adapters.py, src/providers/zero_dte_stocks/provider.py, src/services/automation_scheduler_facade.py, src/services/scheduler_runner.py, tests/test_phase10k8zfo_src_providers_skeleton.py, tests/test_provider_health.py`
- runtime_callers: `src/ai/deepseek_profit_lab.py, src/providers/__init__.py, src/providers/base.py, src/providers/prediction_markets/adapters.py, src/providers/sportsbooks/adapters.py, src/providers/zero_dte_stocks/provider.py, src/services/automation_scheduler_facade.py, src/services/scheduler_runner.py`
- test_callers: `tests/test_phase10k8zfo_src_providers_skeleton.py, tests/test_provider_health.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/injury_weather_adapter_contract.py`

- imports_from: `src.providers.validation, src.services.scheduler_config`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/institutional_cross_asset_adapters.py`

- imports_from: `src.analytics.review_queue, src.brokerage.paper_decision_ledger, src.data.data_paths, src.market_intelligence.institutional_cross_asset_scores, src.services.outcome_store, src.services.scheduler_config`
- imported_by: `src/ai/institutional_deepseek_review.py, src/analytics/institutional_cross_asset_reports.py, src/market_intelligence/institutional_cross_asset_lab.py, src/services/runtime_shared.py`
- runtime_callers: `src/ai/institutional_deepseek_review.py, src/analytics/institutional_cross_asset_reports.py, src/market_intelligence/institutional_cross_asset_lab.py, src/services/runtime_shared.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/kalshi_adapter_contract.py`

- imports_from: `src.providers.prediction_markets`
- imported_by: `tests/test_phase10k8zft_provider_foundation_transport.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zft_provider_foundation_transport.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/kalshi_monitor.py`

- imports_from: `none`
- imported_by: `src/services/scheduler_runner.py`
- runtime_callers: `src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/kalshi_readonly_readiness.py`

- imports_from: `src.providers.registry, src.services.prediction_market_runtime_bridge`
- imported_by: `src/ai/deepseek_data_pull_check.py, src/market_intelligence/prediction_market_outcome_candidates.py, tests/test_phase10k8zga_provider_registry_runtime_blocker.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- runtime_callers: `src/ai/deepseek_data_pull_check.py, src/market_intelligence/prediction_market_outcome_candidates.py`
- test_callers: `tests/test_phase10k8zga_provider_registry_runtime_blocker.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/kalshi_scoring.py`

- imports_from: `none`
- imported_by: `src/core/market_structure.py, src/services/scheduler_runner.py`
- runtime_callers: `src/core/market_structure.py, src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/ncaaf_collegefootballdata_adapter.py`

- imports_from: `src.data, src.data.data_paths, src.market_intelligence.multi_sport_model_registry`
- imported_by: `src/services/automation_scheduler_facade.py`
- runtime_callers: `src/services/automation_scheduler_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/news_events_adapter_contract.py`

- imports_from: `src.providers.validation, src.services.scheduler_config`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/nfl_coaching_adapters.py`

- imports_from: `src.data, src.data.data_paths, src.market_intelligence.nfl_coaching_sources, src.services.scheduler_config`
- imported_by: `src/market_intelligence/nfl_coaching_feature_builders.py, src/services/streamlit_dashboard_facade.py, tests/test_nfl_coaching_adapters.py, tests/test_nfl_coaching_feature_builders.py`
- runtime_callers: `src/market_intelligence/nfl_coaching_feature_builders.py, src/services/streamlit_dashboard_facade.py`
- test_callers: `tests/test_nfl_coaching_adapters.py, tests/test_nfl_coaching_feature_builders.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/streamlit_dashboard_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/nfl_open_data_adapters.py`

- imports_from: `src.data, src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/providers/nfl_open_data_backfill.py, src/services/streamlit_dashboard_facade.py, tests/test_nfl_open_data_adapters.py, tests/test_nfl_open_data_backfill.py`
- runtime_callers: `src/providers/nfl_open_data_backfill.py, src/services/streamlit_dashboard_facade.py`
- test_callers: `tests/test_nfl_open_data_adapters.py, tests/test_nfl_open_data_backfill.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/streamlit_dashboard_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/nfl_open_data_backfill.py`

- imports_from: `src.data, src.data.data_paths, src.providers.nfl_open_data_adapters, src.services.scheduler_config`
- imported_by: `tests/test_nfl_open_data_backfill.py`
- runtime_callers: `none`
- test_callers: `tests/test_nfl_open_data_backfill.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/nfl_open_data_feature_builders.py`

- imports_from: `src.data, src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/analytics/derived_feature_backfill_report.py, src/providers/nfl_open_data_feature_readiness.py`
- runtime_callers: `src/analytics/derived_feature_backfill_report.py, src/providers/nfl_open_data_feature_readiness.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/nfl_open_data_feature_readiness.py`

- imports_from: `src.data, src.data.data_paths, src.providers.nfl_open_data_feature_builders, src.services.scheduler_config`
- imported_by: `tests/test_nfl_open_data_feature_builders.py`
- runtime_callers: `none`
- test_callers: `tests/test_nfl_open_data_feature_builders.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/normalization.py`

- imports_from: `none`
- imported_by: `src/providers/__init__.py, src/providers/base.py, src/providers/prediction_markets/contracts.py, src/providers/sportsbooks/contracts.py, src/providers/zero_dte_stocks/contracts.py, tests/test_phase10k8zfo_src_providers_skeleton.py, tests/test_phase10k8zft_provider_foundation_transport.py, tests/test_provider_normalization_contract.py`
- runtime_callers: `src/providers/__init__.py, src/providers/base.py, src/providers/prediction_markets/contracts.py, src/providers/sportsbooks/contracts.py, src/providers/zero_dte_stocks/contracts.py`
- test_callers: `tests/test_phase10k8zfo_src_providers_skeleton.py, tests/test_phase10k8zft_provider_foundation_transport.py, tests/test_provider_normalization_contract.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/player_props_adapter_contract.py`

- imports_from: `src.providers.validation, src.services.scheduler_config`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/policy/__init__.py`

- imports_from: `src.providers.policy.allowlist, src.providers.policy.secret_policy, src.providers.policy.write_firewall`
- imported_by: `src/providers/__init__.py, tests/test_phase10k8zt_provider_security_surface_retirement.py`
- runtime_callers: `src/providers/__init__.py`
- test_callers: `tests/test_phase10k8zt_provider_security_surface_retirement.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/policy/allowlist.py`

- imports_from: `none`
- imported_by: `src/analytics/advanced_red_team_provider_policy.py, src/brokerage/readiness_support.py, src/providers/policy/__init__.py, src/providers/policy/write_firewall.py, src/security/ai_provider_security.py, src/security/hard_gate_policy.py, src/services/runtime_shared.py, tests/test_phase10k8zft_provider_foundation_transport.py, tests/test_phase10k8zt_provider_security_surface_retirement.py`
- runtime_callers: `src/analytics/advanced_red_team_provider_policy.py, src/brokerage/readiness_support.py, src/providers/policy/__init__.py, src/providers/policy/write_firewall.py, src/security/ai_provider_security.py, src/security/hard_gate_policy.py, src/services/runtime_shared.py`
- test_callers: `tests/test_phase10k8zft_provider_foundation_transport.py, tests/test_phase10k8zt_provider_security_surface_retirement.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/policy/secret_policy.py`

- imports_from: `none`
- imported_by: `src/providers/policy/__init__.py, src/providers/policy/write_firewall.py, src/providers/registry.py, src/services/odds_runtime_bridge.py, src/services/prediction_market_runtime_bridge.py, tests/test_provider_secret_policy.py`
- runtime_callers: `src/providers/policy/__init__.py, src/providers/policy/write_firewall.py, src/providers/registry.py, src/services/odds_runtime_bridge.py, src/services/prediction_market_runtime_bridge.py`
- test_callers: `tests/test_provider_secret_policy.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/policy/write_firewall.py`

- imports_from: `src.providers.policy.allowlist, src.providers.policy.secret_policy`
- imported_by: `src/brokerage/readiness.py, src/providers/policy/__init__.py, tests/test_phase10k8zgb_provider_write_firewall_runtime_blocker.py, tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py, tests/test_phase10k8zgd_final_provider_foundation_blocker_deletion.py, tests/test_security_framework.py`
- runtime_callers: `src/brokerage/readiness.py, src/providers/policy/__init__.py`
- test_callers: `tests/test_phase10k8zgb_provider_write_firewall_runtime_blocker.py, tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py, tests/test_phase10k8zgd_final_provider_foundation_blocker_deletion.py, tests/test_security_framework.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/prediction_markets/__init__.py`

- imports_from: `src.providers.prediction_markets.adapters, src.providers.prediction_markets.contracts`
- imported_by: `src/providers/__init__.py, src/providers/kalshi_adapter_contract.py, src/providers/provider_router.py, tests/test_kalshi_market_provider.py, tests/test_kalshi_readonly_adapter.py, tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py, tests/test_phase10k8zgy_prediction_market_shell_deletion.py, tests/test_screenshot_analysis.py`
- runtime_callers: `src/providers/__init__.py, src/providers/kalshi_adapter_contract.py, src/providers/provider_router.py`
- test_callers: `tests/test_kalshi_market_provider.py, tests/test_kalshi_readonly_adapter.py, tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py, tests/test_phase10k8zgy_prediction_market_shell_deletion.py, tests/test_screenshot_analysis.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/prediction_markets/adapters.py`

- imports_from: `src.providers.base, src.providers.contracts, src.providers.health, src.providers.prediction_markets.contracts, src.providers.prediction_markets.models, src.providers.validation`
- imported_by: `src/providers/prediction_markets/__init__.py, src/services/prediction_market_runtime_bridge.py`
- runtime_callers: `src/providers/prediction_markets/__init__.py, src/services/prediction_market_runtime_bridge.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/prediction_markets/contracts.py`

- imports_from: `src.providers.contracts, src.providers.normalization, src.providers.validation`
- imported_by: `src/providers/prediction_markets/__init__.py, src/providers/prediction_markets/adapters.py`
- runtime_callers: `src/providers/prediction_markets/__init__.py, src/providers/prediction_markets/adapters.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/prediction_markets/models.py`

- imports_from: `none`
- imported_by: `src/providers/prediction_markets/adapters.py`
- runtime_callers: `src/providers/prediction_markets/adapters.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/provider_router.py`

- imports_from: `src.connectors.odds_data, src.providers.compat, src.providers.prediction_markets, src.providers.routing, src.providers.sportsbooks`
- imported_by: `main.py, src/api/model_card_service.py, tests/test_phase10k8zg4_runtime_bridge_import_redirection.py, tests/test_phase10k8zg5_provider_router_independence.py, tests/test_phase10k8zg6_legacy_provider_router_delete_proof.py, tests/test_phase10k8zg7_legacy_provider_router_deletion.py`
- runtime_callers: `src/api/model_card_service.py`
- test_callers: `tests/test_phase10k8zg4_runtime_bridge_import_redirection.py, tests/test_phase10k8zg5_provider_router_independence.py, tests/test_phase10k8zg6_legacy_provider_router_delete_proof.py, tests/test_phase10k8zg7_legacy_provider_router_deletion.py`
- script_callers: `none`
- api_callers: `src/api/model_card_service.py`
- facade_callers: `tests/test_phase10k8zg6_legacy_provider_router_delete_proof.py, tests/test_phase10k8zg7_legacy_provider_router_deletion.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/registry.py`

- imports_from: `src.providers.contracts, src.providers.errors, src.providers.policy.secret_policy`
- imported_by: `src/providers/__init__.py, src/providers/kalshi_readonly_readiness.py, src/services/automation_scheduler_facade.py, src/services/cadence_controller.py, src/services/prediction_market_runtime_bridge.py, src/services/scheduler_config.py, tests/test_kalshi_market_provider.py, tests/test_phase10k8zfo_src_providers_skeleton.py, tests/test_phase10k8zft_provider_foundation_transport.py, tests/test_phase10k8zga_provider_registry_runtime_blocker.py, tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py, tests/test_phase10k8zgd_final_provider_foundation_blocker_deletion.py, tests/test_provider_registry.py, tests/test_sportsbook_odds_provider.py`
- runtime_callers: `src/providers/__init__.py, src/providers/kalshi_readonly_readiness.py, src/services/automation_scheduler_facade.py, src/services/cadence_controller.py, src/services/prediction_market_runtime_bridge.py, src/services/scheduler_config.py`
- test_callers: `tests/test_kalshi_market_provider.py, tests/test_phase10k8zfo_src_providers_skeleton.py, tests/test_phase10k8zft_provider_foundation_transport.py, tests/test_phase10k8zga_provider_registry_runtime_blocker.py, tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py, tests/test_phase10k8zgd_final_provider_foundation_blocker_deletion.py, tests/test_provider_registry.py, tests/test_sportsbook_odds_provider.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/routing.py`

- imports_from: `src.providers.categories`
- imported_by: `src/providers/__init__.py, src/providers/provider_router.py`
- runtime_callers: `src/providers/__init__.py, src/providers/provider_router.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/sportsbook_adapter_contract.py`

- imports_from: `src.providers.sportsbooks`
- imported_by: `tests/test_phase10k8zft_provider_foundation_transport.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zft_provider_foundation_transport.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/sportsbook_manifold_mapper.py`

- imports_from: `src.market_intelligence.market_state_manifold`
- imported_by: `src/market_intelligence/cross_asset_manifold_router.py`
- runtime_callers: `src/market_intelligence/cross_asset_manifold_router.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/sportsbooks/__init__.py`

- imports_from: `src.providers.sportsbooks.adapters, src.providers.sportsbooks.contracts`
- imported_by: `src/providers/__init__.py, src/providers/provider_router.py, src/providers/sportsbook_adapter_contract.py, tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_provider_normalization_contract.py`
- runtime_callers: `src/providers/__init__.py, src/providers/provider_router.py, src/providers/sportsbook_adapter_contract.py`
- test_callers: `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_provider_normalization_contract.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/sportsbooks/adapters.py`

- imports_from: `src.core.math_utils, src.providers.base, src.providers.contracts, src.providers.health, src.providers.sportsbooks.contracts, src.providers.sportsbooks.models, src.providers.validation`
- imported_by: `src/providers/sportsbooks/__init__.py, src/services/odds_runtime_bridge.py, tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgo_odds_compatibility_test_retirement.py, tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py, tests/test_sharp_sportsbook_adapter.py`
- runtime_callers: `src/providers/sportsbooks/__init__.py, src/services/odds_runtime_bridge.py`
- test_callers: `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgo_odds_compatibility_test_retirement.py, tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py, tests/test_sharp_sportsbook_adapter.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgo_odds_compatibility_test_retirement.py, tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/sportsbooks/contracts.py`

- imports_from: `src.providers.contracts, src.providers.normalization, src.providers.validation`
- imported_by: `src/providers/sportsbooks/__init__.py, src/providers/sportsbooks/adapters.py, src/services/odds_runtime_bridge.py, tests/test_sportsbook_odds_provider.py`
- runtime_callers: `src/providers/sportsbooks/__init__.py, src/providers/sportsbooks/adapters.py, src/services/odds_runtime_bridge.py`
- test_callers: `tests/test_sportsbook_odds_provider.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/sportsbooks/models.py`

- imports_from: `none`
- imported_by: `src/providers/sportsbooks/adapters.py`
- runtime_callers: `src/providers/sportsbooks/adapters.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/stock_fundamentals_adapter_contract.py`

- imports_from: `src.providers.validation, src.services.scheduler_config`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/stock_monitor.py`

- imports_from: `none`
- imported_by: `tests/test_stock_monitor.py`
- runtime_callers: `none`
- test_callers: `tests/test_stock_monitor.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/stock_price_adapter_contract.py`

- imports_from: `src.providers.validation, src.services.scheduler_config`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/validation.py`

- imports_from: `src.providers.contracts`
- imported_by: `src/providers/__init__.py, src/providers/base.py, src/providers/injury_weather_adapter_contract.py, src/providers/news_events_adapter_contract.py, src/providers/player_props_adapter_contract.py, src/providers/prediction_markets/adapters.py, src/providers/prediction_markets/contracts.py, src/providers/sportsbooks/adapters.py, src/providers/sportsbooks/contracts.py, src/providers/stock_fundamentals_adapter_contract.py, src/providers/stock_price_adapter_contract.py, src/providers/zero_dte_stocks/contracts.py, src/services/prediction_market_runtime_bridge.py, tests/test_phase10k8zft_provider_foundation_transport.py, tests/test_provider_payload_validator.py`
- runtime_callers: `src/providers/__init__.py, src/providers/base.py, src/providers/injury_weather_adapter_contract.py, src/providers/news_events_adapter_contract.py, src/providers/player_props_adapter_contract.py, src/providers/prediction_markets/adapters.py, src/providers/prediction_markets/contracts.py, src/providers/sportsbooks/adapters.py, src/providers/sportsbooks/contracts.py, src/providers/stock_fundamentals_adapter_contract.py, src/providers/stock_price_adapter_contract.py, src/providers/zero_dte_stocks/contracts.py, src/services/prediction_market_runtime_bridge.py`
- test_callers: `tests/test_phase10k8zft_provider_foundation_transport.py, tests/test_provider_payload_validator.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/zero_dte_stocks/__init__.py`

- imports_from: `src.providers.zero_dte_stocks.adapters, src.providers.zero_dte_stocks.contracts, src.providers.zero_dte_stocks.models, src.providers.zero_dte_stocks.normalization, src.providers.zero_dte_stocks.provider`
- imported_by: `src/providers/__init__.py, tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py`
- runtime_callers: `src/providers/__init__.py`
- test_callers: `tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/zero_dte_stocks/adapters.py`

- imports_from: `src.providers.zero_dte_stocks.provider`
- imported_by: `src/providers/zero_dte_stocks/__init__.py`
- runtime_callers: `src/providers/zero_dte_stocks/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/zero_dte_stocks/contracts.py`

- imports_from: `src.providers.contracts, src.providers.normalization, src.providers.validation`
- imported_by: `src/providers/zero_dte_stocks/__init__.py, src/providers/zero_dte_stocks/provider.py`
- runtime_callers: `src/providers/zero_dte_stocks/__init__.py, src/providers/zero_dte_stocks/provider.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/zero_dte_stocks/models.py`

- imports_from: `none`
- imported_by: `src/providers/zero_dte_stocks/__init__.py, src/providers/zero_dte_stocks/normalization.py, src/providers/zero_dte_stocks/provider.py`
- runtime_callers: `src/providers/zero_dte_stocks/__init__.py, src/providers/zero_dte_stocks/normalization.py, src/providers/zero_dte_stocks/provider.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/zero_dte_stocks/normalization.py`

- imports_from: `src.connectors.market_data.models, src.providers.zero_dte_stocks.models`
- imported_by: `src/providers/zero_dte_stocks/__init__.py, src/providers/zero_dte_stocks/provider.py`
- runtime_callers: `src/providers/zero_dte_stocks/__init__.py, src/providers/zero_dte_stocks/provider.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/providers/zero_dte_stocks/provider.py`

- imports_from: `src.connectors.market_data.models, src.providers.base, src.providers.contracts, src.providers.errors, src.providers.health, src.providers.zero_dte_stocks.contracts, src.providers.zero_dte_stocks.models, src.providers.zero_dte_stocks.normalization`
- imported_by: `src/providers/zero_dte_stocks/__init__.py, src/providers/zero_dte_stocks/adapters.py`
- runtime_callers: `src/providers/zero_dte_stocks/__init__.py, src/providers/zero_dte_stocks/adapters.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/__init__.py`

- imports_from: `src.research.ablation, src.research.contracts, src.research.experiments, src.research.lanes, src.research.maturity, src.research.storage`
- imported_by: `src/market_intelligence/cross_asset_intelligence_router.py, src/market_intelligence/data_intelligence_registry.py, tests/test_data_intelligence_stack.py, tests/test_phase10k5_core_arbitrage_engine.py, tests/test_phase10k8zho_research_foundation.py, tests/test_phase10k8zhp_legacy_analytics_research_owner_map.py, tests/test_phase10k8zhq_analytics_research_checkpoint.py, tests/test_phase10k8zhw_research_downstream_redirection.py, tests/test_phase10k8zhz_analytics_research_wrapper_delete_proof.py, tests/test_phase10k8zi1_analytics_research_compatibility_test_retirement.py, tests/test_phase10k8zi3_model_maturity_registry_decoupling.py, tests/test_phase10k8zi4_final_analytics_research_delete_readiness.py, tests/test_phase10k8zi5_analytics_research_wrapper_deletion.py`
- runtime_callers: `src/market_intelligence/cross_asset_intelligence_router.py, src/market_intelligence/data_intelligence_registry.py`
- test_callers: `tests/test_data_intelligence_stack.py, tests/test_phase10k5_core_arbitrage_engine.py, tests/test_phase10k8zho_research_foundation.py, tests/test_phase10k8zhp_legacy_analytics_research_owner_map.py, tests/test_phase10k8zhq_analytics_research_checkpoint.py, tests/test_phase10k8zhw_research_downstream_redirection.py, tests/test_phase10k8zhz_analytics_research_wrapper_delete_proof.py, tests/test_phase10k8zi1_analytics_research_compatibility_test_retirement.py, tests/test_phase10k8zi3_model_maturity_registry_decoupling.py, tests/test_phase10k8zi4_final_analytics_research_delete_readiness.py, tests/test_phase10k8zi5_analytics_research_wrapper_deletion.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zhp_legacy_analytics_research_owner_map.py, tests/test_phase10k8zhz_analytics_research_wrapper_delete_proof.py, tests/test_phase10k8zi1_analytics_research_compatibility_test_retirement.py, tests/test_phase10k8zi5_analytics_research_wrapper_deletion.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/ablation.py`

- imports_from: `src.research.contracts`
- imported_by: `src/research/__init__.py`
- runtime_callers: `src/research/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/calibration_strategy_filter.py`

- imports_from: `src.market_intelligence.feature_packs, src.research.feature_control`
- imported_by: `src/research/feature_control.py`
- runtime_callers: `src/research/feature_control.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/causal_discovery_research.py`

- imports_from: `src.security.policy`
- imported_by: `src/analytics/advanced_shape_diagnostics.py`
- runtime_callers: `src/analytics/advanced_shape_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/causal_scaffold.py`

- imports_from: `src.security.policy`
- imported_by: `src/market_intelligence/cross_asset_intelligence_router.py`
- runtime_callers: `src/market_intelligence/cross_asset_intelligence_router.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/contracts.py`

- imports_from: `none`
- imported_by: `src/research/__init__.py, src/research/ablation.py, src/research/experiments.py, src/research/lanes.py`
- runtime_callers: `src/research/__init__.py, src/research/ablation.py, src/research/experiments.py, src/research/lanes.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/contrastive_embedding_diagnostics.py`

- imports_from: `src.analytics.advanced_shape_diagnostics, src.security.policy`
- imported_by: `src/analytics/advanced_shape_diagnostics.py`
- runtime_callers: `src/analytics/advanced_shape_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/correlation_structure_diagnostics.py`

- imports_from: `src.core.random_matrix_risk, src.security.policy`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/derived_feature_planner.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/experiment_history_store.py`

- imports_from: `src.research.feature_control`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/experiment_report_exporter.py`

- imports_from: `src.research.history`
- imported_by: `src/research/history.py`
- runtime_callers: `src/research/history.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/experiments.py`

- imports_from: `src.research.contracts`
- imported_by: `src/research/__init__.py`
- runtime_callers: `src/research/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/extreme_randomness_diagnostics.py`

- imports_from: `src.analytics.random_baseline_comparison, src.core.random_matrix_risk, src.market_intelligence.tail_event_classifier, src.research.tracy_widom_research, src.security.policy`
- imported_by: `src/analytics/extreme_signal_red_team.py`
- runtime_callers: `src/analytics/extreme_signal_red_team.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/extreme_randomness_report.py`

- imports_from: `src.data.data_paths, src.research.universality_research_lanes, src.security.policy`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/feature_ablation_lab.py`

- imports_from: `src.market_intelligence.feature_packs`
- imported_by: `src/research/feature_control.py`
- runtime_callers: `src/research/feature_control.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/feature_control.py`

- imports_from: `src.data, src.data.historical_odds, src.market_intelligence.feature_packs, src.research.calibration_strategy_filter, src.research.feature_ablation_lab`
- imported_by: `src/research/calibration_strategy_filter.py, src/research/experiment_history_store.py, src/research/history.py, src/services/streamlit_dashboard_data.py, tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- runtime_callers: `src/research/calibration_strategy_filter.py, src/research/experiment_history_store.py, src/research/history.py, src/services/streamlit_dashboard_data.py`
- test_callers: `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/history.py`

- imports_from: `src.research.experiment_report_exporter, src.research.feature_control`
- imported_by: `src/research/experiment_report_exporter.py, src/services/streamlit_dashboard_data.py, tests/test_streamlit_dashboard_data.py`
- runtime_callers: `src/research/experiment_report_exporter.py, src/services/streamlit_dashboard_data.py`
- test_callers: `tests/test_streamlit_dashboard_data.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/lanes.py`

- imports_from: `src.research.contracts`
- imported_by: `src/research/__init__.py, src/research/maturity.py`
- runtime_callers: `src/research/__init__.py, src/research/maturity.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/maturity.py`

- imports_from: `src.research.lanes`
- imported_by: `src/brokerage/readiness.py, src/research/__init__.py`
- runtime_callers: `src/brokerage/readiness.py, src/research/__init__.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/pattern_calibration.py`

- imports_from: `src.analytics.micro_outcome_calibration, src.services.scheduler_config`
- imported_by: `src/services/automation_scheduler_facade.py, src/services/streamlit_dashboard_facade.py`
- runtime_callers: `src/services/automation_scheduler_facade.py, src/services/streamlit_dashboard_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py, src/services/streamlit_dashboard_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/representation_feature_builder.py`

- imports_from: `src.market_intelligence.manifold_feature_builder, src.security.policy`
- imported_by: `src/market_intelligence/cross_asset_embedding_router.py`
- runtime_callers: `src/market_intelligence/cross_asset_embedding_router.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/storage.py`

- imports_from: `none`
- imported_by: `src/research/__init__.py, tests/test_market_research_store.py, tests/test_phase10k2_sports_snapshot_pipeline.py, tests/test_phase10k3_runtime_csv_migration_plan.py, tests/test_phase10k4_0dte_options_schema_foundation.py, tests/test_phase10k5_core_arbitrage_engine.py, tests/test_phase10k8zhs_research_migration_batch_1.py, tests/test_phase10k8zi2_research_store_ownership_migration.py`
- runtime_callers: `src/research/__init__.py`
- test_callers: `tests/test_market_research_store.py, tests/test_phase10k2_sports_snapshot_pipeline.py, tests/test_phase10k3_runtime_csv_migration_plan.py, tests/test_phase10k4_0dte_options_schema_foundation.py, tests/test_phase10k5_core_arbitrage_engine.py, tests/test_phase10k8zhs_research_migration_batch_1.py, tests/test_phase10k8zi2_research_store_ownership_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/tracy_widom_research.py`

- imports_from: `src.security.policy`
- imported_by: `src/research/extreme_randomness_diagnostics.py`
- runtime_callers: `src/research/extreme_randomness_diagnostics.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/research/universality_research_lanes.py`

- imports_from: `src.security.policy`
- imported_by: `src/research/extreme_randomness_report.py`
- runtime_callers: `src/research/extreme_randomness_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/security/__init__.py`

- imports_from: `src.security.policy, src.security.secret_safety`
- imported_by: `tests/test_phase10k8zt_provider_security_surface_retirement.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zt_provider_security_surface_retirement.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/security/ai_provider_security.py`

- imports_from: `src.providers.policy.allowlist, src.security.policy, src.services.ledger_service`
- imported_by: `src/ai/deepseek_profit_lab.py, src/services/security_readiness.py`
- runtime_callers: `src/ai/deepseek_profit_lab.py, src/services/security_readiness.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/security/hard_gate_policy.py`

- imports_from: `src.data.data_paths, src.providers.policy.allowlist, src.security.owner_approval_gate, src.security.policy, src.security.risk_limit_guard, src.security.secret_safety`
- imported_by: `src/analytics/strategy_readiness_report.py`
- runtime_callers: `src/analytics/strategy_readiness_report.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/security/owner_approval_gate.py`

- imports_from: `src.data.data_paths, src.security.policy, src.services.ledger_service, src.services.scheduler_config`
- imported_by: `src/security/hard_gate_policy.py, src/services/runtime_shared.py, tests/test_phase10k8zt_provider_security_surface_retirement.py`
- runtime_callers: `src/security/hard_gate_policy.py, src/services/runtime_shared.py`
- test_callers: `tests/test_phase10k8zt_provider_security_surface_retirement.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/security/policy.py`

- imports_from: `none`
- imported_by: `src/ai/deepseek_response_validator.py, src/analytics/advanced_red_team_provider_policy.py, src/analytics/advanced_red_team_report.py, src/analytics/advanced_shape_diagnostics.py, src/analytics/bayesian_structural_baseline.py, src/analytics/dynamical_systems_diagnostics.py, src/analytics/extreme_signal_red_team.py, src/analytics/information_theory_diagnostics.py, src/analytics/intelligence_readiness_report.py, src/analytics/random_baseline_comparison.py, src/analytics/strategy_readiness_report.py, src/analytics/topological_red_team.py, src/core/conformal_uncertainty.py, src/core/random_matrix_risk.py, src/core/strategy_context_buckets.py, src/core/strategy_disagreement.py, src/core/strategy_maturity.py, src/core/strategy_promotion.py, src/core/strategy_registry.py, src/core/strategy_router.py, src/core/strategy_score_aggregator.py, src/market_intelligence/baseball_impact_common.py, src/market_intelligence/basketball_player_impact.py, src/market_intelligence/basketball_player_impact_common.py, src/market_intelligence/combat_impact_common.py, src/market_intelligence/cross_asset_embedding_router.py, src/market_intelligence/cross_asset_intelligence_router.py, src/market_intelligence/data_intelligence_registry.py, src/market_intelligence/football_impact_schema.py, src/market_intelligence/golf_impact_common.py, src/market_intelligence/graph_relationship_mapper.py, src/market_intelligence/hockey_impact_common.py, src/market_intelligence/soccer_impact_common.py, src/market_intelligence/tail_event_classifier.py, src/market_intelligence/tennis_impact_common.py, src/research/causal_discovery_research.py, src/research/causal_scaffold.py, src/research/contrastive_embedding_diagnostics.py, src/research/correlation_structure_diagnostics.py, src/research/extreme_randomness_diagnostics.py, src/research/extreme_randomness_report.py, src/research/representation_feature_builder.py, src/research/tracy_widom_research.py, src/research/universality_research_lanes.py, src/security/__init__.py, src/security/ai_provider_security.py, src/security/hard_gate_policy.py, src/security/owner_approval_gate.py, src/security/risk_limit_guard.py, src/services/runtime_shared.py, src/services/security_readiness.py`
- runtime_callers: `src/ai/deepseek_response_validator.py, src/analytics/advanced_red_team_provider_policy.py, src/analytics/advanced_red_team_report.py, src/analytics/advanced_shape_diagnostics.py, src/analytics/bayesian_structural_baseline.py, src/analytics/dynamical_systems_diagnostics.py, src/analytics/extreme_signal_red_team.py, src/analytics/information_theory_diagnostics.py, src/analytics/intelligence_readiness_report.py, src/analytics/random_baseline_comparison.py, src/analytics/strategy_readiness_report.py, src/analytics/topological_red_team.py, src/core/conformal_uncertainty.py, src/core/random_matrix_risk.py, src/core/strategy_context_buckets.py, src/core/strategy_disagreement.py, src/core/strategy_maturity.py, src/core/strategy_promotion.py, src/core/strategy_registry.py, src/core/strategy_router.py, src/core/strategy_score_aggregator.py, src/market_intelligence/baseball_impact_common.py, src/market_intelligence/basketball_player_impact.py, src/market_intelligence/basketball_player_impact_common.py, src/market_intelligence/combat_impact_common.py, src/market_intelligence/cross_asset_embedding_router.py, src/market_intelligence/cross_asset_intelligence_router.py, src/market_intelligence/data_intelligence_registry.py, src/market_intelligence/football_impact_schema.py, src/market_intelligence/golf_impact_common.py, src/market_intelligence/graph_relationship_mapper.py, src/market_intelligence/hockey_impact_common.py, src/market_intelligence/soccer_impact_common.py, src/market_intelligence/tail_event_classifier.py, src/market_intelligence/tennis_impact_common.py, src/research/causal_discovery_research.py, src/research/causal_scaffold.py, src/research/contrastive_embedding_diagnostics.py, src/research/correlation_structure_diagnostics.py, src/research/extreme_randomness_diagnostics.py, src/research/extreme_randomness_report.py, src/research/representation_feature_builder.py, src/research/tracy_widom_research.py, src/research/universality_research_lanes.py, src/security/__init__.py, src/security/ai_provider_security.py, src/security/hard_gate_policy.py, src/security/owner_approval_gate.py, src/security/risk_limit_guard.py, src/services/runtime_shared.py, src/services/security_readiness.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/security/risk_limit_guard.py`

- imports_from: `src.security.policy, src.services.ledger_service`
- imported_by: `src/security/hard_gate_policy.py, src/services/runtime_shared.py, tests/test_phase10k8zt_provider_security_surface_retirement.py`
- runtime_callers: `src/security/hard_gate_policy.py, src/services/runtime_shared.py`
- test_callers: `tests/test_phase10k8zt_provider_security_surface_retirement.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/security/secret_safety.py`

- imports_from: `none`
- imported_by: `src/ai/deepseek_response_validator.py, src/analytics/advanced_red_team_report.py, src/analytics/advanced_shape_diagnostics.py, src/analytics/strategy_readiness_report.py, src/analytics/topological_red_team.py, src/core/strategy_context_buckets.py, src/core/strategy_disagreement.py, src/core/strategy_promotion.py, src/core/strategy_router.py, src/core/strategy_score_aggregator.py, src/market_intelligence/baseball_impact_common.py, src/market_intelligence/basketball_player_impact_common.py, src/market_intelligence/combat_impact_common.py, src/market_intelligence/football_impact_schema.py, src/market_intelligence/golf_impact_common.py, src/market_intelligence/hockey_impact_common.py, src/market_intelligence/response_compactor.py, src/market_intelligence/soccer_impact_common.py, src/market_intelligence/tennis_impact_common.py, src/security/__init__.py, src/security/hard_gate_policy.py`
- runtime_callers: `src/ai/deepseek_response_validator.py, src/analytics/advanced_red_team_report.py, src/analytics/advanced_shape_diagnostics.py, src/analytics/strategy_readiness_report.py, src/analytics/topological_red_team.py, src/core/strategy_context_buckets.py, src/core/strategy_disagreement.py, src/core/strategy_promotion.py, src/core/strategy_router.py, src/core/strategy_score_aggregator.py, src/market_intelligence/baseball_impact_common.py, src/market_intelligence/basketball_player_impact_common.py, src/market_intelligence/combat_impact_common.py, src/market_intelligence/football_impact_schema.py, src/market_intelligence/golf_impact_common.py, src/market_intelligence/hockey_impact_common.py, src/market_intelligence/response_compactor.py, src/market_intelligence/soccer_impact_common.py, src/market_intelligence/tennis_impact_common.py, src/security/__init__.py, src/security/hard_gate_policy.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/__init__.py`

- imports_from: `none`
- imported_by: `src/services/ops_workflow.py`
- runtime_callers: `src/services/ops_workflow.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/action_betting_service.py`

- imports_from: `src.providers`
- imported_by: `main.py, src/api/betting_action_routes.py, tests/test_analyze_event.py`
- runtime_callers: `src/api/betting_action_routes.py`
- test_callers: `tests/test_analyze_event.py`
- script_callers: `none`
- api_callers: `src/api/betting_action_routes.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/alert_engine.py`

- imports_from: `src.market_intelligence.opportunity_scoring`
- imported_by: `src/services/scheduler_runner.py`
- runtime_callers: `src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/audit_log.py`

- imports_from: `src.services.scheduler_config`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/automation_scheduler_facade.py`

- imports_from: `src.ai.deepseek_disagreement_queue, src.ai.deepseek_profit_lab, src.ai.deepseek_reviewer, src.ai.institutional_deepseek_review, src.analytics.calibration, src.analytics.calibration_collector, src.analytics.intelligence_readiness_report, src.analytics.micro_outcome_calibration, src.analytics.pattern_review_queue, src.analytics.review_queue, src.analytics.strategy_readiness_report, src.core.balance_sheet_risk, src.data, src.data.data_paths, src.market_intelligence.institutional_cross_asset_lab, src.market_intelligence.model_input_coverage, src.providers.health, src.providers.ncaaf_collegefootballdata_adapter, src.providers.registry, src.research.pattern_calibration, src.services.collector_scheduled_runner, src.services.execution_service, src.services.ledger_service, src.services.odds_runtime_bridge, src.services.outcome_store, src.services.prediction_market_runtime_bridge, src.services.runtime_shared, src.services.scheduler_config, src.services.scheduler_runner, src.services.security_readiness, src.services.settlement_service, src.services.system_health`
- imported_by: `main.py, src/api/provider_status_routes.py, src/services/ops_workflow.py, tests/test_phase10k8zga_provider_registry_runtime_blocker.py, tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py, tests/test_phase10k8zgd_final_provider_foundation_blocker_deletion.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- runtime_callers: `src/api/provider_status_routes.py, src/services/ops_workflow.py`
- test_callers: `tests/test_phase10k8zga_provider_registry_runtime_blocker.py, tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py, tests/test_phase10k8zgd_final_provider_foundation_blocker_deletion.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- script_callers: `none`
- api_callers: `src/api/provider_status_routes.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/bet_csv_service.py`

- imports_from: `none`
- imported_by: `main.py, src/api/bet_csv_routes.py`
- runtime_callers: `src/api/bet_csv_routes.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `src/api/bet_csv_routes.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/bet_decision_engine.py`

- imports_from: `src.core.market_pricing, src.core.quant_engine, src.services.model_blender`
- imported_by: `main.py, tests/test_evaluate_lines.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py`
- runtime_callers: `none`
- test_callers: `tests/test_evaluate_lines.py, tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/bet_log.py`

- imports_from: `src.core.clv, src.core.math_utils`
- imported_by: `main.py, tests/test_bet_log.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py`
- runtime_callers: `none`
- test_callers: `tests/test_bet_log.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/cadence_controller.py`

- imports_from: `src.providers.registry`
- imported_by: `src/analytics/review_queue.py, tests/test_phase10k8zga_provider_registry_runtime_blocker.py`
- runtime_callers: `src/analytics/review_queue.py`
- test_callers: `tests/test_phase10k8zga_provider_registry_runtime_blocker.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/collector_scheduled_runner.py`

- imports_from: `src.analytics.calibration_collector, src.data.data_paths`
- imported_by: `src/services/automation_scheduler_facade.py`
- runtime_callers: `src/services/automation_scheduler_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/decision_engine.py`

- imports_from: `src.brokerage.orders, src.brokerage.readiness, src.core.execution, src.core.game_theory, src.core.market_impact, src.core.portfolio, src.core.pricing, src.core.risk`
- imported_by: `tests/test_phase10k8zh8_decision_engine_service_plan.py, tests/test_phase10k8zhb_service_layer_ownership_audit.py, tests/test_phase10k8zhd_decision_and_bet_log_audit.py, tests/test_phase10k8zia_execution_scheduler_audit.py, tests/test_phase10k8zic_execution_ownership_migration.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zif_execution_boundary_checkpoint.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py, tests/test_phase10k8zik_execution_remediation_checkpoint.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8ziw_final_execution_blocker_audit.py, tests/test_phase10k8zix_final_execution_blocker_canonicalization.py, tests/test_phase10k8ziz_final_execution_blocker_delete_proof.py, tests/test_phase10k8zj0_final_execution_blocker_deletion.py, tests/test_phase10k8zj1_execution_cleanup_checkpoint.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zh8_decision_engine_service_plan.py, tests/test_phase10k8zhb_service_layer_ownership_audit.py, tests/test_phase10k8zhd_decision_and_bet_log_audit.py, tests/test_phase10k8zia_execution_scheduler_audit.py, tests/test_phase10k8zic_execution_ownership_migration.py, tests/test_phase10k8zid_execution_final_delete_readiness.py, tests/test_phase10k8zif_execution_boundary_checkpoint.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zih_execution_blocker_canonicalization.py, tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py, tests/test_phase10k8zik_execution_remediation_checkpoint.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py, tests/test_phase10k8ziw_final_execution_blocker_audit.py, tests/test_phase10k8zix_final_execution_blocker_canonicalization.py, tests/test_phase10k8ziz_final_execution_blocker_delete_proof.py, tests/test_phase10k8zj0_final_execution_blocker_deletion.py, tests/test_phase10k8zj1_execution_cleanup_checkpoint.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py, tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/enrichment_service.py`

- imports_from: `src.core.entity_resolver, src.services.odds_runtime_bridge, src.services.prediction_market_runtime_bridge`
- imported_by: `src/services/screenshot_intake.py, tests/test_phase10k8zfz_odds_data_connector_batch_2.py, tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py`
- runtime_callers: `src/services/screenshot_intake.py`
- test_callers: `tests/test_phase10k8zfz_odds_data_connector_batch_2.py, tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/execution_service.py`

- imports_from: `src.services.execution_support, src.services.ledger_service`
- imported_by: `src/ai/deepseek_profit_lab.py, src/api/automation_institutional_lab_routes.py, src/market_intelligence/cross_asset_manifold_router.py, src/market_intelligence/institutional_cross_asset_lab.py, src/market_intelligence/market_state_manifold.py, src/services/automation_scheduler_facade.py, tests/test_broker_quality_scoring.py, tests/test_institutional_execution_desk.py, tests/test_market_state_manifold.py, tests/test_phase10k8zin_strategy_execution_helper_canonicalization.py, tests/test_phase10k8zio_execution_helper_final_delete_readiness.py, tests/test_phase10k8zip_execution_helper_canonicalization_checkpoint.py, tests/test_phase10k8zix_final_execution_blocker_canonicalization.py, tests/test_small_account_strategy.py`
- runtime_callers: `src/ai/deepseek_profit_lab.py, src/api/automation_institutional_lab_routes.py, src/market_intelligence/cross_asset_manifold_router.py, src/market_intelligence/institutional_cross_asset_lab.py, src/market_intelligence/market_state_manifold.py, src/services/automation_scheduler_facade.py`
- test_callers: `tests/test_broker_quality_scoring.py, tests/test_institutional_execution_desk.py, tests/test_market_state_manifold.py, tests/test_phase10k8zin_strategy_execution_helper_canonicalization.py, tests/test_phase10k8zio_execution_helper_final_delete_readiness.py, tests/test_phase10k8zip_execution_helper_canonicalization_checkpoint.py, tests/test_phase10k8zix_final_execution_blocker_canonicalization.py, tests/test_small_account_strategy.py`
- script_callers: `none`
- api_callers: `src/api/automation_institutional_lab_routes.py`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/execution_support.py`

- imports_from: `src.services.runtime_shared`
- imported_by: `src/api/automation_security.py, src/services/execution_service.py, tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- runtime_callers: `src/api/automation_security.py, src/services/execution_service.py`
- test_callers: `tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- script_callers: `none`
- api_callers: `src/api/automation_security.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/full_board_engine.py`

- imports_from: `none`
- imported_by: `src/services/screenshot_intake.py, tests/test_nba_model_activation.py`
- runtime_callers: `src/services/screenshot_intake.py`
- test_callers: `tests/test_nba_model_activation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/ledger_service.py`

- imports_from: `src.services.ledger_support`
- imported_by: `src/ai/institutional_deepseek_review.py, src/brokerage/readiness.py, src/market_intelligence/institutional_cross_asset_lab.py, src/security/ai_provider_security.py, src/security/owner_approval_gate.py, src/security/risk_limit_guard.py, src/services/automation_scheduler_facade.py, src/services/execution_service.py, tests/test_institutional_audit_ledger.py, tests/test_phase10k8zim_ledger_canonicalization.py, tests/test_phase10k8zio_execution_helper_final_delete_readiness.py, tests/test_phase10k8zip_execution_helper_canonicalization_checkpoint.py, tests/test_phase10k8zix_final_execution_blocker_canonicalization.py, tests/test_security_framework.py`
- runtime_callers: `src/ai/institutional_deepseek_review.py, src/brokerage/readiness.py, src/market_intelligence/institutional_cross_asset_lab.py, src/security/ai_provider_security.py, src/security/owner_approval_gate.py, src/security/risk_limit_guard.py, src/services/automation_scheduler_facade.py, src/services/execution_service.py`
- test_callers: `tests/test_institutional_audit_ledger.py, tests/test_phase10k8zim_ledger_canonicalization.py, tests/test_phase10k8zio_execution_helper_final_delete_readiness.py, tests/test_phase10k8zip_execution_helper_canonicalization_checkpoint.py, tests/test_phase10k8zix_final_execution_blocker_canonicalization.py, tests/test_security_framework.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/ledger_support.py`

- imports_from: `src.services.runtime_shared`
- imported_by: `src/services/ledger_service.py, tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- runtime_callers: `src/services/ledger_service.py`
- test_callers: `tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/logbook_engine.py`

- imports_from: `none`
- imported_by: `src/services/screenshot_intake.py`
- runtime_callers: `src/services/screenshot_intake.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/model_backtest_service.py`

- imports_from: `src.core.backtester`
- imported_by: `src/api/model_backtest_routes.py, tests/test_phase10k8zhi_legacy_full_gate_remediation.py, tests/test_phase10k8zhm_data_backtesting_checkpoint.py`
- runtime_callers: `src/api/model_backtest_routes.py`
- test_callers: `tests/test_phase10k8zhi_legacy_full_gate_remediation.py, tests/test_phase10k8zhm_data_backtesting_checkpoint.py`
- script_callers: `none`
- api_callers: `src/api/model_backtest_routes.py`
- facade_callers: `tests/test_phase10k8zhi_legacy_full_gate_remediation.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/model_blender.py`

- imports_from: `none`
- imported_by: `src/services/bet_decision_engine.py`
- runtime_callers: `src/services/bet_decision_engine.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/model_recheck_runner.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry`
- imported_by: `tests/test_model_recheck_runner.py`
- runtime_callers: `none`
- test_callers: `tests/test_model_recheck_runner.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/odds_runtime_bridge.py`

- imports_from: `src.connectors.errors, src.connectors.odds_data, src.core.entity_resolver, src.providers.policy.secret_policy, src.providers.sportsbooks.adapters, src.providers.sportsbooks.contracts`
- imported_by: `src/services/automation_scheduler_facade.py, src/services/enrichment_service.py, src/services/scheduler_runner.py, tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py, tests/test_phase10k8zgm_odds_historical_test_redirection.py, tests/test_phase10k8zgn_odds_proof_history_cleanup.py, tests/test_phase10k8zgo_odds_compatibility_test_retirement.py, tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_sharp_sportsbook_adapter.py, tests/test_sportsbook_odds_provider.py`
- runtime_callers: `src/services/automation_scheduler_facade.py, src/services/enrichment_service.py, src/services/scheduler_runner.py`
- test_callers: `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py, tests/test_phase10k8zgm_odds_historical_test_redirection.py, tests/test_phase10k8zgn_odds_proof_history_cleanup.py, tests/test_phase10k8zgo_odds_compatibility_test_retirement.py, tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_sharp_sportsbook_adapter.py, tests/test_sportsbook_odds_provider.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py, tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py, tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgo_odds_compatibility_test_retirement.py, tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/ops_workflow.py`

- imports_from: `src.data, src.data.data_paths, src.services, src.services.automation_scheduler_facade`
- imported_by: `scripts/ops_check.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `scripts/ops_check.py`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `scripts/ops_check.py, scripts/run_tests.ps1`

## `src/services/outcome_store.py`

- imports_from: `src.data.data_paths, src.services.scheduler_config`
- imported_by: `src/ai/deepseek_profit_lab.py, src/analytics/calibration.py, src/analytics/calibration_collector.py, src/analytics/intelligence_readiness_report.py, src/analytics/manifold_calibration.py, src/providers/institutional_cross_asset_adapters.py, src/services/automation_scheduler_facade.py`
- runtime_callers: `src/ai/deepseek_profit_lab.py, src/analytics/calibration.py, src/analytics/calibration_collector.py, src/analytics/intelligence_readiness_report.py, src/analytics/manifold_calibration.py, src/providers/institutional_cross_asset_adapters.py, src/services/automation_scheduler_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/prediction_market_runtime_bridge.py`

- imports_from: `src.connectors.errors, src.connectors.prediction_market_data, src.core.entity_resolver, src.providers.policy.secret_policy, src.providers.prediction_markets.adapters, src.providers.registry, src.providers.validation`
- imported_by: `src/analytics/calibration_collector.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/providers/kalshi_readonly_readiness.py, src/services/automation_scheduler_facade.py, src/services/enrichment_service.py, src/services/scheduler_runner.py, src/services/settlement_service.py, tests/test_calibration_collector.py, tests/test_kalshi_market_provider.py, tests/test_kalshi_readonly_adapter.py, tests/test_kalshi_readonly_readiness_contract.py, tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py, tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py, tests/test_phase10k8zgy_prediction_market_shell_deletion.py`
- runtime_callers: `src/analytics/calibration_collector.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/providers/kalshi_readonly_readiness.py, src/services/automation_scheduler_facade.py, src/services/enrichment_service.py, src/services/scheduler_runner.py, src/services/settlement_service.py`
- test_callers: `tests/test_calibration_collector.py, tests/test_kalshi_market_provider.py, tests/test_kalshi_readonly_adapter.py, tests/test_kalshi_readonly_readiness_contract.py, tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py, tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py, tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py, tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py, tests/test_phase10k8zgy_prediction_market_shell_deletion.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py, tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py, tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/repo_inventory.py`

- imports_from: `none`
- imported_by: `scripts/ops_check.py, tests/test_phase_x_non_src_inventory.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase_x_non_src_inventory.py`
- script_callers: `scripts/ops_check.py`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/run_context.py`

- imports_from: `none`
- imported_by: `src/services/scheduler_runner.py`
- runtime_callers: `src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/runtime_shared.py`

- imports_from: `src.analytics.pattern_review_queue, src.core.balance_sheet_risk, src.market_intelligence.candlestick_pattern_detector, src.providers.institutional_cross_asset_adapters, src.providers.policy.allowlist, src.security.owner_approval_gate, src.security.policy, src.security.risk_limit_guard`
- imported_by: `src/brokerage/readiness_support.py, src/services/automation_scheduler_facade.py, src/services/execution_support.py, src/services/ledger_support.py, src/services/settlement_support.py`
- runtime_callers: `src/brokerage/readiness_support.py, src/services/automation_scheduler_facade.py, src/services/execution_support.py, src/services/ledger_support.py, src/services/settlement_support.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/scheduler_config.py`

- imports_from: `src.data.data_paths, src.providers.registry`
- imported_by: `src/ai/deepseek_daily_report.py, src/ai/deepseek_data_pull_check.py, src/ai/deepseek_disagreement_queue.py, src/ai/deepseek_profit_lab.py, src/ai/deepseek_response_validator.py, src/ai/deepseek_reviewer.py, src/analytics/advanced_red_team_report.py, src/analytics/calibration.py, src/analytics/calibration_collector.py, src/analytics/derived_feature_backfill_report.py, src/analytics/field_scorecard.py, src/analytics/institutional_cross_asset_reports.py, src/analytics/manifold_calibration.py, src/analytics/manifold_review_queue.py, src/analytics/micro_outcome_calibration.py, src/analytics/model_performance_report.py, src/analytics/pattern_review_queue.py, src/analytics/report_writer.py, src/analytics/review_queue.py, src/backtesting/backtesting_engine.py, src/brokerage/later/execution_audit_log.py, src/brokerage/paper_decision_ledger.py, src/brokerage/paper_trade_ledger.py, src/core/liquidity_risk.py, src/core/strategy_disagreement.py, src/market_intelligence/candlestick_pattern_detector.py, src/market_intelligence/clv_tracker.py, src/market_intelligence/institutional_cross_asset_lab.py, src/market_intelligence/local_sports_history_audit.py, src/market_intelligence/manifold_cluster_registry.py, src/market_intelligence/manifold_feature_builder.py, src/market_intelligence/nfl_coaching_feature_builders.py, src/market_intelligence/nfl_coaching_sources.py, src/market_intelligence/nfl_cutoff_week_features.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/providers/injury_weather_adapter_contract.py, src/providers/institutional_cross_asset_adapters.py, src/providers/news_events_adapter_contract.py, src/providers/nfl_coaching_adapters.py, src/providers/nfl_open_data_adapters.py, src/providers/nfl_open_data_backfill.py, src/providers/nfl_open_data_feature_builders.py, src/providers/nfl_open_data_feature_readiness.py, src/providers/player_props_adapter_contract.py, src/providers/stock_fundamentals_adapter_contract.py, src/providers/stock_price_adapter_contract.py, src/research/pattern_calibration.py, src/security/owner_approval_gate.py, src/services/audit_log.py, src/services/automation_scheduler_facade.py, src/services/outcome_store.py, src/services/scheduler_runner.py, src/services/snapshot_store.py, src/services/system_health.py, tests/test_phase10k8zga_provider_registry_runtime_blocker.py`
- runtime_callers: `src/ai/deepseek_daily_report.py, src/ai/deepseek_data_pull_check.py, src/ai/deepseek_disagreement_queue.py, src/ai/deepseek_profit_lab.py, src/ai/deepseek_response_validator.py, src/ai/deepseek_reviewer.py, src/analytics/advanced_red_team_report.py, src/analytics/calibration.py, src/analytics/calibration_collector.py, src/analytics/derived_feature_backfill_report.py, src/analytics/field_scorecard.py, src/analytics/institutional_cross_asset_reports.py, src/analytics/manifold_calibration.py, src/analytics/manifold_review_queue.py, src/analytics/micro_outcome_calibration.py, src/analytics/model_performance_report.py, src/analytics/pattern_review_queue.py, src/analytics/report_writer.py, src/analytics/review_queue.py, src/backtesting/backtesting_engine.py, src/brokerage/later/execution_audit_log.py, src/brokerage/paper_decision_ledger.py, src/brokerage/paper_trade_ledger.py, src/core/liquidity_risk.py, src/core/strategy_disagreement.py, src/market_intelligence/candlestick_pattern_detector.py, src/market_intelligence/clv_tracker.py, src/market_intelligence/institutional_cross_asset_lab.py, src/market_intelligence/local_sports_history_audit.py, src/market_intelligence/manifold_cluster_registry.py, src/market_intelligence/manifold_feature_builder.py, src/market_intelligence/nfl_coaching_feature_builders.py, src/market_intelligence/nfl_coaching_sources.py, src/market_intelligence/nfl_cutoff_week_features.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/providers/injury_weather_adapter_contract.py, src/providers/institutional_cross_asset_adapters.py, src/providers/news_events_adapter_contract.py, src/providers/nfl_coaching_adapters.py, src/providers/nfl_open_data_adapters.py, src/providers/nfl_open_data_backfill.py, src/providers/nfl_open_data_feature_builders.py, src/providers/nfl_open_data_feature_readiness.py, src/providers/player_props_adapter_contract.py, src/providers/stock_fundamentals_adapter_contract.py, src/providers/stock_price_adapter_contract.py, src/research/pattern_calibration.py, src/security/owner_approval_gate.py, src/services/audit_log.py, src/services/automation_scheduler_facade.py, src/services/outcome_store.py, src/services/scheduler_runner.py, src/services/snapshot_store.py, src/services/system_health.py`
- test_callers: `tests/test_phase10k8zga_provider_registry_runtime_blocker.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/scheduler_runner.py`

- imports_from: `src.analytics.calibration, src.analytics.model_governance.cross_book_gate, src.analytics.model_governance.data_lineage, src.analytics.model_governance.data_quality_monitor, src.analytics.model_governance.settlement_liquidity_gate, src.analytics.report_writer, src.analytics.review_queue, src.backtesting.engine, src.brokerage.paper_decision_ledger, src.core.cross_book_line_comparator, src.core.ev_line_shopper, src.core.market_structure, src.data.data_paths, src.market_intelligence.arbitrage_detector, src.market_intelligence.middle_opportunity_detector, src.market_intelligence.opportunity_scoring, src.providers.base, src.providers.health, src.providers.kalshi_monitor, src.providers.kalshi_scoring, src.services.alert_engine, src.services.odds_runtime_bridge, src.services.prediction_market_runtime_bridge, src.services.run_context, src.services.scheduler_config, src.services.snapshot_store, src.services.system_health`
- imported_by: `src/analytics/calibration_collector.py, src/services/automation_scheduler_facade.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- runtime_callers: `src/analytics/calibration_collector.py, src/services/automation_scheduler_facade.py`
- test_callers: `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/screenshot_intake.py`

- imports_from: `src.core.entity_resolver, src.market_intelligence.multi_sport_model_registry, src.services.enrichment_service, src.services.full_board_engine, src.services.logbook_engine`
- imported_by: `main.py, tests/test_phase10k8zhc_screenshot_workflow_thinning_plan.py, tests/test_tennis_model_activation.py`
- runtime_callers: `none`
- test_callers: `tests/test_phase10k8zhc_screenshot_workflow_thinning_plan.py, tests/test_tennis_model_activation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/security_readiness.py`

- imports_from: `src.data.data_paths, src.security.ai_provider_security, src.security.policy`
- imported_by: `src/ai/deepseek_profit_lab.py, src/analytics/intelligence_readiness_report.py, src/services/automation_scheduler_facade.py`
- runtime_callers: `src/ai/deepseek_profit_lab.py, src/analytics/intelligence_readiness_report.py, src/services/automation_scheduler_facade.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/settlement_service.py`

- imports_from: `src.brokerage.settlement, src.services.prediction_market_runtime_bridge, src.services.settlement_support`
- imported_by: `src/analytics/calibration_collector.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/services/automation_scheduler_facade.py, tests/test_outcome_store.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zil_settlement_canonicalization.py, tests/test_phase10k8zip_execution_helper_canonicalization_checkpoint.py, tests/test_settlement_discovery.py`
- runtime_callers: `src/analytics/calibration_collector.py, src/market_intelligence/prediction_market_outcome_candidates.py, src/services/automation_scheduler_facade.py`
- test_callers: `tests/test_outcome_store.py, tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py, tests/test_phase10k8zig_execution_blocker_remediation_audit.py, tests/test_phase10k8zil_settlement_canonicalization.py, tests/test_phase10k8zip_execution_helper_canonicalization_checkpoint.py, tests/test_settlement_discovery.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py, tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/settlement_support.py`

- imports_from: `src.services.runtime_shared`
- imported_by: `src/services/settlement_service.py, tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- runtime_callers: `src/services/settlement_service.py`
- test_callers: `tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/snapshot_store.py`

- imports_from: `src.services.scheduler_config`
- imported_by: `src/services/scheduler_runner.py`
- runtime_callers: `src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/streamlit_dashboard_data.py`

- imports_from: `src.backtesting.dataset_builder, src.backtesting.engine, src.backtesting.historical_bridge, src.backtesting.strategy_profiles, src.core.quant_engine, src.data, src.data.historical_odds, src.data.historical_sources, src.data.line_movement, src.data.source_event_links, src.market_intelligence.feature_packs, src.research.feature_control, src.research.history`
- imported_by: `src/data/line_movement.py, tests/test_phase10k8d_paper_only_fixture_readiness_payload_adapter.py, tests/test_phase10k8f_paper_only_fixture_evaluation_helper.py, tests/test_phase10k8g_paper_only_evaluation_readiness_adapter.py, tests/test_phase10k8i_paper_only_fixture_pipeline_helper.py, tests/test_phase10k8j_controlled_pipeline_smoke_review.py, tests/test_phase10k8k_prediction_testing_readiness_review.py, tests/test_phase10k8q_dedicated_0dte_validation_readiness_payload.py, tests/test_phase10k8r_dedicated_0dte_validation_readiness_ui.py, tests/test_phase10k8t_dedicated_0dte_evaluation_readiness_payload.py, tests/test_phase10k8u_dedicated_0dte_evaluation_ui.py, tests/test_phase10k8x_controlled_0dte_paper_run_smoke_review.py, tests/test_phase10k8y_0dte_prediction_testing_readiness_review.py, tests/test_phase10k8ze_institutional_market_metric_catalog.py, tests/test_phase10k8zf1_compatibility_alias_migration.py, tests/test_phase10k8zf2_production_symbol_migration.py`
- runtime_callers: `src/data/line_movement.py`
- test_callers: `tests/test_phase10k8d_paper_only_fixture_readiness_payload_adapter.py, tests/test_phase10k8f_paper_only_fixture_evaluation_helper.py, tests/test_phase10k8g_paper_only_evaluation_readiness_adapter.py, tests/test_phase10k8i_paper_only_fixture_pipeline_helper.py, tests/test_phase10k8j_controlled_pipeline_smoke_review.py, tests/test_phase10k8k_prediction_testing_readiness_review.py, tests/test_phase10k8q_dedicated_0dte_validation_readiness_payload.py, tests/test_phase10k8r_dedicated_0dte_validation_readiness_ui.py, tests/test_phase10k8t_dedicated_0dte_evaluation_readiness_payload.py, tests/test_phase10k8u_dedicated_0dte_evaluation_ui.py, tests/test_phase10k8x_controlled_0dte_paper_run_smoke_review.py, tests/test_phase10k8y_0dte_prediction_testing_readiness_review.py, tests/test_phase10k8ze_institutional_market_metric_catalog.py, tests/test_phase10k8zf1_compatibility_alias_migration.py, tests/test_phase10k8zf2_production_symbol_migration.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `tests/test_phase10k8zf1_compatibility_alias_migration.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `data/backtests/canonical/latest.jsonl, data/backtests/canonical/schema_report.json, data/backtests/dashboard/latest_dashboard.json, data/backtests/dashboard/latest_dashboard.md, data/historical/historical_odds.db, data/historical/uploads, data/paper_ledger/latest.json, data/review_queue/latest.json, data/review_queue/review_queue.json, data/system_health/health.json`

## `src/services/streamlit_dashboard_facade.py`

- imports_from: `src.analytics.calibration_collector, src.analytics.institutional_cross_asset_reports, src.analytics.pattern_review_queue, src.analytics.performance_metrics, src.data, src.market_intelligence.local_sports_history_audit, src.market_intelligence.nfl_coaching_sources, src.providers.nfl_coaching_adapters, src.providers.nfl_open_data_adapters, src.research.pattern_calibration`
- imported_by: `streamlit_app.py, tests/test_advanced_red_team.py, tests/test_alert_engine.py, tests/test_arbitrage_detector.py, tests/test_arbitrage_draw_market.py, tests/test_arbitrage_exchange.py, tests/test_arbitrage_prediction_market.py, tests/test_arbitrage_risk_filters.py, tests/test_arbitrage_three_way.py, tests/test_arbitrage_two_way.py, tests/test_asof_line_movement_query.py, tests/test_audit_log.py, tests/test_backtest_dataset_builder.py, tests/test_backtest_leakage.py, tests/test_backtest_regression_strategy.py, tests/test_backtest_schema.py, tests/test_backtest_strategy_bankroll.py, tests/test_backtest_strategy_profiles.py, tests/test_backtesting.py, tests/test_backtesting_engine.py, tests/test_balance_sheet_risk.py, tests/test_basketball_player_impact.py, tests/test_bookmaker_normalizer.py, tests/test_budget_gates.py, tests/test_cadence_controller.py, tests/test_calibration.py, tests/test_calibration_collector.py, tests/test_calibration_strategy_filter.py, tests/test_calibration_tracker.py, tests/test_candlestick_pattern_detector.py, tests/test_clv_tracker.py, tests/test_collector_scheduled_runner.py, tests/test_cross_book_line_comparator.py, tests/test_crypto_edge_lab_registry.py, tests/test_data_availability_tiers.py, tests/test_data_intelligence_stack.py, tests/test_data_paths.py, tests/test_deepseek_data_pull_check_contract.py, tests/test_deepseek_profit_lab.py, tests/test_deepseek_reviewer.py, tests/test_derived_feature_backfill_report.py, tests/test_derived_feature_planner.py, tests/test_ev_line_shopper.py, tests/test_experiment_history_store.py, tests/test_experiment_report_exporter.py, tests/test_extreme_randomness_diagnostics.py, tests/test_feature_ablation_lab.py, tests/test_football_impact_intelligence.py, tests/test_historical_backtest_bridge.py, tests/test_historical_data_sources.py, tests/test_historical_line_movement.py, tests/test_historical_odds_importers.py, tests/test_historical_odds_sqlite.py, tests/test_historical_replay.py, tests/test_injury_weather_adapter_contract.py, tests/test_institutional_cross_asset_adapters.py, tests/test_institutional_cross_asset_lab.py, tests/test_institutional_cross_asset_reports.py, tests/test_institutional_cross_asset_scores.py, tests/test_institutional_deepseek_review.py, tests/test_institutional_model_router.py, tests/test_institutional_risk_engine.py, tests/test_institutional_stock_pro_analyst_registry.py, tests/test_kalshi_adapter_contract.py, tests/test_kalshi_market_provider.py, tests/test_kalshi_monitor.py, tests/test_kalshi_provider_shape_contract.py, tests/test_kalshi_readonly_readiness_contract.py, tests/test_kalshi_scoring.py, tests/test_later_auto_execution_policy.py, tests/test_line_movement_data_quality_dashboard.py, tests/test_line_movement_import_contract.py, tests/test_line_movement_readiness.py, tests/test_liquidity_context_scoring.py, tests/test_liquidity_risk.py, tests/test_local_sports_history_audit.py, tests/test_market_feature_packs.py, tests/test_market_identity_resolver.py, tests/test_market_state_manifold.py, tests/test_market_structure.py, tests/test_middle_alt_line.py, tests/test_middle_ev_simulator.py, tests/test_middle_key_number.py, tests/test_middle_opportunity_detector.py, tests/test_middle_prop.py, tests/test_middle_push_corridor.py, tests/test_middle_spread.py, tests/test_middle_team_total.py, tests/test_middle_total.py, tests/test_model_input_coverage.py, tests/test_model_performance_report.py, tests/test_ncaaf_collegefootballdata_adapter.py, tests/test_news_event_monitor.py, tests/test_news_events_adapter_contract.py, tests/test_nfl_coaching_adapters.py, tests/test_nfl_coaching_feature_builders.py, tests/test_nfl_coaching_sources.py, tests/test_nfl_historical_pattern_lab.py, tests/test_nfl_historical_pattern_validation.py, tests/test_nfl_open_data_adapters.py, tests/test_nfl_open_data_backfill.py, tests/test_nfl_open_data_feature_builders.py, tests/test_nfl_open_data_field_catalog.py, tests/test_nfl_open_data_sources.py, tests/test_nfl_source_exhaustion.py, tests/test_no_vig_pricing.py, tests/test_odds_line_monitor.py, tests/test_odds_math.py, tests/test_open_sports_history_derived_features.py, tests/test_open_sports_history_import.py, tests/test_opportunity_scoring.py, tests/test_ops_workflow.py, tests/test_outcome_import_endpoint.py, tests/test_outcome_migration.py, tests/test_outcome_reconciliation.py, tests/test_outcome_store.py, tests/test_paper_decision_ledger.py, tests/test_paper_trade_ledger.py, tests/test_pattern_calibration.py, tests/test_pattern_review_queue.py, tests/test_performance_metrics.py, tests/test_phase10k5_core_arbitrage_engine.py, tests/test_phase10k8c_paper_only_fixture_validation_helper.py, tests/test_phase10k8d_paper_only_fixture_readiness_payload_adapter.py, tests/test_phase10k8f_paper_only_fixture_evaluation_helper.py, tests/test_phase10k8g_paper_only_evaluation_readiness_adapter.py, tests/test_phase10k8m_strict_model_field_baseline_by_market_and_sport.py, tests/test_phase10k8n_controlled_field_catalog_ui_review.py, tests/test_phase10k8o_dedicated_0dte_paper_fixture_template.py, tests/test_phase10k8p_dedicated_0dte_fixture_validation_adapter.py, tests/test_phase10k8q_dedicated_0dte_validation_readiness_payload.py, tests/test_phase10k8s_dedicated_0dte_paper_evaluation_adapter.py, tests/test_phase10k8u_dedicated_0dte_evaluation_ui.py, tests/test_phase10k8v_full_0dte_paper_pipeline_adapter.py, tests/test_phase10k8y_0dte_prediction_testing_readiness_review.py, tests/test_phase10k8za_0dte_data_field_formula_coverage_audit.py, tests/test_phase10k8zb_0dte_field_formula_gap_patch.py, tests/test_phase10k8ze_institutional_market_metric_catalog.py, tests/test_phase10k8zfg_safe_migration_batch_1.py, tests/test_phase10k8zl6_market_intelligence_runtime_test_redirection.py, tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py, tests/test_player_prop_monitor.py, tests/test_player_props_adapter_contract.py, tests/test_report_writer.py, tests/test_response_compactor.py, tests/test_review_queue.py, tests/test_run_context.py, tests/test_scheduler_config.py, tests/test_scheduler_runner.py, tests/test_security_framework.py, tests/test_sharp_cross_book_review_queue.py, tests/test_sharp_scheduler_flow.py, tests/test_small_account_strategy.py, tests/test_snapshot_store.py, tests/test_source_event_link_resolver.py, tests/test_source_quality_scoring.py, tests/test_sport_feature_packs.py, tests/test_sportsbook_adapter_contract.py, tests/test_sportsbook_odds_provider.py, tests/test_stock_fundamentals_adapter_contract.py, tests/test_stock_monitor.py, tests/test_stock_price_adapter_contract.py, tests/test_strategy_framework.py, tests/test_streamlit_dashboard_data.py, tests/test_system_health.py`
- runtime_callers: `streamlit_app.py`
- test_callers: `tests/test_advanced_red_team.py, tests/test_alert_engine.py, tests/test_arbitrage_detector.py, tests/test_arbitrage_draw_market.py, tests/test_arbitrage_exchange.py, tests/test_arbitrage_prediction_market.py, tests/test_arbitrage_risk_filters.py, tests/test_arbitrage_three_way.py, tests/test_arbitrage_two_way.py, tests/test_asof_line_movement_query.py, tests/test_audit_log.py, tests/test_backtest_dataset_builder.py, tests/test_backtest_leakage.py, tests/test_backtest_regression_strategy.py, tests/test_backtest_schema.py, tests/test_backtest_strategy_bankroll.py, tests/test_backtest_strategy_profiles.py, tests/test_backtesting.py, tests/test_backtesting_engine.py, tests/test_balance_sheet_risk.py, tests/test_basketball_player_impact.py, tests/test_bookmaker_normalizer.py, tests/test_budget_gates.py, tests/test_cadence_controller.py, tests/test_calibration.py, tests/test_calibration_collector.py, tests/test_calibration_strategy_filter.py, tests/test_calibration_tracker.py, tests/test_candlestick_pattern_detector.py, tests/test_clv_tracker.py, tests/test_collector_scheduled_runner.py, tests/test_cross_book_line_comparator.py, tests/test_crypto_edge_lab_registry.py, tests/test_data_availability_tiers.py, tests/test_data_intelligence_stack.py, tests/test_data_paths.py, tests/test_deepseek_data_pull_check_contract.py, tests/test_deepseek_profit_lab.py, tests/test_deepseek_reviewer.py, tests/test_derived_feature_backfill_report.py, tests/test_derived_feature_planner.py, tests/test_ev_line_shopper.py, tests/test_experiment_history_store.py, tests/test_experiment_report_exporter.py, tests/test_extreme_randomness_diagnostics.py, tests/test_feature_ablation_lab.py, tests/test_football_impact_intelligence.py, tests/test_historical_backtest_bridge.py, tests/test_historical_data_sources.py, tests/test_historical_line_movement.py, tests/test_historical_odds_importers.py, tests/test_historical_odds_sqlite.py, tests/test_historical_replay.py, tests/test_injury_weather_adapter_contract.py, tests/test_institutional_cross_asset_adapters.py, tests/test_institutional_cross_asset_lab.py, tests/test_institutional_cross_asset_reports.py, tests/test_institutional_cross_asset_scores.py, tests/test_institutional_deepseek_review.py, tests/test_institutional_model_router.py, tests/test_institutional_risk_engine.py, tests/test_institutional_stock_pro_analyst_registry.py, tests/test_kalshi_adapter_contract.py, tests/test_kalshi_market_provider.py, tests/test_kalshi_monitor.py, tests/test_kalshi_provider_shape_contract.py, tests/test_kalshi_readonly_readiness_contract.py, tests/test_kalshi_scoring.py, tests/test_later_auto_execution_policy.py, tests/test_line_movement_data_quality_dashboard.py, tests/test_line_movement_import_contract.py, tests/test_line_movement_readiness.py, tests/test_liquidity_context_scoring.py, tests/test_liquidity_risk.py, tests/test_local_sports_history_audit.py, tests/test_market_feature_packs.py, tests/test_market_identity_resolver.py, tests/test_market_state_manifold.py, tests/test_market_structure.py, tests/test_middle_alt_line.py, tests/test_middle_ev_simulator.py, tests/test_middle_key_number.py, tests/test_middle_opportunity_detector.py, tests/test_middle_prop.py, tests/test_middle_push_corridor.py, tests/test_middle_spread.py, tests/test_middle_team_total.py, tests/test_middle_total.py, tests/test_model_input_coverage.py, tests/test_model_performance_report.py, tests/test_ncaaf_collegefootballdata_adapter.py, tests/test_news_event_monitor.py, tests/test_news_events_adapter_contract.py, tests/test_nfl_coaching_adapters.py, tests/test_nfl_coaching_feature_builders.py, tests/test_nfl_coaching_sources.py, tests/test_nfl_historical_pattern_lab.py, tests/test_nfl_historical_pattern_validation.py, tests/test_nfl_open_data_adapters.py, tests/test_nfl_open_data_backfill.py, tests/test_nfl_open_data_feature_builders.py, tests/test_nfl_open_data_field_catalog.py, tests/test_nfl_open_data_sources.py, tests/test_nfl_source_exhaustion.py, tests/test_no_vig_pricing.py, tests/test_odds_line_monitor.py, tests/test_odds_math.py, tests/test_open_sports_history_derived_features.py, tests/test_open_sports_history_import.py, tests/test_opportunity_scoring.py, tests/test_ops_workflow.py, tests/test_outcome_import_endpoint.py, tests/test_outcome_migration.py, tests/test_outcome_reconciliation.py, tests/test_outcome_store.py, tests/test_paper_decision_ledger.py, tests/test_paper_trade_ledger.py, tests/test_pattern_calibration.py, tests/test_pattern_review_queue.py, tests/test_performance_metrics.py, tests/test_phase10k5_core_arbitrage_engine.py, tests/test_phase10k8c_paper_only_fixture_validation_helper.py, tests/test_phase10k8d_paper_only_fixture_readiness_payload_adapter.py, tests/test_phase10k8f_paper_only_fixture_evaluation_helper.py, tests/test_phase10k8g_paper_only_evaluation_readiness_adapter.py, tests/test_phase10k8m_strict_model_field_baseline_by_market_and_sport.py, tests/test_phase10k8n_controlled_field_catalog_ui_review.py, tests/test_phase10k8o_dedicated_0dte_paper_fixture_template.py, tests/test_phase10k8p_dedicated_0dte_fixture_validation_adapter.py, tests/test_phase10k8q_dedicated_0dte_validation_readiness_payload.py, tests/test_phase10k8s_dedicated_0dte_paper_evaluation_adapter.py, tests/test_phase10k8u_dedicated_0dte_evaluation_ui.py, tests/test_phase10k8v_full_0dte_paper_pipeline_adapter.py, tests/test_phase10k8y_0dte_prediction_testing_readiness_review.py, tests/test_phase10k8za_0dte_data_field_formula_coverage_audit.py, tests/test_phase10k8zb_0dte_field_formula_gap_patch.py, tests/test_phase10k8ze_institutional_market_metric_catalog.py, tests/test_phase10k8zfg_safe_migration_batch_1.py, tests/test_phase10k8zl6_market_intelligence_runtime_test_redirection.py, tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py, tests/test_player_prop_monitor.py, tests/test_player_props_adapter_contract.py, tests/test_report_writer.py, tests/test_response_compactor.py, tests/test_review_queue.py, tests/test_run_context.py, tests/test_scheduler_config.py, tests/test_scheduler_runner.py, tests/test_security_framework.py, tests/test_sharp_cross_book_review_queue.py, tests/test_sharp_scheduler_flow.py, tests/test_small_account_strategy.py, tests/test_snapshot_store.py, tests/test_source_event_link_resolver.py, tests/test_source_quality_scoring.py, tests/test_sport_feature_packs.py, tests/test_sportsbook_adapter_contract.py, tests/test_sportsbook_odds_provider.py, tests/test_stock_fundamentals_adapter_contract.py, tests/test_stock_monitor.py, tests/test_stock_price_adapter_contract.py, tests/test_strategy_framework.py, tests/test_streamlit_dashboard_data.py, tests/test_system_health.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/services/system_health.py`

- imports_from: `src.analytics.model_governance.model_inventory, src.analytics.review_queue, src.brokerage.paper_trade_ledger, src.data.data_paths, src.market_intelligence.clv_tracker, src.services.scheduler_config`
- imported_by: `src/services/automation_scheduler_facade.py, src/services/scheduler_runner.py`
- runtime_callers: `src/services/automation_scheduler_facade.py, src/services/scheduler_runner.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `src/services/automation_scheduler_facade.py`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/sports/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/sports/nba_features.py`

- imports_from: `src.core.math_utils`
- imported_by: `src/api/model_card_service.py, src/core/backtester.py`
- runtime_callers: `src/api/model_card_service.py, src/core/backtester.py`
- test_callers: `none`
- script_callers: `none`
- api_callers: `src/api/model_card_service.py`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/storage/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/storage/archive_manifest.py`

- imports_from: `none`
- imported_by: `scripts/daily_data_hygiene.py, scripts/r2_archive_pipeline.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `scripts/daily_data_hygiene.py, scripts/r2_archive_pipeline.py`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `src/storage/r2_archive_adapter.py`

- imports_from: `none`
- imported_by: `scripts/r2_archive_pipeline.py`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `scripts/r2_archive_pipeline.py`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `streamlit_app.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/conftest.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/support/__init__.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/support/action_imports.py`

- imports_from: `api_server, src.api.schemas`
- imported_by: `tests/test_advanced_red_team.py, tests/test_afl_model_activation.py, tests/test_automation_scheduler_endpoints.py, tests/test_badminton_model_activation.py, tests/test_baseball_impact_intelligence.py, tests/test_basketball_player_impact.py, tests/test_bet_log.py, tests/test_call_of_duty_esports_model_activation.py, tests/test_collector_scheduled_runner.py, tests/test_college_football_model_activation.py, tests/test_combat_impact_intelligence.py, tests/test_combat_sports_model_activation.py, tests/test_cricket_model_activation.py, tests/test_cs2_esports_model_activation.py, tests/test_darts_model_activation.py, tests/test_data_intelligence_stack.py, tests/test_data_source_endpoints.py, tests/test_deepseek_data_pull_check_contract.py, tests/test_dota2_esports_model_activation.py, tests/test_extreme_randomness_diagnostics.py, tests/test_football_impact_intelligence.py, tests/test_formula_1_model_activation.py, tests/test_formula_e_model_activation.py, tests/test_golf_impact_intelligence.py, tests/test_golf_model_activation.py, tests/test_handball_model_activation.py, tests/test_hockey_impact_intelligence.py, tests/test_indycar_model_activation.py, tests/test_lacrosse_model_activation.py, tests/test_league_of_legends_esports_model_activation.py, tests/test_market_state_manifold.py, tests/test_mens_college_basketball_model_activation.py, tests/test_mlb_model_activation.py, tests/test_model_probability.py, tests/test_motogp_model_activation.py, tests/test_multi_sport_model_registry.py, tests/test_nascar_model_activation.py, tests/test_nba_model_activation.py, tests/test_nfl_model_activation.py, tests/test_nhl_model_activation.py, tests/test_outcome_import_endpoint.py, tests/test_overwatch_esports_model_activation.py, tests/test_pickleball_model_activation.py, tests/test_price_event.py, tests/test_rugby_model_activation.py, tests/test_screenshot_analysis.py, tests/test_screenshot_normalization_parity.py, tests/test_security_framework.py, tests/test_small_account_endpoints.py, tests/test_snooker_model_activation.py, tests/test_soccer_impact_intelligence.py, tests/test_soccer_model_activation.py, tests/test_sport_analysis_endpoint.py, tests/test_table_tennis_model_activation.py, tests/test_tennis_impact_intelligence.py, tests/test_tennis_model_activation.py, tests/test_valorant_esports_model_activation.py, tests/test_volleyball_model_activation.py, tests/test_water_polo_model_activation.py, tests/test_wnba_model_activation.py, tests/test_womens_college_basketball_model_activation.py`
- runtime_callers: `none`
- test_callers: `tests/test_advanced_red_team.py, tests/test_afl_model_activation.py, tests/test_automation_scheduler_endpoints.py, tests/test_badminton_model_activation.py, tests/test_baseball_impact_intelligence.py, tests/test_basketball_player_impact.py, tests/test_bet_log.py, tests/test_call_of_duty_esports_model_activation.py, tests/test_collector_scheduled_runner.py, tests/test_college_football_model_activation.py, tests/test_combat_impact_intelligence.py, tests/test_combat_sports_model_activation.py, tests/test_cricket_model_activation.py, tests/test_cs2_esports_model_activation.py, tests/test_darts_model_activation.py, tests/test_data_intelligence_stack.py, tests/test_data_source_endpoints.py, tests/test_deepseek_data_pull_check_contract.py, tests/test_dota2_esports_model_activation.py, tests/test_extreme_randomness_diagnostics.py, tests/test_football_impact_intelligence.py, tests/test_formula_1_model_activation.py, tests/test_formula_e_model_activation.py, tests/test_golf_impact_intelligence.py, tests/test_golf_model_activation.py, tests/test_handball_model_activation.py, tests/test_hockey_impact_intelligence.py, tests/test_indycar_model_activation.py, tests/test_lacrosse_model_activation.py, tests/test_league_of_legends_esports_model_activation.py, tests/test_market_state_manifold.py, tests/test_mens_college_basketball_model_activation.py, tests/test_mlb_model_activation.py, tests/test_model_probability.py, tests/test_motogp_model_activation.py, tests/test_multi_sport_model_registry.py, tests/test_nascar_model_activation.py, tests/test_nba_model_activation.py, tests/test_nfl_model_activation.py, tests/test_nhl_model_activation.py, tests/test_outcome_import_endpoint.py, tests/test_overwatch_esports_model_activation.py, tests/test_pickleball_model_activation.py, tests/test_price_event.py, tests/test_rugby_model_activation.py, tests/test_screenshot_analysis.py, tests/test_screenshot_normalization_parity.py, tests/test_security_framework.py, tests/test_small_account_endpoints.py, tests/test_snooker_model_activation.py, tests/test_soccer_impact_intelligence.py, tests/test_soccer_model_activation.py, tests/test_sport_analysis_endpoint.py, tests/test_table_tennis_model_activation.py, tests/test_tennis_impact_intelligence.py, tests/test_tennis_model_activation.py, tests/test_valorant_esports_model_activation.py, tests/test_volleyball_model_activation.py, tests/test_water_polo_model_activation.py, tests/test_wnba_model_activation.py, tests/test_womens_college_basketball_model_activation.py`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_activation_tiers.py`

- imports_from: `src.analytics.model_governance.activation_tiers`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_advanced_red_team.py`

- imports_from: `src.analytics.advanced_red_team_report, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_afl_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_alert_engine.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_alert_gate.py`

- imports_from: `src.analytics.model_governance.alert_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_analyze_event.py`

- imports_from: `src.api.schemas.betting_actions, src.services.action_betting_service`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_arbitrage_detector.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_arbitrage_draw_market.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_arbitrage_exchange.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_arbitrage_prediction_market.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_arbitrage_risk_filters.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_arbitrage_three_way.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_arbitrage_two_way.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_asof_line_movement_query.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_audit_log.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_automation_scheduler_endpoints.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_automation_scheduler_scripts.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `scripts/run_scheduler_health_check.ps1, scripts/run_scheduler_once.ps1`

## `tests/test_backtest_dataset_builder.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_backtest_gate.py`

- imports_from: `src.analytics.model_governance.backtest_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_backtest_leakage.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_backtest_regression_strategy.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_backtest_schema.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_backtest_strategy_bankroll.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_backtest_strategy_profiles.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_backtesting.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_backtesting_engine.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_badminton_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_balance_sheet_risk.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_bankroll_state.py`

- imports_from: `src.backtesting.bankroll_state`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `data/bankroll/test_bankroll.json, data/bankroll/test_bankroll_redact.json`

## `tests/test_baseball_impact_intelligence.py`

- imports_from: `src.market_intelligence.response_compactor, src.market_intelligence.sports, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_basketball_player_impact.py`

- imports_from: `src.market_intelligence.basketball_player_impact, src.market_intelligence.basketball_player_impact_readiness, src.market_intelligence.response_compactor, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_bet_log.py`

- imports_from: `src.services.bet_log, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_bookmaker_normalizer.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_broker_quality_scoring.py`

- imports_from: `src.services.execution_service`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_budget_gates.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_cadence_controller.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_calibration.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_calibration_collector.py`

- imports_from: `src.services.prediction_market_runtime_bridge, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_calibration_gate.py`

- imports_from: `src.analytics.model_governance.calibration_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_calibration_strategy_filter.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_calibration_tracker.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_call_of_duty_esports_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_candlestick_pattern_detector.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_champion_challenger.py`

- imports_from: `src.analytics.model_governance.champion_challenger`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_clv_tracker.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_collector_scheduled_runner.py`

- imports_from: `src.services.streamlit_dashboard_facade, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_college_football_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_combat_impact_intelligence.py`

- imports_from: `src.market_intelligence.response_compactor, src.market_intelligence.sports, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_combat_sports_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_cricket_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_cross_book_gate.py`

- imports_from: `src.analytics.model_governance.cross_book_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_cross_book_line_comparator.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_crypto_edge_lab_registry.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_cs2_esports_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_darts_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_data_availability_tiers.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_data_intelligence_stack.py`

- imports_from: `src.analytics.intelligence_readiness_report, src.market_intelligence.cross_asset_intelligence_router, src.market_intelligence.response_compactor, src.research, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_data_lineage.py`

- imports_from: `src.analytics.model_governance.data_lineage`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_data_paths.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_data_quality_monitor.py`

- imports_from: `src.analytics.model_governance.data_quality_monitor`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_data_source_endpoints.py`

- imports_from: `src.data, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_data_source_registry.py`

- imports_from: `src.data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_data_source_research_lanes.py`

- imports_from: `src.data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_deepseek_data_pull_check_contract.py`

- imports_from: `src.ai.deepseek_data_pull_check, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_deepseek_profit_lab.py`

- imports_from: `src.ai.deepseek_profit_lab, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_deepseek_reviewer.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_derived_feature_backfill_report.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_derived_feature_planner.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_dota2_esports_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_drawdown_controls.py`

- imports_from: `src.core.drawdown_controls`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_ev_line_shopper.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_evaluate_lines.py`

- imports_from: `src.core.quant_engine, src.services.bet_decision_engine`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_execution_later_gate.py`

- imports_from: `src.analytics.model_governance.execution_later_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_experiment_history_store.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_experiment_report_exporter.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_exposure_limits.py`

- imports_from: `src.core.exposure_limits`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_extreme_randomness_diagnostics.py`

- imports_from: `src.market_intelligence.response_compactor, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_feature_ablation_lab.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_field_scorecard.py`

- imports_from: `src.analytics.field_scorecard`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_football_impact_intelligence.py`

- imports_from: `src.analytics.football_impact_report, src.market_intelligence.response_compactor, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_formula_1_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_formula_e_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_golf_impact_intelligence.py`

- imports_from: `src.market_intelligence.response_compactor, src.market_intelligence.sports, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_golf_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_governance_audit_log.py`

- imports_from: `src.analytics.model_governance.governance_audit_log`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_governance_config.py`

- imports_from: `src.analytics.model_governance.governance_config`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_governance_health.py`

- imports_from: `src.analytics.governance`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_governance_report.py`

- imports_from: `src.analytics.reports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_handball_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_historical_backtest_bridge.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_historical_data_sources.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_historical_line_movement.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_historical_odds_importers.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_historical_odds_sqlite.py`

- imports_from: `src.data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_historical_replay.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_hockey_impact_intelligence.py`

- imports_from: `src.market_intelligence.response_compactor, src.market_intelligence.sports, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_human_approval_gate.py`

- imports_from: `src.analytics.model_governance.human_approval_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_indycar_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_injury_weather_adapter_contract.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_input_quality_gate.py`

- imports_from: `src.analytics.model_governance.input_quality_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_alternative_investments.py`

- imports_from: `src.analytics.institutional.alternative_investments`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_audit_ledger.py`

- imports_from: `src.services.ledger_service`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_credit_risk_models.py`

- imports_from: `src.analytics.institutional.credit_risk_models`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_cross_asset_adapters.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_cross_asset_calibration.py`

- imports_from: `src.analytics.institutional_cross_asset_calibration`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_cross_asset_lab.py`

- imports_from: `src.core.stake_sizing_simulator, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_cross_asset_reports.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_cross_asset_scores.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_deepseek_review.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_derivatives_hedging.py`

- imports_from: `src.analytics.institutional.derivatives_hedging`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_execution_cost_models.py`

- imports_from: `src.analytics.institutional.execution_cost_models`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_execution_desk.py`

- imports_from: `src.services.execution_service`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_factor_risk_models.py`

- imports_from: `src.analytics.institutional.factor_risk_models`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_fixed_income_rates.py`

- imports_from: `src.analytics.institutional.fixed_income_rates`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_liability_retirement_models.py`

- imports_from: `src.analytics.institutional.liability_retirement_models`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_macro_regime_models.py`

- imports_from: `src.analytics.institutional.macro_regime_models`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_model_governance.py`

- imports_from: `src.analytics.institutional.model_governance`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_model_router.py`

- imports_from: `src.analytics.institutional, src.analytics.institutional.model_router, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_performance_attribution.py`

- imports_from: `src.analytics.institutional.performance_attribution`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_portfolio_construction.py`

- imports_from: `src.analytics.institutional.portfolio_construction`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_risk_engine.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_stock_pro_analyst_registry.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_institutional_tax_aware_models.py`

- imports_from: `src.analytics.institutional.tax_aware_models`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_kalshi_adapter_contract.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_kalshi_market_provider.py`

- imports_from: `src.providers.prediction_markets, src.providers.registry, src.services.prediction_market_runtime_bridge, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_kalshi_monitor.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_kalshi_provider_shape_contract.py`

- imports_from: `src.market_intelligence.response_compactor, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_kalshi_readonly_adapter.py`

- imports_from: `src.connectors.errors, src.connectors.prediction_market_data, src.providers.prediction_markets`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.prediction_market_data, src.providers.prediction_markets, src.services.prediction_market_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_kalshi_readonly_readiness_contract.py`

- imports_from: `src.services.prediction_market_runtime_bridge, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_kalshi_scoring.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_kelly_gate.py`

- imports_from: `src.analytics.model_governance.kelly_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_kelly_staking.py`

- imports_from: `src.core.kelly_staking, src.core.stake_confidence`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_lacrosse_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_later_auto_execution_policy.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_league_of_legends_esports_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_line_movement_data_quality_dashboard.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_line_movement_import_contract.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_line_movement_readiness.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_liquidity_context_scoring.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_liquidity_risk.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_live_smoke_payload_contract.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_local_sports_history_audit.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_market_clock.py`

- imports_from: `src.core.market_clock`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_market_feature_packs.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_market_identity_resolver.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_market_research_store.py`

- imports_from: `src.research.storage`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_market_state_manifold.py`

- imports_from: `src.analytics.manifold_calibration, src.market_intelligence.cross_asset_manifold_router, src.market_intelligence.response_compactor, src.services.execution_service, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_market_structure.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_mens_college_basketball_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_middle_alt_line.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_middle_ev_simulator.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_middle_key_number.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_middle_opportunity_detector.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_middle_prop.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_middle_push_corridor.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_middle_spread.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_middle_team_total.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_middle_total.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_mlb_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_model_card.py`

- imports_from: `src.analytics.model_governance.model_card`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_model_drift_monitor.py`

- imports_from: `src.analytics.model_governance.model_drift_monitor`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_model_input_coverage.py`

- imports_from: `src.market_intelligence.model_input_coverage, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_model_inventory.py`

- imports_from: `src.analytics.model_governance.model_inventory`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_model_performance_report.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_model_probability.py`

- imports_from: `src.core.model_probability, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_model_recheck_runner.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, src.services.model_recheck_runner`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_model_router.py`

- imports_from: `src.analytics.model_governance.model_router`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_model_router_registry.py`

- imports_from: `src.analytics.model_governance.model_router_registry`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_model_validation_report.py`

- imports_from: `src.analytics.reports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_motogp_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_multi_sport_model_registry.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nascar_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nba_model_activation.py`

- imports_from: `src.services.full_board_engine, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_ncaaf_collegefootballdata_adapter.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_news_event_monitor.py`

- imports_from: `src.market_intelligence.news_event_monitor, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_news_events_adapter_contract.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_coaching_adapters.py`

- imports_from: `src.providers.nfl_coaching_adapters, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_coaching_feature_builders.py`

- imports_from: `src.market_intelligence.nfl_coaching_feature_builders, src.providers.nfl_coaching_adapters, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_coaching_sources.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_cutoff_week_features.py`

- imports_from: `src.market_intelligence.nfl_cutoff_week_features`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_historical_pattern_lab.py`

- imports_from: `src.data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_historical_pattern_validation.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_open_data_adapters.py`

- imports_from: `src.providers.nfl_open_data_adapters, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_open_data_backfill.py`

- imports_from: `src.providers.nfl_open_data_adapters, src.providers.nfl_open_data_backfill, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_open_data_feature_builders.py`

- imports_from: `src.providers.nfl_open_data_feature_readiness, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_open_data_field_catalog.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_open_data_sources.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nfl_source_exhaustion.py`

- imports_from: `src.data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_nhl_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_no_vig_pricing.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_odds_line_monitor.py`

- imports_from: `src.data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_odds_math.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_open_sports_history_backfill.py`

- imports_from: `src.data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_open_sports_history_derived_features.py`

- imports_from: `src.analytics.derived_feature_backfill_report, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_open_sports_history_import.py`

- imports_from: `src.data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_open_sports_history_sources.py`

- imports_from: `src.data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_opportunity_scoring.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_ops_scripts_contract.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_ops_workflow.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_outcome_import_endpoint.py`

- imports_from: `src.services.streamlit_dashboard_facade, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_outcome_migration.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_outcome_reconciliation.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_outcome_store.py`

- imports_from: `src.services.settlement_service, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_overwatch_esports_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_paper_decision_ledger.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_paper_trade_ledger.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_pattern_calibration.py`

- imports_from: `src.market_intelligence.response_compactor, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_pattern_review_queue.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_performance_metrics.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k0_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k2_sports_snapshot_pipeline.py`

- imports_from: `src.data, src.research.storage`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k3_runtime_csv_migration_plan.py`

- imports_from: `src.research.storage`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k4_0dte_options_schema_foundation.py`

- imports_from: `src.research.storage`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k5_core_arbitrage_engine.py`

- imports_from: `src, src.core, src.core.math_utils, src.market_intelligence.arbitrage.two_way_arbitrage, src.research, src.research.storage, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k6a_frontend_readiness_gate_inspection.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k6b_dashboard_navigation_plan_contract.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k6c_controlled_ui_shell.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k6d_readiness_gate_display_contract.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k6e_readiness_display_data_helper.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k6f_readiness_display_payload_builder.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k6g_readiness_display_renderer_contract.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k6h_readiness_display_renderer_helper.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `PHASE10K6H_READINESS_DISPLAY_RENDERER_HELPER.md, src/services/streamlit_dashboard_data.py, streamlit_app.py`

## `tests/test_phase10k6i_controlled_navigation_shell.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k6j_controlled_readiness_ui_wiring.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k6k_controlled_dashboard_shell_review.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k7a_full_suite_readiness_ownership_map.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `PHASE10K7A_FULL_SUITE_READINESS_OWNERSHIP_MAP.md, src/services/streamlit_dashboard_data.py, streamlit_app.py`

## `tests/test_phase10k7b_test_guardrail_stabilization.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `PHASE10K7B_TEST_GUARDRAIL_STABILIZATION.md, tests/test_phase10k6k_controlled_dashboard_shell_review.py`

## `tests/test_phase10k7c_full_suite_readiness_gate_matrix.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `PHASE10K7C_FULL_SUITE_READINESS_GATE_MATRIX.md, src/services/streamlit_dashboard_data.py, streamlit_app.py, tests/test_phase10k6k_controlled_dashboard_shell_review.py`

## `tests/test_phase10k7d_10k8_prediction_testing_entry_contract.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `PHASE10K7D_10K8_PREDICTION_TESTING_ENTRY_CONTRACT.md, src/services/streamlit_dashboard_data.py, streamlit_app.py, tests/test_phase10k6k_controlled_dashboard_shell_review.py`

## `tests/test_phase10k8a_paper_only_prediction_testing_owner_scan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `PHASE10K8A_PAPER_ONLY_PREDICTION_TESTING_OWNER_SCAN.md, src/services/streamlit_dashboard_data.py, streamlit_app.py, tests/test_phase10k6k_controlled_dashboard_shell_review.py`

## `tests/test_phase10k8b_paper_only_fixture_testing_contract.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `PHASE10K8B_PAPER_ONLY_FIXTURE_TESTING_CONTRACT.md, src/services/streamlit_dashboard_data.py, streamlit_app.py, tests/test_phase10k6k_controlled_dashboard_shell_review.py`

## `tests/test_phase10k8c_paper_only_fixture_validation_helper.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `PHASE10K8C_PAPER_ONLY_FIXTURE_VALIDATION_HELPER.md, src/backtesting/backtest_dataset_builder.py, src/services/streamlit_dashboard_data.py, streamlit_app.py, tests/test_phase10k6k_controlled_dashboard_shell_review.py`

## `tests/test_phase10k8d_paper_only_fixture_readiness_payload_adapter.py`

- imports_from: `src.services.streamlit_dashboard_data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8e_paper_only_fixture_evaluation_contract.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8f_paper_only_fixture_evaluation_helper.py`

- imports_from: `src.core.quant_engine, src.services.streamlit_dashboard_data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8g_paper_only_evaluation_readiness_adapter.py`

- imports_from: `src.core.quant_engine, src.services.streamlit_dashboard_data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8h_paper_only_fixture_pipeline_contract.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8i_paper_only_fixture_pipeline_helper.py`

- imports_from: `src.services.streamlit_dashboard_data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8j_controlled_pipeline_smoke_review.py`

- imports_from: `src.services.streamlit_dashboard_data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8k_prediction_testing_readiness_review.py`

- imports_from: `src.services.streamlit_dashboard_data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8l_controlled_multi_market_test_mode_ui.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8m_strict_model_field_baseline_by_market_and_sport.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8n_controlled_field_catalog_ui_review.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8o_dedicated_0dte_paper_fixture_template.py`

- imports_from: `src.data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8p_dedicated_0dte_fixture_validation_adapter.py`

- imports_from: `src.data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8q_dedicated_0dte_validation_readiness_payload.py`

- imports_from: `src.data, src.services.streamlit_dashboard_data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8r_dedicated_0dte_validation_readiness_ui.py`

- imports_from: `src.data, src.services.streamlit_dashboard_data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8s_dedicated_0dte_paper_evaluation_adapter.py`

- imports_from: `src.data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8t_dedicated_0dte_evaluation_readiness_payload.py`

- imports_from: `src.data, src.services.streamlit_dashboard_data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8u_dedicated_0dte_evaluation_ui.py`

- imports_from: `src.data, src.services.streamlit_dashboard_data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8v_full_0dte_paper_pipeline_adapter.py`

- imports_from: `src.data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8w_full_0dte_paper_pipeline_ui.py`

- imports_from: `src.data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8x_controlled_0dte_paper_run_smoke_review.py`

- imports_from: `src.data, src.services.streamlit_dashboard_data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8y_0dte_prediction_testing_readiness_review.py`

- imports_from: `src.data, src.services.streamlit_dashboard_data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8z0_deployment_governance.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.adapter_readiness, src.brokerage.approval, src.brokerage.approval_evidence, src.brokerage.client_factory, src.brokerage.credential_readiness, src.brokerage.kill_switch, src.brokerage.monitoring, src.brokerage.rollback`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8z_final_controlled_prediction_testing_freeze.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8za_0dte_data_field_formula_coverage_audit.py`

- imports_from: `src.data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zb0_product_contract_reset.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zb_0dte_field_formula_gap_patch.py`

- imports_from: `src.data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zc_dashboard_product_lane_cleanup.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zd_orb_strategy_research_integration_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8ze_institutional_market_metric_catalog.py`

- imports_from: `src.data, src.services.streamlit_dashboard_data, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf0_canonical_research_backtest_workflow_migration_plan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf0a_frozen_test_contract_reset.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf1_compatibility_alias_migration.py`

- imports_from: `src.data, src.services.streamlit_dashboard_data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf2_production_symbol_migration.py`

- imports_from: `src.data, src.services.streamlit_dashboard_data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf3_product_ui_language_finalization.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf4_asset_grade_repo_clean_inventory.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf5_universal_runtime_ownership_map.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf6_r2_object_storage_archive_contract.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf7_r2_archive_pipeline.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf8_r2_transfer_proof_report.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf9_full_r2_transfer_report.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf9b_batch_safe_remaining_transfer.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf9c_headerless_csv_final_deletion.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zf9d_final_data_inventory_reconciliation.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfe1_universal_product_language_alignment.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfe2_daily_data_hygiene_scheduler.py`

- imports_from: `scripts.daily_data_hygiene`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfe_duplicate_code_evidence_scan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zff_canonical_owner_decision_report.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfg_safe_migration_batch_1.py`

- imports_from: `src.core, src.core.math_utils, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfh_safe_migration_batch_2_boundary_guards.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfi_automation_scheduler_decomposition_plan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfj_provider_live_market_decomposition_plan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfk_test_suite_cleanup_plan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfo_src_providers_skeleton.py`

- imports_from: `src.providers.contracts, src.providers.health, src.providers.normalization, src.providers.registry`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfp_provider_taxonomy_correction.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfr_production_module_boundaries.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfs_legacy_vendor_transport_batch_plan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zft_provider_foundation_transport.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.providers.base, src.providers.contracts, src.providers.kalshi_adapter_contract, src.providers.normalization, src.providers.policy.allowlist, src.providers.registry, src.providers.sportsbook_adapter_contract, src.providers.validation`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfu_provider_foundation_completion.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfw_runtime_provider_migration_batch_2.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfx_connector_boundary_isolation.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfy_prediction_market_connector_batch_1.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.prediction_market_data`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zfz_odds_data_connector_batch_2.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.odds_data, src.services.enrichment_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zg0_market_data_connector_batch_3.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.market_data, src.connectors.odds_data, src.connectors.prediction_market_data`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zg1_zero_dte_stocks_provider_batch.py`

- imports_from: `src.providers.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.market_data, src.connectors.odds_data, src.connectors.prediction_market_data, src.providers.zero_dte_stocks`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zg2_legacy_deletion_readiness_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zg3_wrapper_import_redirection.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zg4_runtime_bridge_import_redirection.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.providers.provider_router`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zg5_provider_router_independence.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.providers.provider_router`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zg6_legacy_provider_router_delete_proof.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.providers.provider_router`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zg7_legacy_provider_router_deletion.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.providers.provider_router`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zg8_provider_foundation_deletion_proof.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zg9_provider_foundation_thin_wrapper_deletion.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zga_provider_registry_runtime_blocker.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.providers.kalshi_readonly_readiness, src.providers.registry, src.services.automation_scheduler_facade, src.services.cadence_controller, src.services.scheduler_config`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgb_provider_write_firewall_runtime_blocker.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.readiness, src.providers.policy.write_firewall`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgc_final_provider_foundation_blocker_proof.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.readiness, src.providers.policy.write_firewall, src.providers.registry, src.services.automation_scheduler_facade`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgd_final_provider_foundation_blocker_deletion.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.providers.policy.write_firewall, src.providers.registry, src.services.automation_scheduler_facade`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zge_broader_legacy_runtime_owner_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgf_live_client_connector_isolation_proof.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.errors, src.connectors.prediction_market_data, src.connectors.prediction_market_data.auth, src.connectors.prediction_market_data.configuration, src.connectors.prediction_market_data.disabled_client, src.connectors.prediction_market_data.readiness, src.connectors.prediction_market_data.signing, src.connectors.prediction_market_data.transport`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.errors, src.connectors.odds_data, src.connectors.odds_data.auth, src.connectors.odds_data.configuration, src.connectors.odds_data.disabled_client, src.connectors.odds_data.live_client, src.connectors.odds_data.readiness, src.connectors.odds_data.source_profile, src.connectors.odds_data.transport`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.errors, src.connectors.odds_data`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.errors, src.connectors.odds_data, src.providers.sportsbooks, src.providers.sportsbooks.adapters, src.services.odds_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.errors, src.connectors.odds_data, src.services.odds_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.errors, src.connectors.odds_data, src.services.odds_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgm_odds_historical_test_redirection.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.errors, src.connectors.odds_data, src.services.odds_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgn_odds_proof_history_cleanup.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.errors, src.connectors.odds_data, src.services.odds_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgo_odds_compatibility_test_retirement.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.errors, src.connectors.odds_data, src.providers.sportsbooks.adapters, src.services.odds_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.errors, src.connectors.odds_data, src.providers.sportsbooks.adapters, src.services.odds_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.services.enrichment_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.services.prediction_market_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.prediction_market_data, src.providers.prediction_markets, src.services.prediction_market_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.analytics.calibration_collector, src.connectors.odds_data, src.connectors.prediction_market_data, src.market_intelligence.prediction_market_outcome_candidates, src.providers.kalshi_readonly_readiness, src.providers.prediction_markets, src.providers.sportsbooks, src.services.automation_scheduler_facade, src.services.odds_runtime_bridge, src.services.prediction_market_runtime_bridge, src.services.scheduler_runner, src.services.settlement_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.analytics.calibration_collector, src.connectors.odds_data, src.connectors.prediction_market_data, src.market_intelligence.prediction_market_outcome_candidates, src.providers.kalshi_readonly_readiness, src.providers.prediction_markets, src.providers.sportsbooks, src.services.odds_runtime_bridge, src.services.prediction_market_runtime_bridge, src.services.scheduler_runner, src.services.settlement_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.prediction_market_data, src.providers.prediction_markets, src.services.prediction_market_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.odds_data, src.connectors.prediction_market_data, src.providers.prediction_markets, src.providers.sportsbooks, src.services.odds_runtime_bridge, src.services.prediction_market_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.prediction_market_data, src.providers.prediction_markets, src.services.prediction_market_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgy_prediction_market_shell_deletion.py`

- imports_from: `src.connectors.errors`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.connectors.prediction_market_data, src.providers.prediction_markets, src.services.prediction_market_runtime_bridge`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zgz_post_provider_connector_cleanup_freeze.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zh0_core_engine_extraction_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zh1_core_math_foundation_batch.py`

- imports_from: `src.core.math_utils`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zh2_risk_foundation_batch.py`

- imports_from: `src.core.risk`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zh3_game_theory_execution_edge_plan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zh4_core_pricing_extraction.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `market_pricing, quant_engine, src.core.pricing`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zh5_core_probability_extraction.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `model_probability, src.core.probability`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zh6_portfolio_foundation.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.core.portfolio`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zh7_execution_game_theory_foundation.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.core.execution, src.core.game_theory, src.core.market_impact`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zh8_decision_engine_service_plan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zh9_core_engine_compatibility_wrappers.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.core.market_pricing, src.core.model_probability, src.core.pricing, src.core.probability, src.core.quant_engine, src.core.risk, src.core.risk_engine, src.services.bet_decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zha_core_engine_migration_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhb_service_layer_ownership_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhc_screenshot_workflow_thinning_plan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.services.screenshot_intake`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhd_decision_and_bet_log_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `bet_decision_engine, bet_log, src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhe_api_layer_ownership_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.api.model_card_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhf_dashboard_entrypoint_ownership_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhg_automation_scheduler_decommission_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhh_service_api_dashboard_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhi_legacy_full_gate_remediation.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.api.model_backtest_routes, src.core.backtester, src.core.math_utils, src.core.risk, src.services.model_backtest_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhj_data_foundation.py`

- imports_from: `src.data, src.data.validation`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhk_backtesting_foundation.py`

- imports_from: `src.backtesting.datasets, src.backtesting.leakage, src.backtesting.replay, src.backtesting.simulation`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhl_legacy_data_backtesting_owner_map.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhm_data_backtesting_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.api.model_backtest_routes, src.api.performance_routes, src.backtesting, src.core.backtester, src.data, src.services.model_backtest_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhn_analytics_foundation.py`

- imports_from: `src.analytics`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zho_research_foundation.py`

- imports_from: `src.research`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhp_legacy_analytics_research_owner_map.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.analytics, src.research`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhq_analytics_research_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.analytics, src.research`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhr_analytics_migration_batch_1.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.analytics.reports`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhs_research_migration_batch_1.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.research.storage`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zht_analytics_research_batch_1_legacy_scan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhu_analytics_research_batch_1_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhv_analytics_downstream_redirection.py`

- imports_from: `src.analytics.governance, src.analytics.model_governance, src.analytics.reports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhw_research_downstream_redirection.py`

- imports_from: `src.research`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhx_analytics_research_batch_2_legacy_scan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhy_analytics_research_batch_2_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhz_analytics_research_reference_scan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhz_analytics_research_wrapper_delete_proof.py`

- imports_from: `src.analytics.model_governance`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.analytics, src.research`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zhz_scheduler_coupled_research_blockers.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zi0_analytics_research_delete_proof_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zi1_analytics_research_compatibility_test_retirement.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.analytics, src.research`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zi2_research_store_ownership_migration.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.research.storage`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zi3_model_maturity_registry_decoupling.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.research`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zi4_final_analytics_research_delete_readiness.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `model_governance, src.analytics, src.research`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zi5_analytics_research_wrapper_deletion.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.analytics, src.analytics.model_governance, src.research`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zi6_ai_llm_boundary_audit.py`

- imports_from: `src.ai`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zi7_ai_boundary_scaffold.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.ai, src.ai.contracts, src.ai.disabled_client, src.ai.prompt_policy, src.ai.readiness`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zi8_ai_scheduler_blocker_map.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zi9_ai_boundary_checkpoint.py`

- imports_from: `src.ai`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zia_execution_scheduler_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zib_unified_brokerage_boundary.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage, src.brokerage.contracts, src.brokerage.execution, src.brokerage.ledger, src.brokerage.orders, src.brokerage.positions, src.brokerage.readiness`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zic_execution_ownership_migration.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zid_execution_final_delete_readiness.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage, src.brokerage.execution, src.brokerage.ledger, src.brokerage.orders, src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine, tempfile`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zie_execution_scheduler_wrapper_deletion.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage, src.brokerage.execution`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zif_execution_boundary_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage, src.brokerage.execution, src.brokerage.readiness, src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zig_execution_blocker_remediation_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage, src.brokerage.execution, src.brokerage.ledger, src.brokerage.orders, src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.brokerage.settlement, src.services.bet_decision_engine, src.services.bet_log, src.services.decision_engine, src.services.settlement_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zih_execution_blocker_canonicalization.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage, src.brokerage.execution, src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine, tempfile`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zii_execution_blocker_final_delete_readiness.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zij_execution_blocker_wrapper_deletion.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage, src.brokerage.execution, src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zik_execution_remediation_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage, src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zil_settlement_canonicalization.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.settlement, src.services.settlement_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zim_ledger_canonicalization.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.services.ledger_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zin_strategy_execution_helper_canonicalization.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.services.execution_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zio_execution_helper_final_delete_readiness.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.settlement, src.services.execution_service, src.services.ledger_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `FINAL_EXECUTION_HELPER_DELETE_DECISION_AFTER_10K8ZIO.md, PHASE10K8ZIO_EXECUTION_HELPER_FINAL_DELETE_READINESS.md`

## `tests/test_phase10k8zip_execution_helper_canonicalization_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.settlement, src.services.execution_service, src.services.ledger_service, src.services.settlement_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `PHASE10K8ZIP_EXECUTION_HELPER_CANONICALIZATION_CHECKPOINT.md`

## `tests/test_phase10k8ziq_execution_helper_reference_redirection_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zir_execution_helper_runtime_redirection.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zis_execution_helper_test_redirection.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zit_execution_helper_final_delete_proof.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8ziu_execution_helper_wrapper_deletion.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage, src.brokerage.execution, src.brokerage.ledger, src.brokerage.orders, src.brokerage.readiness, src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8ziv_execution_helper_deletion_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8ziw_final_execution_blocker_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage, src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zix_final_execution_blocker_canonicalization.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine, src.services.execution_service, src.services.ledger_service`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8ziy_final_execution_test_redirection.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8ziz_final_execution_blocker_delete_proof.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zj0_final_execution_blocker_deletion.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage, src.brokerage.readiness, src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zj1_execution_cleanup_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage, src.brokerage.paper_decision_ledger, src.brokerage.paper_trade_ledger, src.brokerage.readiness, src.services.decision_engine`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zj2_broker_account_boundary_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zj3_disabled_broker_account_boundary.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zj4_live_ledger_persistence_boundary_plan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zj5_production_approval_gate_plan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zj6_live_trading_readiness_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zj7_approval_gate_scaffold.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zj8_broker_client_factory_scaffold.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zj9_live_submit_interface_scaffold.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zja_live_reconciliation_ledger_scaffold.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjb_kill_switch_rollback_scaffold.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjc_live_activation_scaffold_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjd_broker_adapter_protocol.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zje_sandbox_broker_boundary.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjf_credential_activation_boundary.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjg_sandbox_submit_flow.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjh_production_activation_blocker_audit.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zji_sandbox_activation_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjj_activation_gate_verification.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.approval, src.brokerage.kill_switch`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjk_broker_adapter_readiness.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjl_credential_readiness_verification.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjm_live_submit_readiness_verification.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.approval, src.brokerage.client_factory, src.brokerage.ledger, src.brokerage.live_submit, src.brokerage.orders`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjn_monitoring_rollback_readiness.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.kill_switch, src.brokerage.rollback`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjo_controlled_activation_readiness_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.accounts, src.brokerage.activation, src.brokerage.adapter_readiness, src.brokerage.approval, src.brokerage.client_factory, src.brokerage.credential_readiness, src.brokerage.credentials, src.brokerage.deployment_readiness, src.brokerage.execution, src.brokerage.kill_switch, src.brokerage.ledger, src.brokerage.live_ledger, src.brokerage.live_reconciliation, src.brokerage.live_submit, src.brokerage.monitoring, src.brokerage.orders, src.brokerage.readiness, src.brokerage.reconciliation, src.brokerage.rollback, src.brokerage.submit_readiness`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjp_approval_evidence.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjq_sandbox_activation_composition.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.approval_evidence`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjr_dry_run_submit_proof.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjs_dry_run_ledger_verification.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjt_final_sandbox_activation_proof.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjv_operator_approval_interface.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.approval`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjw_approval_audit_layer.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjx_sandbox_enablement_layer.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.activation, src.brokerage.approval, src.brokerage.approval_evidence, src.brokerage.client_factory, src.brokerage.credential_readiness, src.brokerage.deployment_readiness, src.brokerage.kill_switch, src.brokerage.monitoring, src.brokerage.rollback`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjy_sandbox_adapter_stub.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zjz_kill_switch_governance.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk1_controlled_sandbox_governance_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.approval, src.brokerage.approval_audit, src.brokerage.client_factory, src.brokerage.deployment_policy, src.brokerage.execution, src.brokerage.kill_switch_policy, src.brokerage.live_submit, src.brokerage.operator, src.brokerage.orders, src.brokerage.readiness, src.brokerage.sandbox_adapter, src.brokerage.sandbox_enablement`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `PHASE10K8ZK1_CONTROLLED_SANDBOX_GOVERNANCE_CHECKPOINT.md`

## `tests/test_phase10k8zk2_credential_sdk_network_freeze.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.credential_readiness`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk2_final_live_trading_disabled_proof.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.accounts, src.brokerage.approval, src.brokerage.client_factory, src.brokerage.credential_loader, src.brokerage.credentials, src.brokerage.deployment_readiness, src.brokerage.kill_switch, src.brokerage.live_ledger, src.brokerage.live_reconciliation, src.brokerage.live_submit, src.brokerage.orders`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk2_final_system_freeze.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk2_production_activation_readiness_ledger.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.accounts, src.brokerage.approval, src.brokerage.client_factory, src.brokerage.credential_readiness, src.brokerage.deployment_readiness, src.brokerage.kill_switch, src.brokerage.live_ledger, src.brokerage.live_reconciliation, src.brokerage.live_submit, src.brokerage.monitoring, src.brokerage.orders, src.brokerage.rollback`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk3_final_production_readiness_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk4_architecture_invariants.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.brokerage.approval, src.brokerage.client_factory, src.brokerage.live_submit`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk4_operator_implementation_plan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk4_project_completion_status.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk4_rollout_plan.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk5_automation_scheduler_full_inventory.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk6_automation_scheduler_ownership_migration.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk7_automation_scheduler_runtime_redirection.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk8_automation_scheduler_test_redirection.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zk9_automation_scheduler_final_delete_proof.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zl0_automation_scheduler_deletion.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zl1_automation_scheduler_decommission_checkpoint.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zl2_market_intelligence_foundation.py`

- imports_from: `src.market_intelligence`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zl3_sports_intelligence_absorption.py`

- imports_from: `src.market_intelligence.sports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zl4_prediction_market_intelligence_absorption.py`

- imports_from: `src.market_intelligence.manifold, src.market_intelligence.prediction_markets`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zl5_options_0dte_gex_vanna_foundation.py`

- imports_from: `src.market_intelligence.options`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zl6_market_intelligence_runtime_test_redirection.py`

- imports_from: `src.market_intelligence, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zl7_market_intelligence_scheduler_deletion.py`

- imports_from: `src.market_intelligence`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zl8_market_intelligence_absorption_checkpoint.py`

- imports_from: `src.market_intelligence`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zl9a_automation_scheduler_runtime_import_removal.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `src.api.automation_security, src.brokerage.readiness_support, src.services.automation_scheduler_facade, src.services.execution_support, src.services.ledger_support, src.services.settlement_support, src.services.streamlit_dashboard_facade`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `main.py, src/api/automation_review_outcomes_routes.py, src/api/provider_status_routes.py, src/automation_scheduler_legacy/__init__.py, src/brokerage/readiness.py, src/services/execution_service.py, src/services/ledger_service.py, src/services/settlement_service.py, streamlit_app.py`

## `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`

- imports_from: `src.backtesting.dataset_builder, src.backtesting.engine, src.backtesting.strategy_profiles, src.data, src.data.historical_odds, src.data.historical_sources, src.data.line_movement, src.data.source_event_links, src.market_intelligence.feature_packs, src.research.feature_control`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zmh_automation_scheduler_final_removal_attempt.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zmi_streamlit_dashboard_test_import_redirection.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zmj_sports_impact_test_import_redirection.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zmr_security_policy_secret_safety_migration.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zms_security_cluster_migration.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase10k8zt_provider_security_surface_retirement.py`

- imports_from: `src.providers.policy, src.providers.policy.allowlist, src.security, src.security.owner_approval_gate, src.security.risk_limit_guard`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase1_legacy_inventory.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_phase_x_non_src_inventory.py`

- imports_from: `src.services.repo_inventory`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_pickleball_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_player_prop_monitor.py`

- imports_from: `src.market_intelligence.player_prop_monitor, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_player_props_adapter_contract.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_price_event.py`

- imports_from: `src.core.market_pricing, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_promotion_gate.py`

- imports_from: `src.analytics.model_governance.promotion_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_provider_adapter_base.py`

- imports_from: `src.providers.base, src.providers.contracts`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_provider_contracts.py`

- imports_from: `src.providers.contracts`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_provider_health.py`

- imports_from: `src.providers.contracts, src.providers.health`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_provider_normalization_contract.py`

- imports_from: `src.providers.normalization, src.providers.sportsbooks`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_provider_payload_validator.py`

- imports_from: `src.providers.validation`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_provider_registry.py`

- imports_from: `src.providers.registry`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_provider_secret_policy.py`

- imports_from: `src.providers.policy.secret_policy`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_quant_engine_foundation.py`

- imports_from: `src.core.quant_engine`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_repo_architecture_guard.py`

- imports_from: `none`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_report_writer.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_research_evidence_gate.py`

- imports_from: `src.analytics.model_governance.research_evidence_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_response_compactor.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_review_queue.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_review_queue_gate.py`

- imports_from: `src.analytics.model_governance.review_queue_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_risk_gate.py`

- imports_from: `src.analytics.model_governance.risk_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_risk_of_ruin.py`

- imports_from: `src.core.risk_of_ruin`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_rugby_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_run_context.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_scheduler_config.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_scheduler_runner.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_screenshot_analysis.py`

- imports_from: `src.providers.prediction_markets, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_screenshot_normalization_parity.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_security_framework.py`

- imports_from: `src.brokerage.readiness, src.providers.policy.write_firewall, src.services.ledger_service, src.services.streamlit_dashboard_facade, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_settlement_discovery.py`

- imports_from: `src.services.settlement_service`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_settlement_liquidity_gate.py`

- imports_from: `src.analytics.model_governance.settlement_liquidity_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_settlement_rule_checker.py`

- imports_from: `src.brokerage.settlement`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_sharp_cross_book_review_queue.py`

- imports_from: `src.market_intelligence.response_compactor, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_sharp_scheduler_flow.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_sharp_sportsbook_adapter.py`

- imports_from: `src.connectors.errors, src.connectors.odds_data, src.providers.sportsbooks.adapters, src.services.odds_runtime_bridge`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_small_account_endpoints.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_small_account_strategy.py`

- imports_from: `src.services.execution_service, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_snapshot_store.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_snooker_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_soccer_impact_intelligence.py`

- imports_from: `src.market_intelligence.response_compactor, src.market_intelligence.sports, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_soccer_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_source_event_link_resolver.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_source_quality_scoring.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_sport_analysis_endpoint.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_sport_feature_packs.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_sport_model_routing.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_sportsbook_adapter_contract.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_sportsbook_odds_provider.py`

- imports_from: `src.connectors.odds_data, src.providers.registry, src.providers.sportsbooks.contracts, src.services.odds_runtime_bridge, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `src/services/odds_runtime_bridge.py`

## `tests/test_stake_confidence.py`

- imports_from: `src.core.stake_confidence`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_stake_sizing_simulator.py`

- imports_from: `src.core.stake_sizing_simulator`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_status_classifier.py`

- imports_from: `src.analytics.model_governance.status_classifier`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_stock_fundamentals_adapter_contract.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_stock_monitor.py`

- imports_from: `src.providers.stock_monitor, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_stock_price_adapter_contract.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_strategy_framework.py`

- imports_from: `src.brokerage.readiness, src.core.strategy_disagreement, src.core.strategy_promotion, src.core.strategy_score_aggregator, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_streamlit_dashboard_data.py`

- imports_from: `src.data.historical_odds, src.data.line_movement, src.research.history, src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `streamlit_app.py`

## `tests/test_synthetic_line_movement_sandbox.py`

- imports_from: `src.data`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_system_health.py`

- imports_from: `src.services.streamlit_dashboard_facade`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_table_tennis_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_tennis_impact_intelligence.py`

- imports_from: `src.market_intelligence.response_compactor, src.market_intelligence.sports, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_tennis_model_activation.py`

- imports_from: `src.services.screenshot_intake, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `multi_sport_model_registry`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_valorant_esports_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_volleyball_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_walk_forward_gate.py`

- imports_from: `src.analytics.model_governance.walk_forward_gate`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_water_polo_model_activation.py`

- imports_from: `src.market_intelligence.multi_sport_model_registry, tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_wnba_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`

## `tests/test_womens_college_basketball_model_activation.py`

- imports_from: `tests.support.action_imports`
- imported_by: `none`
- runtime_callers: `none`
- test_callers: `none`
- script_callers: `none`
- api_callers: `none`
- facade_callers: `none`
- importlib string dependencies: `none`
- monkeypatch string dependencies: `none`
- file-path open/read dependencies: `none`
