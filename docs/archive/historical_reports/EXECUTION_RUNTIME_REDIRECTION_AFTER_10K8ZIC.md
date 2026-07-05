# Execution Runtime Redirection After 10K8ZIC

Runtime imports now flow through canonical execution shapes:

- `src.services.decision_engine.build_brokerage_execution_plan`
- `src.brokerage.orders.build_order_request`
- `src.brokerage.orders.build_execution_request`
- `src.brokerage.readiness.get_execution_readiness`
- `src.brokerage.ledger.record_ledger_event`

Legacy scheduler files remain importable as compatibility wrappers.

