# Execution Ownership Migration Map After 10K8ZIC

| File | Current responsibility | Canonical target | Migration decision | Delete-readiness |
| --- | --- | --- | --- | --- |
| `automation_scheduler/execution_gatekeeper.py` | Compatibility wrapper | `src.brokerage.readiness` | Wrapper only | No |
| `automation_scheduler/execution_authorization.py` | Compatibility wrapper | `src.brokerage.readiness` | Wrapper only | No |
| `automation_scheduler/paper_trade_ledger.py` | File-backed compatibility ledger | `src.brokerage.ledger` | Wrapper/mapped | No |
| `automation_scheduler/paper_decision_ledger.py` | File-backed compatibility ledger | `src.brokerage.ledger` | Wrapper/mapped | No |
| `automation_scheduler/settlement_discovery.py` | Read-only settlement candidate discovery | `src.services` | Preserve | No |
| `automation_scheduler/settlement_rule_checker.py` | Settlement rule comparison helper | `src.services` | Preserve | No |
| `automation_scheduler/audit_ledger.py` | Local audit log | `src.brokerage.ledger` | Preserve | No |
| `automation_scheduler/institutional_execution_desk.py` | Simulation-only execution desk | `src.brokerage.execution` | Preserve | No |
| `automation_scheduler/institutional_audit_ledger.py` | Audit log | `src.brokerage.ledger` | Preserve | No |
| `automation_scheduler/strategy_performance_ledger.py` | Strategy performance ledger | `src.analytics` or helper layer | Preserve | No |
| `automation_scheduler/broker_quality_scoring.py` | Broker research scoring | `src.brokerage` later | Preserve | No |
| `automation_scheduler/small_account_strategy.py` | Local risk/review strategy | `src.core` | Preserve | No |
| `automation_scheduler/manifold_no_bet_detector.py` | No-bet trap detection helper | `src.core` | Preserve | No |
| `bet_decision_engine.py` | Legacy evaluation wrapper | `src.core` | Preserve | No |
| `bet_log.py` | Legacy logging wrapper | `src.brokerage.ledger` compatibility | Preserve | No |
| `src/services/action_betting_service.py` | Orchestration | `src.services` | Preserve | No |
| `src/services/decision_engine.py` | Canonical orchestration | `src.services` | Preserve | No |

