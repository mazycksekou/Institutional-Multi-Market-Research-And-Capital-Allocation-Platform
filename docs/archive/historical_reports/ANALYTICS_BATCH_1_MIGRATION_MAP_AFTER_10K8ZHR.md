# Analytics Batch 1 Migration Map After 10K8ZHR

## Canonical Owner
`src.analytics`

## Migrated or Wrapped
| Legacy File | Canonical Destination | Status |
| --- | --- | --- |
| `model_governance/model_validation_report.py` | `src.analytics.reports` | migrated/wrapped |
| `model_governance/governance_report.py` | `src.analytics.reports` | migrated/wrapped |
| `model_governance/data_quality_monitor.py` | `src.analytics.governance` | preserved for later review |
| `automation_scheduler/performance_metrics.py` | `src.analytics.performance` | planned |
| `automation_scheduler/model_performance_report.py` | `src.analytics.performance` | planned |
| `automation_scheduler/clv_tracker.py` | `src.analytics.performance` | planned |
| `automation_scheduler/calibration.py` | `src.analytics.governance` | planned |
| `automation_scheduler/calibration_collector.py` | `src.analytics.governance` | planned |
| `automation_scheduler/calibration_tracker.py` | `src.analytics.governance` | planned |
| `automation_scheduler/calibration_strategy_filter.py` | `src.analytics.governance` | planned |
| `automation_scheduler/micro_outcome_calibration.py` | `src.analytics.governance` | planned |
| `automation_scheduler/pattern_calibration.py` | `src.analytics.governance` | planned |
| `automation_scheduler/manifold_calibration.py` | `src.analytics.governance` | planned |

## Preserved for Now
- `model_governance` enforcement gates
- `model_governance/governance_health.py`
- `model_governance/risk_gate.py`
- `model_governance/promotion_gate.py`
- `model_governance/human_approval_gate.py`

## Why
- Analytics owns summaries and descriptors.
- Enforcement and approval logic remains in place until a later proof-backed migration.
