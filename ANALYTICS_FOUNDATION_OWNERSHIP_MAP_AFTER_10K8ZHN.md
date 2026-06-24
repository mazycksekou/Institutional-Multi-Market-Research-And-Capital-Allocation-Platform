# Analytics Foundation Ownership Map After 10K8ZHN

## Canonical Owner
`src.analytics`

## Initial Ownership Map

| Current Artifact | Planned Analytics Ownership | Notes |
| --- | --- | --- |
| `model_governance/model_validation_report.py` | `src.analytics.governance` | Model evaluation summary surface |
| `model_governance/governance_report.py` | `src.analytics.governance` | Governance summary surface |
| `model_governance/governance_health.py` | `src.analytics.governance` | Summary/reporting only |
| `model_governance/governance_audit_log.py` | `src.analytics.governance` | Audit summary/reporting only |
| `model_governance/data_quality_monitor.py` | `src.analytics.governance` | Data-quality reporting |
| `model_governance/data_lineage.py` | `src.analytics.governance` | Lineage summaries |
| `model_governance/model_drift_monitor.py` | `src.analytics.governance` | Drift summaries |
| `model_governance/model_card.py` | `src.analytics.governance` | Model evaluation summaries |
| `model_governance/review_queue_gate.py` | `src.analytics.governance` | Review summaries |
| `model_governance/research_evidence_gate.py` | `src.analytics.governance` | Evidence summaries |
| `automation_scheduler/performance_metrics.py` | `src.analytics.performance` | Performance analytics |
| `automation_scheduler/model_performance_report.py` | `src.analytics.performance` | Performance reporting |
| `automation_scheduler/clv_tracker.py` | `src.analytics.performance` | Attribution/performance summaries |
| `automation_scheduler/calibration.py` | `src.analytics.governance` | Calibration summaries |
| `automation_scheduler/calibration_collector.py` | `src.analytics.governance` | Calibration summaries |
| `automation_scheduler/calibration_tracker.py` | `src.analytics.governance` | Calibration summaries |
| `automation_scheduler/calibration_strategy_filter.py` | `src.analytics.governance` | Calibration summaries |
| `automation_scheduler/micro_outcome_calibration.py` | `src.analytics.governance` | Calibration summaries |
| `automation_scheduler/pattern_calibration.py` | `src.analytics.governance` | Calibration summaries |
| `automation_scheduler/manifold_calibration.py` | `src.analytics.governance` | Calibration summaries |
| `automation_scheduler/risk_of_ruin.py` | `src.core` | Hard risk math stays in core |
| `automation_scheduler/drawdown_controls.py` | `src.core` | Hard risk math stays in core |
| `automation_scheduler/liquidity_risk.py` | `src.core` | Hard risk math stays in core |
| `automation_scheduler/balance_sheet_risk.py` | `src.core` | Hard risk math stays in core |
| `automation_scheduler/session_risk_rules.py` | `src.core` | Hard risk math stays in core |
| `automation_scheduler/risk_limit_guard.py` | `src.core` | Hard risk math stays in core |
| `automation_scheduler/bankroll_state.py` | `src.core` | Risk state primitives stay in core |
| `automation_scheduler/exposure_limits.py` | `src.core` | Risk state primitives stay in core |

## Migration Notes
- Analytics owns summaries and reporting.
- Enforcement remains in `model_governance` or `src.core` until separate proof phases land.
- No file moves happen in this phase.
