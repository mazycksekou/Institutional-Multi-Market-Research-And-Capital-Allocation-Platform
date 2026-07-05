# Broker Reconciliation Disabled Behavior After 10K8ZJ3

- `PositionReconciliationRequest` is a live-shaped descriptor only.
- `PositionReconciliationResult` is a live-shaped disabled snapshot only.
- `build_reconciliation_request()` constructs local descriptors only.
- `reconcile_positions_disabled()` always raises `DisabledBrokerageError`.
- No position reconciliation can run until explicit live approval exists.
