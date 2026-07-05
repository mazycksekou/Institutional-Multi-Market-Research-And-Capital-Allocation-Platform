# PHASE 10K8ZHW Research Downstream Redirection

## Scope
This batch redirects the safest downstream research consumers to canonical `src.research` ownership.

## Canonical ownership
- `src.research` now owns deterministic research lane descriptors, experiment metadata, hypothesis records, ablation plans, and storage/schema descriptors.
- `automation_scheduler.__init__`, `automation_scheduler.model_maturity_registry`, `automation_scheduler.deep_learning_research_lanes`, and `automation_scheduler.tabular_ml_research` now delegate to canonical research helpers.

## What changed
- The scheduler package no longer owns the safe lane-builder logic.
- The canonical package provides the lane and maturity-record helpers directly.
- Legacy module entry points remain importable as compatibility wrappers.

## Compatibility and safety
- No AI/LLM calls were introduced.
- No live data pulls were introduced.
- No connector imports were introduced.
- No scheduler job activation was introduced.

## Remaining blockers
- `automation_scheduler.feature_ablation_lab` remains scheduler-coupled and is not yet a migration candidate.
- `automation_scheduler.calibration_strategy_filter` remains coupled to the ablation lab.

## Next step
Document the remaining research and scheduler blockers, then evaluate delete-readiness for the thin wrappers only.
