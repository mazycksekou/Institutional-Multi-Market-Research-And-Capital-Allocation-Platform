# Analytics/Research Batch 1 Legacy Import Scan After 10K8ZHT

## Remaining Blocker Categories
- `MODEL_GOVERNANCE_ENFORCEMENT_BLOCKED`
- `AI_ADJACENT_BLOCKED`
- `SCHEDULER_COUPLED_BLOCKED`
- `FILE_IO_OR_STORAGE_BLOCKED`
- `TRAINING_OR_EXECUTION_BLOCKED`
- `SAFE_FOR_LATER_COMPATIBILITY_SHIM`
- `DELETE_CANDIDATE_AFTER_PROOF`

## Notable Remaining Legacy Owners
- `model_governance/governance_health.py` -> `MODEL_GOVERNANCE_ENFORCEMENT_BLOCKED`
- `model_governance/backtest_gate.py` -> `MODEL_GOVERNANCE_ENFORCEMENT_BLOCKED`
- `automation_scheduler/deepseek_daily_report.py` -> `AI_ADJACENT_BLOCKED`
- `automation_scheduler/deepseek_disagreement_queue.py` -> `AI_ADJACENT_BLOCKED`
- `automation_scheduler/deepseek_prompt_contracts.py` -> `AI_ADJACENT_BLOCKED`
- `automation_scheduler/deepseek_profit_lab.py` -> `AI_ADJACENT_BLOCKED`
- `automation_scheduler/deepseek_response_validator.py` -> `AI_ADJACENT_BLOCKED`
- `automation_scheduler/deepseek_reviewer.py` -> `AI_ADJACENT_BLOCKED`
- `automation_scheduler/deepseek_data_pull_check.py` -> `AI_ADJACENT_BLOCKED`
- `automation_scheduler/deep_learning_research_lanes.py` -> `SCHEDULER_COUPLED_BLOCKED`
- `automation_scheduler/tabular_ml_research.py` -> `SCHEDULER_COUPLED_BLOCKED`
- `automation_scheduler/feature_ablation_lab.py` -> `SCHEDULER_COUPLED_BLOCKED`
- `research/market_research_schema.py` -> `SAFE_FOR_LATER_COMPATIBILITY_SHIM`
- `research/market_research_store.py` -> `SAFE_FOR_LATER_COMPATIBILITY_SHIM`

## Why No Deletion Occurred
- Batch 1 only migrates the safest deterministic helpers.
- Enforcement, AI-adjacent lanes, and scheduler-coupled behavior remain preserved.
