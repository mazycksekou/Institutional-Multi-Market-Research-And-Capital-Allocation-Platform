# Broker Account Runtime Risk Map After 10K8ZJ2

| File | Classification | Why |
| --- | --- | --- |
| `src/services/execution_service.py` | `MIGRATE_TO_SRC_SERVICES` | Service orchestration for small-account review and broker-quality summaries |
| `automation_scheduler/__init__.py` | `MIGRATE_TO_SRC_SERVICES` | Thin orchestration wrapper over canonical services |
| `src/api/automation_small_account_routes.py` | `MIGRATE_TO_SRC_SERVICES` | API wrapper only; should call services rather than own logic |
| `src/brokerage/reconciliation.py` | `POSITION_RECONCILIATION_RISK` | Defines disabled reconciliation contracts; execution remains off |
| `automation_scheduler/paper_trade_ledger.py` | `LEDGER_PERSISTENCE_RISK` | File-backed compatibility ledger, local only |
| `automation_scheduler/paper_decision_ledger.py` | `LEDGER_PERSISTENCE_RISK` | File-backed compatibility ledger, local only |
| `src/services/ledger_service.py` | `LEDGER_PERSISTENCE_RISK` | Canonical local file-backed audit/performance store |
| `bet_log.py` | `LEDGER_PERSISTENCE_RISK` | Root-level local bet log only |

Live order submission remains disabled and no account creation path exists.

