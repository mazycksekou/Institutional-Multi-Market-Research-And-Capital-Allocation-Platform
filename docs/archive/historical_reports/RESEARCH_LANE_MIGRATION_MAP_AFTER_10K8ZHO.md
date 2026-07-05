# Research Lane Migration Map After 10K8ZHO

## Canonical Direction
Research lanes belong in `src.research` as local metadata and planning scaffolds.

## Planned Moves
- `research/market_research_schema.py`
- `research/market_research_store.py`
- `automation_scheduler/data_source_research_lanes.py`
- `automation_scheduler/deep_learning_research_lanes.py`
- `automation_scheduler/tabular_ml_research.py`
- `automation_scheduler/causal_discovery_research.py`
- `automation_scheduler/causal_scaffold.py`
- `automation_scheduler/conformal_uncertainty.py`
- `automation_scheduler/information_theory_diagnostics.py`
- `automation_scheduler/tracy_widom_research.py`
- `automation_scheduler/universality_research_lanes.py`
- `automation_scheduler/feature_ablation_lab.py`
- `automation_scheduler/extreme_randomness_diagnostics.py`
- `automation_scheduler/extreme_randomness_report.py`
- `automation_scheduler/extreme_signal_red_team.py`
- `automation_scheduler/dynamical_systems_diagnostics.py`
- `automation_scheduler/manifold_review_queue.py`
- `automation_scheduler/manifold_cluster_registry.py`
- `automation_scheduler/manifold_no_bet_detector.py`
- `automation_scheduler/market_state_manifold.py`
- `automation_scheduler/market_state_graph.py`
- `automation_scheduler/market_feature_packs.py`
- `automation_scheduler/representation_feature_builder.py`
- `automation_scheduler/graph_relationship_mapper.py`

## Deferred AI-Adjacent Files
- `automation_scheduler/deepseek_data_pull_check.py`
- `automation_scheduler/deepseek_daily_report.py`
- `automation_scheduler/deepseek_disagreement_queue.py`
- `automation_scheduler/deepseek_prompt_contracts.py`
- `automation_scheduler/deepseek_profit_lab.py`
- `automation_scheduler/deepseek_response_validator.py`
- `automation_scheduler/deepseek_reviewer.py`

## Why
- Research lanes are metadata and planning objects.
- AI execution lanes are deferred until `src.ai` is separately proven.
- No live behavior should move with them.
