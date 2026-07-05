# Execution Scheduler Delete Candidate Queue After 10K8ZIA

## Delete-ready files
DELETE_READY_AFTER_PROOF: none

## Blocked files
- `automation_scheduler/execution_gatekeeper.py`
- `automation_scheduler/execution_authorization.py`
- `automation_scheduler/settlement_rule_checker.py`
- `automation_scheduler/settlement_discovery.py`
- `automation_scheduler/paper_trade_ledger.py`
- `automation_scheduler/paper_decision_ledger.py`
- `automation_scheduler/audit_ledger.py`
- `automation_scheduler/broker_quality_scoring.py`
- `automation_scheduler/small_account_strategy.py`
- `automation_scheduler/manifold_no_bet_detector.py`
- `automation_scheduler/institutional_execution_desk.py`
- `automation_scheduler/institutional_audit_ledger.py`
- `automation_scheduler/strategy_performance_ledger.py`
- `bet_decision_engine.py`
- `bet_log.py`

## Reason
Runtime and test references still exist, and the canonical brokerage boundary has
only just been introduced. No file has been proven delete-ready yet.
