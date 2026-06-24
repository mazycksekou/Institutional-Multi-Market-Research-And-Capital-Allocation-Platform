# Post Live Trading Readiness Architecture Map After 10K8ZJ6

- `src.core` remains the calculation layer.
- `src.services.decision_engine` remains the orchestration layer.
- `src.brokerage.accounts` defines disabled account descriptors.
- `src.brokerage.credentials` defines disabled credential policy.
- `src.brokerage.reconciliation` defines disabled reconciliation contracts.
- `src.brokerage.ledger` remains local in-memory.
- `src.services.ledger_service` remains local file-backed.

