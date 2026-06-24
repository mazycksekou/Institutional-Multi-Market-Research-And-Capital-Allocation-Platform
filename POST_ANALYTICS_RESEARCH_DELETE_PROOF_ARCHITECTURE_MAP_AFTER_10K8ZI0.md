# Post Analytics/Research Delete Proof Architecture Map After 10K8ZI0

- `src.analytics` remains the canonical owner of deterministic analytics summaries.
- `src.research` remains the canonical owner of deterministic research metadata and planning helpers.
- `model_governance` remains a compatibility layer and preservation point for governance enforcement and summary surfaces.
- `automation_scheduler` remains decommission-targeted and still owns scheduler-coupled research logic.

## Deletion status
- No wrapper deletion occurred.
- No legacy deletion occurred.

## Deferred areas
- AI/LLM.
- Brokerage/live execution.
- Production deployment.
