# PHASE 10K8ZIG - Execution / Scheduler Blocker Remediation Audit

Canonical execution path:
`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary`

This audit classifies the remaining execution, trade, bet, settlement, order, ledger, position, account, and broker ownership surfaces.

## Ownership Classifications

| File | Current responsibility | Canonical target | Risk | Migration decision | Delete-readiness |
| --- | --- | --- | --- | --- | --- |
| `automation_scheduler/execution_gatekeeper.py` | Compatibility wrapper for future execution eligibility | `src.brokerage.readiness` | low | COMPATIBILITY_WRAPPER_ONLY | not ready |
| `automation_scheduler/execution_authorization.py` | Compatibility wrapper for execution authorization | `src.brokerage.readiness` | low | COMPATIBILITY_WRAPPER_ONLY | not ready |
| `automation_scheduler/paper_trade_ledger.py` | Local compatibility ledger for paper-tracking events | `src.brokerage.ledger` | medium | COMPATIBILITY_WRAPPER_ONLY | not ready |
| `automation_scheduler/paper_decision_ledger.py` | Local compatibility ledger for decision records | `src.brokerage.ledger` | medium | COMPATIBILITY_WRAPPER_ONLY | not ready |
| `automation_scheduler/settlement_rule_checker.py` | Settlement-rule comparison helper | `src.services` | medium | MIGRATE_TO_SRC_SERVICES | not ready |
| `automation_scheduler/settlement_discovery.py` | Read-only settlement candidate discovery | `src.services` | medium | MIGRATE_TO_SRC_SERVICES | not ready |
| `automation_scheduler/audit_ledger.py` | Local audit ledger | `src.brokerage.ledger` | medium | MIGRATE_TO_SRC_BROKERAGE | not ready |
| `automation_scheduler/institutional_audit_ledger.py` | Institutional audit ledger | `src.brokerage.ledger` | medium | MIGRATE_TO_SRC_BROKERAGE | not ready |
| `automation_scheduler/strategy_performance_ledger.py` | Strategy performance summary helper | `src.services` | medium | MIGRATE_TO_SRC_SERVICES | not ready |
| `automation_scheduler/broker_quality_scoring.py` | Broker research scoring helper | `src.brokerage` later | medium | MIGRATE_TO_SRC_BROKERAGE | not ready |
| `automation_scheduler/small_account_strategy.py` | Local risk/review helper | `src.core` | medium | MIGRATE_TO_SRC_CORE | not ready |
| `automation_scheduler/manifold_no_bet_detector.py` | Trap/no-bet heuristic | `src.core` | medium | MIGRATE_TO_SRC_CORE | not ready |
| `automation_scheduler/institutional_execution_desk.py` | Simulation-only execution desk | `src.brokerage.execution` | high | COMPATIBILITY_WRAPPER_ONLY | not ready |
| `bet_decision_engine.py` | Legacy evaluation wrapper | `src.core` | low | COMPATIBILITY_WRAPPER_ONLY | not ready |
| `bet_log.py` | Legacy logging wrapper | `src.brokerage.ledger` compatibility | low | COMPATIBILITY_WRAPPER_ONLY | not ready |

## Decision

`DELETE_READY_AFTER_PROOF: none`

No execution/trade/bet/settlement file was proven safe to delete in this phase.

## Notes

- `main.py` is not a deletion candidate.
- `streamlit_app.py` is not a deletion candidate.
- The broker boundary stays disabled.
- Live trading remains impossible.
main.py is not a deletion candidate.
streamlit_app.py is not a deletion candidate.
