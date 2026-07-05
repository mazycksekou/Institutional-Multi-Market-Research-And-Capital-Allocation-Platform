# PHASE 10K8ZHS Research Migration Batch 1

## Executive Summary
The safest research metadata and planning helpers were migrated into `src.research` as local-only deterministic helpers.

Legacy research storage/schema files and scheduler research lanes remain preserved for compatibility and later proof-backed review.

## What Moved
- research schema descriptors
- research store descriptors
- local storage helpers
- research lane descriptors
- experiment metadata
- hypothesis records
- ablation plan descriptors

## What Stayed Preserved
- legacy research/ remains preserved
- `research/market_research_schema.py` as compatibility wrapper
- `research/market_research_store.py` as compatibility wrapper
- `automation_scheduler/deepseek_*`
- `automation_scheduler/deep_learning_research_lanes.py`
- `automation_scheduler/tabular_ml_research.py`
- `automation_scheduler/feature_ablation_lab.py`

## Safety Guarantees
- No AI/LLM calls
- No live data pulls
- No external writes
- No scheduler activation
- No deletion

## Required Statement
Research batch 1 migrates only local deterministic metadata and planning helpers into `src.research`. Execution, training, and AI-adjacent scheduler behavior remain preserved for later proof-backed migration.
