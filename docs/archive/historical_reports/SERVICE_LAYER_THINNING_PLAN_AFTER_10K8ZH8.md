# Service Layer Thinning Plan After 10K8ZH8

## Plan
- Keep orchestration in `src/services/decision_engine.py`.
- Keep pure math in `src/core/*`.
- Keep live behavior deferred.

