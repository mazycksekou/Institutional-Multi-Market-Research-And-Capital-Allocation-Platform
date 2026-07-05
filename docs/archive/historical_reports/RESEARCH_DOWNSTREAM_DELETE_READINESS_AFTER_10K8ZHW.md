# Research Downstream Delete Readiness After 10K8ZHW

## Current decision
- `automation_scheduler/deep_learning_research_lanes.py`: compatibility-shim candidate, but retained for compatibility.
- `automation_scheduler/tabular_ml_research.py`: compatibility-shim candidate, but retained for compatibility.
- `automation_scheduler/model_maturity_registry.py`: redirected consumer, but retained because broader scheduler tests still use it.

## Why deletion did not occur
- The batch is a redirection phase only.
- Historical tests still touch the legacy imports.
- `feature_ablation_lab.py` and `calibration_strategy_filter.py` remain scheduler-coupled blockers.

## Safe next phase
- Reclassify the remaining scheduler-coupled research files.
- Then run a dedicated delete-readiness proof for the thin wrappers only.
