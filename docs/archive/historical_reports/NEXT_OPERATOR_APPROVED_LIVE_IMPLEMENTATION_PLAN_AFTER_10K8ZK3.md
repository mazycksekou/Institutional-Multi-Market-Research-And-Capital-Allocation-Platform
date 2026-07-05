# Next Operator Approved Live Implementation Plan After 10K8ZK3

If operator approval is ever granted, the next work should:

1. keep the canonical execution path unchanged,
2. wire in explicit approval-backed credential loading,
3. create a broker client only behind the kill switch,
4. keep order submission behind the broker adapter boundary,
5. require monitoring and rollback readiness,
6. require production deployment approval,
7. verify live account creation separately,
8. verify live reconciliation separately,
9. verify live ledger persistence separately.

Until then, live trading stays disabled.
