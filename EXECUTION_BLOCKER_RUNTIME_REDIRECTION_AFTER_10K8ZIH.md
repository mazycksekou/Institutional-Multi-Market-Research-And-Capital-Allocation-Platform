# Execution Blocker Runtime Redirection After 10K8ZIH

Runtime execution callers continue to route through the canonical brokerage boundary:

- `src.services.decision_engine.build_brokerage_execution_plan`
- `src.brokerage.orders.build_order_request`
- `src.brokerage.execution.submit_order_disabled`
- `src.brokerage.ledger.record_ledger_event`
- `src.brokerage.readiness.get_execution_readiness`

Legacy wrappers remain importable for compatibility only.

