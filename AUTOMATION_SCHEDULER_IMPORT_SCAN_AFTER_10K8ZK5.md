# Automation Scheduler Decommission Inventory

Canonical src.* architecture already exists. Live trading, broker/account/credential/order/deployment activation remain disabled.

Inventory summary:
- Remaining automation_scheduler files: 329
- Runtime-referenced files: 70
- Test-referenced files: 303
- Delete-ready after proof: 23

## Runtime References

- `automation_scheduler/__init__.py` -> 11 runtime callers
- `automation_scheduler/advanced_red_team_report.py` -> 1 runtime callers
- `automation_scheduler/advanced_shape_diagnostics.py` -> 1 runtime callers
- `automation_scheduler/arbitrage/__init__.py` -> 11 runtime callers
- `automation_scheduler/arbitrage/exchange_arbitrage.py` -> 1 runtime callers
- `automation_scheduler/arbitrage/prediction_market_arbitrage.py` -> 1 runtime callers
- `automation_scheduler/asof_line_movement_query.py` -> 1 runtime callers
- `automation_scheduler/audit_log.py` -> 1 runtime callers
- `automation_scheduler/balance_sheet_risk.py` -> 3 runtime callers
- `automation_scheduler/baseball_impact_readiness.py` -> 2 runtime callers
- `automation_scheduler/basketball_player_impact.py` -> 2 runtime callers
- `automation_scheduler/basketball_player_impact_readiness.py` -> 2 runtime callers
- `automation_scheduler/calibration.py` -> 23 runtime callers
- `automation_scheduler/calibration_collector.py` -> 2 runtime callers
- `automation_scheduler/calibration_strategy_filter.py` -> 1 runtime callers
- `automation_scheduler/candlestick_pattern_detector.py` -> 1 runtime callers
- `automation_scheduler/collector_scheduled_runner.py` -> 1 runtime callers
- `automation_scheduler/combat_impact_readiness.py` -> 2 runtime callers
- `automation_scheduler/data_availability_tiers.py` -> 2 runtime callers
- `automation_scheduler/data_paths.py` -> 4 runtime callers
- `automation_scheduler/data_source_registry.py` -> 2 runtime callers
- `automation_scheduler/data_source_research_lanes.py` -> 2 runtime callers
- `automation_scheduler/deepseek_daily_report.py` -> 1 runtime callers
- `automation_scheduler/extreme_randomness_diagnostics.py` -> 2 runtime callers
- `automation_scheduler/extreme_randomness_report.py` -> 2 runtime callers
- `automation_scheduler/feature_ablation_lab.py` -> 1 runtime callers
- `automation_scheduler/golf_impact_readiness.py` -> 2 runtime callers
- `automation_scheduler/historical_data_sources.py` -> 1 runtime callers
- `automation_scheduler/hockey_impact_readiness.py` -> 2 runtime callers
- `automation_scheduler/institutional_cross_asset_adapters.py` -> 2 runtime callers
- `automation_scheduler/institutional_cross_asset_calibration.py` -> 1 runtime callers
- `automation_scheduler/institutional_deepseek_review.py` -> 1 runtime callers
- `automation_scheduler/institutional_risk_engine.py` -> 1 runtime callers
- `automation_scheduler/later/__init__.py` -> 11 runtime callers
- `automation_scheduler/line_movement_data_quality_dashboard.py` -> 1 runtime callers
- `automation_scheduler/line_movement_import_contract.py` -> 1 runtime callers
- `automation_scheduler/line_movement_readiness.py` -> 1 runtime callers
- `automation_scheduler/liquidity_context_scoring.py` -> 1 runtime callers
- `automation_scheduler/liquidity_risk.py` -> 1 runtime callers
- `automation_scheduler/manifold_calibration.py` -> 1 runtime callers
- `automation_scheduler/market_state_manifold.py` -> 1 runtime callers
- `automation_scheduler/micro_outcome_calibration.py` -> 2 runtime callers
- `automation_scheduler/middles/__init__.py` -> 11 runtime callers
- `automation_scheduler/middles/spread_middle.py` -> 1 runtime callers
- `automation_scheduler/middles/total_middle.py` -> 1 runtime callers
- `automation_scheduler/model_data_field_catalog.py` -> 1 runtime callers
- `automation_scheduler/outcome_migration.py` -> 1 runtime callers
- `automation_scheduler/outcome_store.py` -> 1 runtime callers
- `automation_scheduler/owner_approval_gate.py` -> 1 runtime callers
- `automation_scheduler/pattern_calibration.py` -> 2 runtime callers
- `automation_scheduler/pattern_review_queue.py` -> 3 runtime callers
- `automation_scheduler/performance_metrics.py` -> 1 runtime callers
- `automation_scheduler/provider_allowlist.py` -> 4 runtime callers
- `automation_scheduler/response_compactor.py` -> 2 runtime callers
- `automation_scheduler/review_queue.py` -> 8 runtime callers
- `automation_scheduler/risk_limit_guard.py` -> 1 runtime callers
- `automation_scheduler/risk_of_ruin.py` -> 1 runtime callers
- `automation_scheduler/scheduler_config.py` -> 3 runtime callers
- `automation_scheduler/secret_safety.py` -> 2 runtime callers
- `automation_scheduler/security_event_types.py` -> 2 runtime callers
- `automation_scheduler/security_policy.py` -> 2 runtime callers
- `automation_scheduler/session_risk_rules.py` -> 1 runtime callers
- `automation_scheduler/soccer_impact_readiness.py` -> 2 runtime callers
- `automation_scheduler/source_event_link_resolver.py` -> 1 runtime callers
- `automation_scheduler/strategy_context_buckets.py` -> 2 runtime callers
- `automation_scheduler/streamlit_dashboard_data.py` -> 1 runtime callers
- `automation_scheduler/system_health.py` -> 1 runtime callers
- `automation_scheduler/technical_signal_fields.py` -> 1 runtime callers
- `automation_scheduler/tennis_impact_readiness.py` -> 2 runtime callers
- `automation_scheduler/zero_dte_fixture_template.py` -> 1 runtime callers

## Runtime Import/Reference Notes

- Runtime callers are concentrated in `main.py`, `streamlit_app.py`, `src/api/*`, `src/services/*`, and `src/brokerage/readiness.py`.
- No delete-ready file appears in the runtime reference set.
