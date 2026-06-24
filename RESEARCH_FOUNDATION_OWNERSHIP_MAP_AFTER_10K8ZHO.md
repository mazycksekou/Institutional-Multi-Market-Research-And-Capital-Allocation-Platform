# Research Foundation Ownership Map After 10K8ZHO

## Canonical Owner
`src.research`

## Initial Ownership Map

| Current Artifact | Planned Research Ownership | Notes |
| --- | --- | --- |
| `research/market_research_schema.py` | `src.research` | Local schema contract/store planning |
| `research/market_research_store.py` | `src.research` | Local research store planning |
| `automation_scheduler/data_source_research_lanes.py` | `src.research` | Research lane descriptor |
| `automation_scheduler/deep_learning_research_lanes.py` | `src.research` | Research lane descriptor |
| `automation_scheduler/tabular_ml_research.py` | `src.research` | Deterministic research scaffolds |
| `automation_scheduler/causal_discovery_research.py` | `src.research` | Experimental lane planning |
| `automation_scheduler/causal_scaffold.py` | `src.research` | Experimental lane planning |
| `automation_scheduler/conformal_uncertainty.py` | `src.research` | Research planning |
| `automation_scheduler/information_theory_diagnostics.py` | `src.research` | Research diagnostics |
| `automation_scheduler/tracy_widom_research.py` | `src.research` | Research lane planning |
| `automation_scheduler/universality_research_lanes.py` | `src.research` | Research lane planning |
| `automation_scheduler/feature_ablation_lab.py` | `src.research` | Ablation planning |
| `automation_scheduler/extreme_randomness_diagnostics.py` | `src.research` | Research diagnostics |
| `automation_scheduler/extreme_randomness_report.py` | `src.research` | Research reporting |
| `automation_scheduler/extreme_signal_red_team.py` | `src.research` | Research diagnostics |
| `automation_scheduler/dynamical_systems_diagnostics.py` | `src.research` | Research diagnostics |
| `automation_scheduler/manifold_review_queue.py` | `src.research` | Research queue planning |
| `automation_scheduler/manifold_cluster_registry.py` | `src.research` | Research metadata |
| `automation_scheduler/manifold_no_bet_detector.py` | `src.research` | Research guardrail metadata |
| `automation_scheduler/market_state_manifold.py` | `src.research` | Research lane planning |
| `automation_scheduler/market_state_graph.py` | `src.research` | Research lane planning |
| `automation_scheduler/market_feature_packs.py` | `src.research` | Research lane planning |
| `automation_scheduler/representation_feature_builder.py` | `src.research` | Research lane planning |
| `automation_scheduler/graph_relationship_mapper.py` | `src.research` | Research lane planning |
| `automation_scheduler/deepseek_*` | `src.research` later, `src.ai` deferred | Keep disabled until AI boundary exists |

## Migration Notes
- The root `research/` package currently holds the local schema/store.
- `src.research` should own future experiment metadata and lane descriptors.
- DeepSeek-named files are treated as AI-adjacent and remain deferred until the AI boundary is separately proven.
