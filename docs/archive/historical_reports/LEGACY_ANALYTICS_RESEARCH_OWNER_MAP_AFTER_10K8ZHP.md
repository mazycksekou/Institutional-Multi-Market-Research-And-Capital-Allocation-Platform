# Legacy Analytics/Research Owner Map After 10K8ZHP

## Classification Legend
- `MIGRATE_TO_SRC_ANALYTICS`
- `MIGRATE_TO_SRC_RESEARCH`
- `MIGRATE_TO_SRC_SERVICES`
- `KEEP_MODEL_GOVERNANCE_FOR_NOW`
- `COMPATIBILITY_SHIM_CANDIDATE`
- `DELETE_CANDIDATE_AFTER_PROOF`
- `UNSAFE_TO_TOUCH_AI_OR_LIVE`

## Current Legacy Ownership Map

### `MIGRATE_TO_SRC_ANALYTICS`
- `model_governance/model_validation_report.py`
- `model_governance/governance_report.py`
- `model_governance/governance_health.py`
- `model_governance/governance_audit_log.py`
- `model_governance/data_quality_monitor.py`
- `model_governance/data_lineage.py`
- `model_governance/model_drift_monitor.py`
- `model_governance/model_card.py`
- `model_governance/review_queue_gate.py`
- `model_governance/research_evidence_gate.py`
- `automation_scheduler/calibration.py`
- `automation_scheduler/calibration_collector.py`
- `automation_scheduler/calibration_tracker.py`
- `automation_scheduler/calibration_strategy_filter.py`
- `automation_scheduler/micro_outcome_calibration.py`
- `automation_scheduler/pattern_calibration.py`
- `automation_scheduler/manifold_calibration.py`
- `automation_scheduler/performance_metrics.py`
- `automation_scheduler/model_performance_report.py`
- `automation_scheduler/clv_tracker.py`
- `automation_scheduler/strategy_score_aggregator.py`
- `automation_scheduler/strategy_performance_ledger.py`
- `automation_scheduler/strategy_maturity.py`
- `automation_scheduler/strategy_disagreement.py`

### `MIGRATE_TO_SRC_CORE`
- `automation_scheduler/risk_of_ruin.py`
- `automation_scheduler/drawdown_controls.py`
- `automation_scheduler/liquidity_risk.py`
- `automation_scheduler/balance_sheet_risk.py`
- `automation_scheduler/session_risk_rules.py`
- `automation_scheduler/risk_limit_guard.py`
- `automation_scheduler/bankroll_state.py`
- `automation_scheduler/exposure_limits.py`

### `MIGRATE_TO_SRC_RESEARCH`
- `research/market_research_schema.py`
- `research/market_research_store.py`
- `automation_scheduler/data_source_research_lanes.py`
- `automation_scheduler/deep_learning_research_lanes.py`
- `automation_scheduler/tabular_ml_research.py`
- `automation_scheduler/causal_discovery_research.py`
- `automation_scheduler/causal_scaffold.py`
- `automation_scheduler/conformal_uncertainty.py`
- `automation_scheduler/information_theory_diagnostics.py`
- `automation_scheduler/tracy_widom_research.py`
- `automation_scheduler/universality_research_lanes.py`
- `automation_scheduler/feature_ablation_lab.py`
- `automation_scheduler/extreme_randomness_diagnostics.py`
- `automation_scheduler/extreme_randomness_report.py`
- `automation_scheduler/extreme_signal_red_team.py`
- `automation_scheduler/dynamical_systems_diagnostics.py`
- `automation_scheduler/manifold_review_queue.py`
- `automation_scheduler/manifold_cluster_registry.py`
- `automation_scheduler/manifold_no_bet_detector.py`
- `automation_scheduler/market_state_manifold.py`
- `automation_scheduler/market_state_graph.py`
- `automation_scheduler/market_feature_packs.py`
- `automation_scheduler/representation_feature_builder.py`
- `automation_scheduler/graph_relationship_mapper.py`

### `MIGRATE_TO_SRC_SERVICES`
- `automation_scheduler/report_writer.py`
- `automation_scheduler/experiment_report_exporter.py`
- `automation_scheduler/derived_feature_planner.py`
- `automation_scheduler/derived_feature_backfill_report.py`
- `automation_scheduler/strategy_router.py`
- `automation_scheduler/strategy_registry.py`
- `automation_scheduler/strategy_promotion.py`
- `automation_scheduler/strategy_readiness_report.py`
- `automation_scheduler/strategy_context_buckets.py`
- `automation_scheduler/small_account_strategy.py`

### `KEEP_MODEL_GOVERNANCE_FOR_NOW`
- `model_governance/backtest_gate.py`
- `model_governance/calibration_gate.py`
- `model_governance/risk_gate.py`
- `model_governance/promotion_gate.py`
- `model_governance/input_quality_gate.py`
- `model_governance/human_approval_gate.py`
- `model_governance/cross_book_gate.py`
- `model_governance/champion_challenger.py`
- `model_governance/settlement_liquidity_gate.py`
- `model_governance/walk_forward_gate.py`
- `model_governance/execution_later_gate.py`
- `model_governance/activation_tiers.py`
- `model_governance/model_router.py`
- `model_governance/model_router_registry.py`
- `model_governance/model_inventory.py`
- `model_governance/status_classifier.py`
- `model_governance/alert_gate.py`

### `COMPATIBILITY_SHIM_CANDIDATE`
- `model_governance/model_validation_report.py`
- `model_governance/governance_report.py`
- `research/market_research_schema.py`
- `research/market_research_store.py`

### `DELETE_CANDIDATE_AFTER_PROOF`
- None are approved for deletion in this planning phase.

### `UNSAFE_TO_TOUCH_AI_OR_LIVE`
- `automation_scheduler/deepseek_data_pull_check.py`
- `automation_scheduler/deepseek_daily_report.py`
- `automation_scheduler/deepseek_disagreement_queue.py`
- `automation_scheduler/deepseek_prompt_contracts.py`
- `automation_scheduler/deepseek_profit_lab.py`
- `automation_scheduler/deepseek_response_validator.py`
- `automation_scheduler/deepseek_reviewer.py`

## Notes
- `automation_scheduler remains a decommission target`.
- `model_governance remains preserved until migration proof`.
- `src.analytics` and `src.research` now exist as canonical future owners.
