# Post Final System Freeze Architecture Map After 10K8ZK3

- `src.core`: canonical math, pricing, probability, risk, portfolio, execution primitives.
- `src.services`: orchestration only.
- `src.connectors`: disabled raw external boundaries.
- `src.providers`: normalized product-category data.
- `src.data`: dataset and validation ownership.
- `src.backtesting`: replay and simulation contracts.
- `src.analytics`: deterministic summaries and reporting.
- `src.research`: deterministic research metadata and planning.
- `src.ai`: disabled and inert.
- `src.brokerage`: disabled and production-shaped.

Canonical execution path remains unchanged:

`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.live_submit -> broker adapter boundary`
