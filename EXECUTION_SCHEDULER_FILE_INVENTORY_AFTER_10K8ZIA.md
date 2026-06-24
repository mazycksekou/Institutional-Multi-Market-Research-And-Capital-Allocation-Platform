# Execution Scheduler File Inventory After 10K8ZIA

| File | Responsibility |
| --- | --- |
| `automation_scheduler/execution_gatekeeper.py` | Future execution eligibility wrapper |
| `automation_scheduler/execution_authorization.py` | Execution authorization wrapper |
| `automation_scheduler/settlement_rule_checker.py` | Settlement rule comparison helper |
| `automation_scheduler/settlement_discovery.py` | Read-only settlement candidate discovery |
| `automation_scheduler/paper_trade_ledger.py` | Paper-tracking ledger compatibility helper |
| `automation_scheduler/paper_decision_ledger.py` | Paper decision ledger compatibility helper |
| `automation_scheduler/audit_ledger.py` | Local security/execution audit ledger |
| `automation_scheduler/broker_quality_scoring.py` | Broker research scoring helper |
| `automation_scheduler/small_account_strategy.py` | Local risk/review strategy helper |
| `automation_scheduler/manifold_no_bet_detector.py` | No-bet trap detection helper |
| `automation_scheduler/institutional_execution_desk.py` | Simulation-only institutional execution desk |
| `automation_scheduler/institutional_audit_ledger.py` | Institutional audit ledger |
| `automation_scheduler/strategy_performance_ledger.py` | Strategy performance ledger |
| `bet_decision_engine.py` | Legacy line-evaluation compatibility module |
| `bet_log.py` | Legacy bet logging compatibility module |
| `src/services/action_betting_service.py` | Orchestration-only betting service |
| `src/services/decision_engine.py` | Canonical decision orchestration |

