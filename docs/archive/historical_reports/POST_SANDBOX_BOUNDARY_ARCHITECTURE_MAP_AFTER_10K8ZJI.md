# Post Sandbox Boundary Architecture Map After 10K8ZJI

- `src.core` continues to own the math and decision primitives.
- `src.services.decision_engine` continues to own orchestration.
- `src.brokerage.orders`, `src.brokerage.execution`, and `src.brokerage.ledger` continue to own the live-shaped execution path.
- `src.brokerage.adapter` owns the adapter protocol metadata.
- `src.brokerage.sandbox` owns the sandbox broker descriptor metadata.
- `src.brokerage.credential_loader` owns the disabled credential activation boundary.
- `src.brokerage.sandbox_submit` owns the disabled sandbox submit shape.
