# Post Execution Helper Deletion Architecture Map After 10K8ZIV

Canonical execution path:
`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary`

Deleted wrapper layer:
the nine wrapper-only execution helpers removed in `10K8ZIU`.
