# Final Execution Import Scan After 10K8ZID

Runtime imports still resolve through the canonical disabled brokerage boundary:

- `src.brokerage.orders`
- `src.brokerage.execution`
- `src.brokerage.ledger`
- `src.brokerage.readiness`
- `src.services.decision_engine`

Compatibility wrappers still import for local-only delegation:

- `automation_scheduler.execution_gatekeeper`
- `automation_scheduler.execution_authorization`
- `automation_scheduler.paper_trade_ledger`
- `automation_scheduler.paper_decision_ledger`
- `bet_decision_engine`
- `bet_log`

No execution wrapper was proven delete-ready in this pass.

