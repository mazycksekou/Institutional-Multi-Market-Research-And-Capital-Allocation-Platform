# Analytics/Research Delete Readiness After 10K8ZHP

## Status
- `src.analytics`: delete-ready legacy inputs are not yet being removed.
- `src.research`: delete-ready legacy inputs are not yet being removed.

## Current Decision
- Legacy analytics/research owners are mapped, but nothing is deleted.
- `automation_scheduler` remains a decommission target.
- `model_governance` remains preserved until later proof-backed migration.

## Why No Deletion Occurred
- The phase is planning-only.
- The canonical owners are newly scaffolded.
- Compatibility proof and downstream test redirection still need time.
