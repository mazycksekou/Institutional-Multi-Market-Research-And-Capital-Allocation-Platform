# Legacy Data / Backtesting Owner Map After 10K8ZHL

## Audit Scope

This map covers:

- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/backtest_schema.py`
- `automation_scheduler/backtest_leakage.py`
- `automation_scheduler/backtest_strategy_bankroll.py`
- `automation_scheduler/backtest_strategy_profiles.py`
- `automation_scheduler/historical_data_sources.py`
- `automation_scheduler/historical_odds_importers.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `automation_scheduler/historical_backtest_bridge.py`
- `src/core/backtester.py`
- `src/backtesting`
- `src/services/model_backtest_service.py`
- `src/api/model_backtest_routes.py`
- `src/api/performance_routes.py`

## Ownership Classifications

### MIGRATE_TO_SRC_DATA

- `automation_scheduler/data_paths.py`
- `automation_scheduler/data_source_registry.py`
- `automation_scheduler/data_source_research_lanes.py`
- `automation_scheduler/data_availability_tiers.py`
- `automation_scheduler/data_intelligence_registry.py`
- `automation_scheduler/historical_data_sources.py`
- `automation_scheduler/historical_odds_importers.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `automation_scheduler/historical_backtest_bridge.py`

### MIGRATE_TO_SRC_BACKTESTING

- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/backtest_schema.py`
- `automation_scheduler/backtest_leakage.py`
- `automation_scheduler/backtest_strategy_bankroll.py`
- `automation_scheduler/backtest_strategy_profiles.py`

### MIGRATE_TO_SRC_ANALYTICS

- `model_governance/backtest_gate.py`
- `model_governance/calibration_gate.py`
- `model_governance/risk_gate.py`
- `model_governance/review_queue_gate.py`
- `model_governance/research_evidence_gate.py`
- `model_governance/promotion_gate.py`
- `model_governance/model_validation_report.py`
- `model_governance/model_router.py`
- `model_governance/model_router_registry.py`
- `model_governance/model_inventory.py`
- `model_governance/model_drift_monitor.py`
- `model_governance/model_card.py`
- `model_governance/kelly_gate.py`
- `model_governance/input_quality_gate.py`
- `model_governance/human_approval_gate.py`
- `model_governance/governance_report.py`
- `model_governance/governance_health.py`
- `model_governance/governance_config.py`
- `model_governance/governance_audit_log.py`
- `model_governance/data_quality_monitor.py`
- `model_governance/data_lineage.py`
- `model_governance/cross_book_gate.py`
- `model_governance/champion_challenger.py`
- `model_governance/activation_tiers.py`

### MIGRATE_TO_SRC_RESEARCH

- `research/market_research_schema.py`
- `research/market_research_store.py`
- `automation_scheduler/deepseek_reviewer.py`
- `automation_scheduler/deepseek_response_validator.py`
- `automation_scheduler/deepseek_prompt_contracts.py`
- `automation_scheduler/deepseek_profit_lab.py`
- `automation_scheduler/deepseek_disagreement_queue.py`
- `automation_scheduler/deepseek_data_pull_check.py`
- `automation_scheduler/deepseek_daily_report.py`
- `automation_scheduler/causal_discovery_research.py`
- `automation_scheduler/conformal_uncertainty.py`
- `automation_scheduler/contrastive_embedding_diagnostics.py`
- `automation_scheduler/dynamical_systems_diagnostics.py`
- `automation_scheduler/extreme_randomness_diagnostics.py`
- `automation_scheduler/extreme_randomness_report.py`
- `automation_scheduler/extreme_signal_red_team.py`
- `automation_scheduler/feature_ablation_lab.py`
- `automation_scheduler/information_theory_diagnostics.py`
- `automation_scheduler/tabular_ml_research.py`
- `automation_scheduler/topological_red_team.py`
- `automation_scheduler/tracy_widom_research.py`
- `automation_scheduler/universality_research_lanes.py`

### SERVICE_ORCHESTRATION_ONLY

- `src/services/model_backtest_service.py`
- `src/api/model_backtest_routes.py`
- `src/api/performance_routes.py`

### Canonical Planning / Wrapper Surfaces

- `src.data`
- `src.backtesting`
- `src.services.model_backtest_service.py`
- `src.api.model_backtest_routes.py`
- `src.api.performance_routes.py`

### KEEP_ENTRYPOINT_OR_DASHBOARD

- `main.py`
- `streamlit_app.py`

## Delete Readiness

- Nothing is deleted in this phase.
- automation_scheduler remains a decommission target.
- `src.core.backtester` remains the canonical core validation owner.
- `src.backtesting` is now the canonical planning layer.
