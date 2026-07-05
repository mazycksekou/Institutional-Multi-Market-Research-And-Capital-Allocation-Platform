# Research Batch 1 Migration Map After 10K8ZHS

## Canonical Owner
`src.research`

## Migrated or Wrapped
| Legacy File | Canonical Destination | Status |
| --- | --- | --- |
| `research/market_research_schema.py` | `src.research.storage` | migrated/wrapped |
| `research/market_research_store.py` | `src.research.storage` | migrated/wrapped |
| `automation_scheduler/feature_ablation_lab.py` | `src.research.ablation` | planned |
| `automation_scheduler/deep_learning_research_lanes.py` | `src.research.lanes` | planned |
| `automation_scheduler/tabular_ml_research.py` | `src.research.lanes` | planned |

## Preserved for Now
- `automation_scheduler/deepseek_*`
- `automation_scheduler/*research*` that are AI-adjacent
- `automation_scheduler/*ablation*` with scheduler coupling

## Why
- Research owns descriptors and planning metadata.
- AI-adjacent execution lanes remain deferred.
