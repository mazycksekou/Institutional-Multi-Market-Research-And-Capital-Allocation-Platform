# Execution Blocker Canonicalization Map After 10K8ZIH

| Legacy file | Canonical ownership | Status |
| --- | --- | --- |
| `automation_scheduler/execution_gatekeeper.py` | `src.brokerage.readiness` | wrapper only |
| `automation_scheduler/execution_authorization.py` | `src.brokerage.readiness` | wrapper only |
| `automation_scheduler/paper_trade_ledger.py` | `src.brokerage.ledger` | wrapper / mapped |
| `automation_scheduler/paper_decision_ledger.py` | `src.brokerage.ledger` | wrapper / mapped |
| `automation_scheduler/settlement_rule_checker.py` | `src.services` | preserved helper |
| `automation_scheduler/settlement_discovery.py` | `src.services` | preserved helper |
| `automation_scheduler/audit_ledger.py` | `src.brokerage.ledger` later | preserved helper |
| `automation_scheduler/institutional_audit_ledger.py` | `src.brokerage.ledger` later | preserved helper |
| `automation_scheduler/strategy_performance_ledger.py` | `src.services` | preserved helper |
| `automation_scheduler/broker_quality_scoring.py` | `src.brokerage` later | preserved helper |
| `automation_scheduler/small_account_strategy.py` | `src.core` | preserved helper |
| `automation_scheduler/manifold_no_bet_detector.py` | `src.core` | preserved helper |
| `automation_scheduler/institutional_execution_desk.py` | `src.brokerage.execution` | wrapper only |
| `bet_decision_engine.py` | `src.core` | compatibility wrapper |
| `bet_log.py` | `src.brokerage.ledger` compatibility | compatibility wrapper |

No live submission path was activated.

