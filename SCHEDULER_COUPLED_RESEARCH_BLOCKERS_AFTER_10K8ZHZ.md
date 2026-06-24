# Scheduler-Coupled Research Blockers After 10K8ZHZ

| File | Classification | Reason |
| --- | --- | --- |
| `automation_scheduler/feature_ablation_lab.py` | `SCHEDULER_COUPLED_BLOCKED` | Large scheduler-owned ablation logic with calibration and reporting coupling. |
| `automation_scheduler/calibration_strategy_filter.py` | `SCHEDULER_COUPLED_BLOCKED` | Depends on feature ablation and calibration gating. |
| `automation_scheduler/experiment_history_store.py` | `FILE_IO_OR_STORAGE_BLOCKED` | Owns SQLite experiment-history persistence. |
| `automation_scheduler/deepseek_*` | `AI_ADJACENT_BLOCKED` | AI-adjacent lanes remain deferred and are not migrated here. |

## Status
- No scheduler activation occurred.
- No AI/LLM calls occurred.
- These remain separate from wrapper-only delete proof.
