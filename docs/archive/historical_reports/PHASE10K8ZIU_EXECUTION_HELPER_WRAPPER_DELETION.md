# Phase 10K8ZIU Execution Helper Wrapper Deletion

## Deleted Files
The nine proof-backed wrapper-only execution helpers were deleted.

## Proof Source
Deletion is authorized by `PHASE10K8ZIT_EXECUTION_HELPER_FINAL_DELETE_PROOF.md`.

## Canonical Execution Path
`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary`

## Behavior Preserved
Live trading remains disabled and the brokerage boundary stays production-shaped but inert.
