# Post Live Activation Scaffold Architecture Map After 10K8ZJC

`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary`

New scaffold layers:

- `src.brokerage.approval`
- `src.brokerage.client_factory`
- `src.brokerage.live_submit`
- `src.brokerage.live_reconciliation`
- `src.brokerage.live_ledger`
- `src.brokerage.kill_switch`
- `src.brokerage.rollback`

These layers are live-shaped but disabled.
