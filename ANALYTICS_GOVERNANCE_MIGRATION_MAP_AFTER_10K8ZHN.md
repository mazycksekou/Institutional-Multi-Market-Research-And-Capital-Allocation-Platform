# Analytics Governance Migration Map After 10K8ZHN

## Canonical Direction
Governance summaries should move to `src.analytics`, while hard gates and enforcement remain where they are until proof-backed migration is complete.

## Summary Ownership Split

### Move to `src.analytics`
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
- `automation_scheduler/performance_metrics.py`
- `automation_scheduler/model_performance_report.py`
- `automation_scheduler/clv_tracker.py`
- `automation_scheduler/calibration.py`
- `automation_scheduler/calibration_collector.py`
- `automation_scheduler/calibration_tracker.py`
- `automation_scheduler/calibration_strategy_filter.py`
- `automation_scheduler/micro_outcome_calibration.py`
- `automation_scheduler/pattern_calibration.py`
- `automation_scheduler/manifold_calibration.py`

### Keep in `model_governance` for now
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

## Why
- Analytics should own summaries and reporting surfaces.
- The gates above still participate in enforcement and policy decisions.
- That enforcement remains intentionally thin until later migration proof.

## Required Statement
Model-governance reporting belongs in `src.analytics`. Enforcement and approval gates remain preserved for now until later proof-backed migration.
