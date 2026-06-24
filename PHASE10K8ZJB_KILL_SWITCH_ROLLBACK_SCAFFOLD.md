# PHASE 10K8ZJB Kill Switch and Rollback Scaffold

Canonical execution path:

`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary`

This phase adds the kill-switch and rollback scaffolds only.

Key points:

- The default kill switch blocks live activation.
- Rollback plan is metadata only.
- Live trading remains disabled.
