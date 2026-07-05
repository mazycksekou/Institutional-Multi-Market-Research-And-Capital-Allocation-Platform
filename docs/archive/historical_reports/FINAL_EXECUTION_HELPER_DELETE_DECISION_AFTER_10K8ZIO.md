# Final Execution Helper Delete Decision After 10K8ZIO

## Delete decision

No file in the execution-helper batch is approved for deletion in this phase.

Canonical execution helpers remain anchored in `src.brokerage.settlement` and `src.services.execution_service`.

## Blocked files

- `automation_scheduler/settlement_rule_checker.py`
- `automation_scheduler/settlement_discovery.py`
- `automation_scheduler/audit_ledger.py`
- `automation_scheduler/institutional_audit_ledger.py`
- `automation_scheduler/strategy_performance_ledger.py`
- `automation_scheduler/broker_quality_scoring.py`
- `automation_scheduler/small_account_strategy.py`
- `automation_scheduler/manifold_no_bet_detector.py`
- `automation_scheduler/institutional_execution_desk.py`

## Reason

Runtime and proof-test dependencies remain active, so deletion is not yet proof-backed.
