# Post Analytics/Research Architecture Map After 10K8ZHQ

## Current Canonical Layers
- `src.core` for math, probability, pricing, risk, execution
- `src.data` for datasets, metadata, source registry, and validation
- `src.backtesting` for replay, leakage checks, and simulation contracts
- `src.analytics` for reporting, attribution, calibration summaries, governance summaries, performance analytics, and model evaluation summaries
- `src.research` for research-lane descriptors, experiment metadata, hypothesis tracking, and ablation planning
- `src.services` for orchestration

## Remaining Legacy Owners
- `model_governance`
- `automation_scheduler`
- root research store/schema files
- selected root-level analytics facades

