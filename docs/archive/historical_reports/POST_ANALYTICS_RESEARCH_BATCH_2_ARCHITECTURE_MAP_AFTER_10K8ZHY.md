# Post Analytics/Research Batch 2 Architecture Map After 10K8ZHY

- `src.analytics` owns deterministic health/report/summary helpers.
- `src.research` owns deterministic research lane and storage helpers.
- `model_governance` is now a compatibility layer over canonical analytics for summary composition.
- `automation_scheduler` now defers safe lane planning to canonical research helpers.
- `feature_ablation_lab.py`, `calibration_strategy_filter.py`, and `experiment_history_store.py` remain legacy scheduler owners.

## No-go areas
- No AI/LLM implementation.
- No live data activation.
- No broker execution.
- No legacy deletion in this batch.
