# Execution Scheduler Ownership Map After 10K8ZIA

| File | Current responsibility | Canonical target | Risk | Decision | Delete-ready |
| --- | --- | --- | --- | --- | --- |
| `automation_scheduler/execution_gatekeeper.py` | Compatibility wrapper for future execution eligibility | `src.brokerage.readiness` | Low | Preserve as wrapper | No |
| `automation_scheduler/execution_authorization.py` | Compatibility wrapper for execution authorization | `src.brokerage.readiness` | Low | Preserve as wrapper | No |
| `automation_scheduler/settlement_rule_checker.py` | Local settlement-rule comparison | `src.services` or compatibility | Low | Preserve | No |
| `automation_scheduler/settlement_discovery.py` | Read-only settlement candidate discovery | `src.services` | Medium | Preserve and route through canonical bridge | No |
| `automation_scheduler/paper_trade_ledger.py` | File-backed paper ledger | `src.brokerage.ledger` | Medium | Wrap canonical ledger contracts | No |
| `automation_scheduler/paper_decision_ledger.py` | File-backed paper decision ledger | `src.brokerage.ledger` | Medium | Wrap canonical ledger contracts | No |
| `automation_scheduler/audit_ledger.py` | Local audit log | `src.brokerage.ledger` | Low | Preserve for now | No |
| `automation_scheduler/broker_quality_scoring.py` | Broker research scoring | `src.brokerage` later | Low | Preserve | No |
| `automation_scheduler/small_account_strategy.py` | Local risk/review strategy | `src.core` | Low | Preserve | No |
| `automation_scheduler/manifold_no_bet_detector.py` | Trap/no-bet heuristic | `src.core` or `src.services` | Low | Preserve | No |
| `automation_scheduler/institutional_execution_desk.py` | Simulation-only execution desk | `src.brokerage.execution` | Medium | Preserve compatibility | No |
| `automation_scheduler/institutional_audit_ledger.py` | Institutional audit log | `src.brokerage.ledger` | Low | Preserve | No |
| `automation_scheduler/strategy_performance_ledger.py` | Strategy performance ledger | `src.analytics` or `src.brokerage` helper | Low | Preserve | No |
| `bet_decision_engine.py` | Legacy line-evaluation wrapper | `src.core` | Medium | Preserve compatibility | No |
| `bet_log.py` | Legacy bet log wrapper | `src.brokerage.ledger` compatibility | Medium | Preserve compatibility | No |

