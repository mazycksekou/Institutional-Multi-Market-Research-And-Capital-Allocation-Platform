# Execution Helper Runtime Redirection Map After 10K8ZIR

- `automation_scheduler/settlement_rule_checker.py` -> `src.brokerage.settlement.compare_settlement_rules`
- `automation_scheduler/settlement_discovery.py` -> `src.services.settlement_service`
- `automation_scheduler/audit_ledger.py` -> `src.services.ledger_service`
- `automation_scheduler/institutional_audit_ledger.py` -> `src.services.ledger_service`
- `automation_scheduler/strategy_performance_ledger.py` -> `src.services.ledger_service`
- `automation_scheduler/broker_quality_scoring.py` -> `src.services.execution_service`
- `automation_scheduler/small_account_strategy.py` -> `src.services.execution_service`
- `automation_scheduler/manifold_no_bet_detector.py` -> `src.services.execution_service`
- `automation_scheduler/institutional_execution_desk.py` -> `src.services.execution_service`
