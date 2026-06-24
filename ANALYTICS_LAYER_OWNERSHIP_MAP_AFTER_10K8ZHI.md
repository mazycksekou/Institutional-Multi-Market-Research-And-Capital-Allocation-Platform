# Analytics Layer Ownership Map After 10K8ZHI

## Target Canonical Owner
`src.analytics`

## Current Ownership Map

### Root Analytics / Pricing / Risk Facades
- `market_pricing.py`
- `quant_engine.py`
- `risk_engine.py`

### Core Analytics Primitives
- `src/core/pricing.py`
- `src/core/probability.py`
- `src/core/portfolio.py`
- `src/core/clv.py`
- `src/core/market_impact.py`
- `src/core/opportunity_scanner.py`
- `src/core/game_theory.py`
- `src/core/execution.py`

### Governance and Model Oversight
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

### Calibration / Performance / Risk / Attribution
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
- `automation_scheduler/risk_of_ruin.py`
- `automation_scheduler/drawdown_controls.py`
- `automation_scheduler/liquidity_risk.py`
- `automation_scheduler/balance_sheet_risk.py`
- `automation_scheduler/session_risk_rules.py`
- `automation_scheduler/risk_limit_guard.py`
- `automation_scheduler/bankroll_state.py`
- `automation_scheduler/exposure_limits.py`
- `automation_scheduler/strategy_score_aggregator.py`
- `automation_scheduler/strategy_router.py`
- `automation_scheduler/strategy_registry.py`
- `automation_scheduler/strategy_promotion.py`
- `automation_scheduler/strategy_performance_ledger.py`
- `automation_scheduler/strategy_maturity.py`
- `automation_scheduler/strategy_disagreement.py`
- `automation_scheduler/market_state_manifold.py`
- `automation_scheduler/market_state_graph.py`
- `automation_scheduler/market_feature_packs.py`
- `automation_scheduler/representation_feature_builder.py`
- `automation_scheduler/graph_relationship_mapper.py`

## Why These Belong in `src.analytics`
- They score, attribute, calibrate, and govern model outputs.
- They are downstream of data and backtesting.
- They are upstream of any future AI or brokerage layer.

## Compatibility Notes
- `quant_engine.py` and `risk_engine.py` should stay as thin compatibility wrappers until the analytics kernel is fully centralized.
- `market_pricing.py` should become a thin analytics facade, not a hidden owner.

