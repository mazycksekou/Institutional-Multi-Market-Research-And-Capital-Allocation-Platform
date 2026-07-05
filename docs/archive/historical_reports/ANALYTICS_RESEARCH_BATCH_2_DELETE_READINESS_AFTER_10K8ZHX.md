# Analytics/Research Batch 2 Delete Readiness After 10K8ZHX

## Delete readiness decisions
- `model_governance/governance_health.py`: compatibility-only; delete-ready only after its compatibility tests are reclassified.
- `automation_scheduler/deep_learning_research_lanes.py`: compatibility-only; delete-ready after wrapper-proof.
- `automation_scheduler/tabular_ml_research.py`: compatibility-only; delete-ready after wrapper-proof.
- `automation_scheduler/model_maturity_registry.py`: redirected consumer; not delete-ready yet because scheduler-facing tests still depend on it.
- `automation_scheduler/feature_ablation_lab.py`: not delete-ready; scheduler-coupled.
- `automation_scheduler/calibration_strategy_filter.py`: not delete-ready; scheduler-coupled.
- `automation_scheduler/experiment_history_store.py`: not delete-ready; file-IO/storage coupled.

## Why no deletion occurred
- This phase is redirection and mapping only.
- Compatibility and historical tests still validate the legacy paths.
- The remaining scheduler-coupled files require a separate proof phase.

## Next safe step
- Reclassify any tests that still require the compatibility shims, then do a wrapper delete-readiness pass.
