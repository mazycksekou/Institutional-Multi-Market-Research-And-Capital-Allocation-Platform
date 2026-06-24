# PHASE 10K8ZHR Analytics Migration Batch 1

## Executive Summary
The safest analytics summaries were migrated into `src.analytics` as local-only deterministic helpers. This batch covers reporting summaries, attribution summaries, calibration summaries, governance summaries, performance summaries, and model-evaluation summaries.

Legacy `model_governance` enforcement and approval gates were intentionally preserved.

## What Moved
- `build_model_validation_report(...)`
- `generate_governance_report(...)`
- `summarize_performance(...)`
- `build_performance_summary(...)`
- `summarize_attribution(...)`
- `build_attribution_summary(...)`
- `summarize_governance(...)`
- `build_calibration_summary(...)`
- `build_model_evaluation_summary(...)`

## What Stayed Preserved
- model_governance remains preserved
- `model_governance/backtest_gate.py`
- `model_governance/calibration_gate.py`
- `model_governance/risk_gate.py`
- `model_governance/promotion_gate.py`
- `model_governance/input_quality_gate.py`
- `model_governance/human_approval_gate.py`
- `model_governance/governance_health.py`

## Safety Guarantees
- No network calls
- No credential reads at import time
- No AI/LLM calls
- No scheduler activation
- No broker execution
- No deletion

## Required Statement
Analytics batch 1 migrates only local deterministic summaries into `src.analytics`. Enforcement and approval gates remain preserved for later proof-backed migration.
