# Analytics/Research Batch 2 Remaining Blockers After 10K8ZHX

| File | Classification | Reason |
| --- | --- | --- |
| `automation_scheduler/feature_ablation_lab.py` | `SCHEDULER_COUPLED_BLOCKED` | Contains ablation/filter logic and is still used by scheduler/reporting paths. |
| `automation_scheduler/calibration_strategy_filter.py` | `SCHEDULER_COUPLED_BLOCKED` | Depends on feature ablation and calibration gating. |
| `automation_scheduler/experiment_history_store.py` | `FILE_IO_OR_STORAGE_BLOCKED` | Owns local SQLite persistence and history storage behavior. |
| `model_governance/governance_health.py` | `SAFE_FOR_LATER_COMPATIBILITY_SHIM` | Now delegates to canonical analytics but still serves compatibility imports. |
| `automation_scheduler/deep_learning_research_lanes.py` | `SAFE_FOR_LATER_COMPATIBILITY_SHIM` | Now delegates to canonical research lane builders. |
| `automation_scheduler/tabular_ml_research.py` | `SAFE_FOR_LATER_COMPATIBILITY_SHIM` | Now delegates to canonical research lane builders. |
| `automation_scheduler/model_maturity_registry.py` | `SAFE_FOR_LATER_COMPATIBILITY_SHIM` | Now imports canonical research lane helpers but remains a scheduler-facing compatibility surface. |

## Notes
- No enforcement or gate behavior was migrated.
- No AI/LLM or live execution behavior was introduced.
