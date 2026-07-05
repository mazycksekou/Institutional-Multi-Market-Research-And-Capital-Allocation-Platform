# Final Canonical Architecture Map After 10K8ZK2

| Layer | Canonical ownership |
| --- | --- |
| `src.core` | math, pricing, probability, risk, portfolio, execution primitives |
| `src.services` | orchestration only |
| `src.connectors` | disabled raw external boundaries |
| `src.providers` | normalized product-category data |
| `src.data` | dataset contracts, metadata, validation, local loaders |
| `src.backtesting` | replay, leakage, simulation contracts |
| `src.analytics` | deterministic analytics and governance summaries |
| `src.research` | deterministic research metadata and planning |
| `src.ai` | disabled AI boundary only |
| `src.brokerage` | disabled production-shaped brokerage boundary only |

Canonical execution path:

`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.live_submit -> broker adapter boundary`

No alternate paper-only execution path is canonical.
