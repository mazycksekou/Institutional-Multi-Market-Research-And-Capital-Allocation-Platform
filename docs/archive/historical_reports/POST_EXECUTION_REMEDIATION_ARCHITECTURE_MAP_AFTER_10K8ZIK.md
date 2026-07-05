# Post Execution Remediation Architecture Map After 10K8ZIK

- `src.core`: math, risk, portfolio, execution primitives
- `src.services.decision_engine`: orchestration and disabled execution planning
- `src.brokerage.orders`: production-shaped order requests
- `src.brokerage.execution`: disabled execution submission boundary
- `src.brokerage.ledger`: local-only ledger events
- `automation_scheduler`: compatibility and decommission target

