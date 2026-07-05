# Post Analytics/Research Batch 1 Architecture Map After 10K8ZHU

## Canonical Layers
- `src.core`: math, probability, pricing, risk, execution
- `src.data`: dataset/source/validation
- `src.backtesting`: replay/leakage/simulation contracts
- `src.analytics`: summaries, attribution, calibration, governance reporting
- `src.research`: lane descriptors, experiment metadata, storage descriptors, ablation planning
- `src.services`: orchestration

## Remaining Legacy Layers
- `model_governance`
- `research`
- `automation_scheduler`

