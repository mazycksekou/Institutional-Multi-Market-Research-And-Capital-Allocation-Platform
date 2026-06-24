# Live Reconciliation Disabled Behavior After 10K8ZJA

The live reconciliation interface is a disabled scaffold.

Rules:

- `reconcile_live_positions_disabled()` always raises `LiveReconciliationDisabledError`.
- Live reconciliation plans are local metadata only.
- No live position reconciliation is performed.
