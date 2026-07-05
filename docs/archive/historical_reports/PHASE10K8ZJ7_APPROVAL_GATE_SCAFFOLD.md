# PHASE 10K8ZJ7 Approval-Gated Live Activation Scaffold

Canonical execution path:

`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary`

This phase adds the approval-gated live activation scaffold only.

Key points:

- The approval gate remains local-only.
- Default approval state blocks live activation.
- `require_live_approval()` validates approval state deterministically.
- Live trading remains disabled in this phase.
- No credentials are read at import time.
- No account creation, order submission, or broker SDK activation occurs.

Next step:

- Broker client factory scaffold.
