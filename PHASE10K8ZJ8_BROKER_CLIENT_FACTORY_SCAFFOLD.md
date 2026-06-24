# PHASE 10K8ZJ8 Broker Client Factory Scaffold

Canonical execution path:

`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary`

This phase adds a production-shaped broker client factory scaffold only.

Key points:

- Approval state is required.
- The factory remains disabled in this phase.
- No broker SDK imports exist.
- No credentials are read at import time.
- No live client object is returned.
