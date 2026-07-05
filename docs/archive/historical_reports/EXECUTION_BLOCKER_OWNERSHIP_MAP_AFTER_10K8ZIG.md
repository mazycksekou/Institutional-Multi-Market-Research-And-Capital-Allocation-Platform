# Execution Blocker Ownership Map After 10K8ZIG

## Canonical ownership

- `src.brokerage.orders`
- `src.brokerage.execution`
- `src.brokerage.positions`
- `src.brokerage.ledger`
- `src.brokerage.readiness`
- `src.services.decision_engine`

## Wrapper-only compatibility surfaces

- `automation_scheduler/execution_gatekeeper.py`
- `automation_scheduler/execution_authorization.py`
- `automation_scheduler/paper_trade_ledger.py`
- `automation_scheduler/paper_decision_ledger.py`
- `bet_decision_engine.py`
- `bet_log.py`

## Remaining scheduler-owned helpers

- `automation_scheduler/settlement_rule_checker.py`
- `automation_scheduler/settlement_discovery.py`
- `automation_scheduler/audit_ledger.py`
- `automation_scheduler/institutional_audit_ledger.py`
- `automation_scheduler/strategy_performance_ledger.py`
- `automation_scheduler/broker_quality_scoring.py`
- `automation_scheduler/small_account_strategy.py`
- `automation_scheduler/manifold_no_bet_detector.py`
- `automation_scheduler/institutional_execution_desk.py`

## Decision

- `DELETE_READY_AFTER_PROOF: none`
- `COMPATIBILITY_WRAPPER_ONLY`: wrappers remain on disk for compatibility and tests
- `MIGRATE_TO_SRC_*`: safe future migration targets, not deletion targets yet
- `UNSAFE_TO_TOUCH`: runtime-coupled scheduler execution surfaces

