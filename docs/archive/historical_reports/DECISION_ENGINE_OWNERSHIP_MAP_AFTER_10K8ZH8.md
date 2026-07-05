# Decision Engine Ownership Map After 10K8ZH8

## Ownership
- `src/services/decision_engine.py` is the orchestration layer.
- It can call canonical core helpers only.

## Notes
- No connectors are allowed.
- No live execution or AI is allowed.

