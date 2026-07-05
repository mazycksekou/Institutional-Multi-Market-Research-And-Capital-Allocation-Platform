# Post Execution Boundary Architecture Map After 10K8ZIF

- `src.core` owns math, risk, portfolio, execution/game-theory primitives.
- `src.services.decision_engine` owns orchestration and disabled execution planning.
- `src.brokerage.orders` owns production-shaped order contracts.
- `src.brokerage.execution` owns disabled execution submission behavior.
- `src.brokerage.ledger` owns local-only ledger events.
- `automation_scheduler` remains a compatibility and decommission target.

