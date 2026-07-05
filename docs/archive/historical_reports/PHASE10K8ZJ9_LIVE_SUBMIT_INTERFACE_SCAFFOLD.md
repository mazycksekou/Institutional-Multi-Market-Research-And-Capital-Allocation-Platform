# PHASE 10K8ZJ9 Live Submit Interface Scaffold

Canonical execution path:

`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary`

This phase adds the live submit interface scaffold only.

Key points:

- Live submit uses canonical `OrderRequest` and `ExecutionRequest` contracts.
- Approval state and broker client descriptor are required.
- Live submit remains disabled in this phase.
- No order submission occurs.
