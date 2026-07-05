# Research Layer Ownership Map After 10K8ZHI

## Target Canonical Owner
`src.research`

## Current Ownership Map

### Research Stores
- `research/market_research_schema.py`
- `research/market_research_store.py`

### Research Lanes and Experimental Modules
- `automation_scheduler/deepseek_data_pull_check.py`
- `automation_scheduler/deepseek_daily_report.py`
- `automation_scheduler/deepseek_disagreement_queue.py`
- `automation_scheduler/deepseek_prompt_contracts.py`
- `automation_scheduler/deepseek_profit_lab.py`
- `automation_scheduler/deepseek_response_validator.py`
- `automation_scheduler/deepseek_reviewer.py`
- `automation_scheduler/deep_learning_research_lanes.py`
- `automation_scheduler/tabular_ml_research.py`
- `automation_scheduler/causal_discovery_research.py`
- `automation_scheduler/causal_scaffold.py`
- `automation_scheduler/conformal_uncertainty.py`
- `automation_scheduler/contrastive_embedding_diagnostics.py`
- `automation_scheduler/information_theory_diagnostics.py`
- `automation_scheduler/topological_red_team.py`
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

### Research/Governance Bridges
- `model_governance/research_evidence_gate.py`
- `model_governance/review_queue_gate.py`
- `model_governance/promotion_gate.py`

## Why These Belong in `src.research`
- They are experimental, exploratory, or evidence-tracking utilities.
- They are not raw data storage or backtest simulation.
- They should be isolated from production execution and thin service orchestration.

## Migration Order
1. Move research stores first.
2. Move deterministic research utilities next.
3. Keep governance gates and policy checks thin.
4. Defer any AI/LLM integration until the research, data, and analytics foundations are all canonical.

