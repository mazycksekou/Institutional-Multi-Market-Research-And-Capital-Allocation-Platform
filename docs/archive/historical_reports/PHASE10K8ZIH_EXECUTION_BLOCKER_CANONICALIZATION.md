# PHASE 10K8ZIH - Execution Blocker Canonicalization

Canonical live-shaped execution path remains:

The canonical live-shaped execution path remains:

`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary`

Reusable execution helpers now live in the canonical brokerage and services layers:

- order construction in `src.brokerage.orders`
- disabled execution submission in `src.brokerage.execution`
- local event recording in `src.brokerage.ledger`
- disabled readiness gating in `src.brokerage.readiness`
- decision orchestration in `src.services.decision_engine`

Compatibility wrappers remain on disk where preserved callers still use them.
compatibility wrappers remain on disk
