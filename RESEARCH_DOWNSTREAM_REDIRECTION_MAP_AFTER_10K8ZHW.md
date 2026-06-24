# Research Downstream Redirection Map After 10K8ZHW

| Legacy file | New canonical owner | Wrapper status | Deletion status |
| --- | --- | --- | --- |
| `automation_scheduler/__init__.py` research lane accessors | `src.research.build_tabular_ml_research_lanes` / `src.research.build_deep_learning_research_lanes` | Redirected consumer | Delete candidate after proof |
| `automation_scheduler/deep_learning_research_lanes.py` | `src.research.build_deep_learning_research_lanes` | Compatibility wrapper | Delete candidate after proof |
| `automation_scheduler/tabular_ml_research.py` | `src.research.build_tabular_ml_research_lanes` | Compatibility wrapper | Delete candidate after proof |
| `automation_scheduler/model_maturity_registry.py` lane builders | `src.research.build_tabular_maturity_records` / `src.research.build_deep_learning_maturity_records` | Redirected consumer | Delete candidate after proof |

## Notes
- The canonical lane builders now own the deterministic planning data.
- Legacy import paths remain available.
- No legacy research file was deleted in this batch.
