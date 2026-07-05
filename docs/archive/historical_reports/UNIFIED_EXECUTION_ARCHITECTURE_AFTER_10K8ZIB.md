# Unified Execution Architecture After 10K8ZIB

Canonical path:

`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary`

Notes:
- No paper-only canonical path exists.
- Tests and simulations must use the same contracts as future live trading.
- The broker boundary is disabled by design.

