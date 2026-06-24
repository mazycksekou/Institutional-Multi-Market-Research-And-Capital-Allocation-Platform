# Post Execution Helper Architecture Map After 10K8ZIP

```
src.core
  -> src.services.decision_engine
  -> src.brokerage.orders
  -> src.brokerage.execution
  -> src.brokerage.ledger
  -> disabled broker boundary
```

Additional canonical helper ownership:

- `src.brokerage.settlement`
- `src.services.settlement_service`
- `src.services.ledger_service`
- `src.services.execution_service`

Legacy scheduler wrappers remain import-compatible and are not deleted.
