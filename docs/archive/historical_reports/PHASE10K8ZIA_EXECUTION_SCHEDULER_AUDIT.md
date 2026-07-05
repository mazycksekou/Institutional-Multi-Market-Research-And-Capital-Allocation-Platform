# PHASE10K8ZIA Execution Scheduler Audit

## Scope
This phase audits remaining execution, trade, bet, settlement, order, ledger,
position, account, and broker ownership.

Canonical execution path:

`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary`

## Summary
- `src.services.decision_engine` owns canonical execution planning.
- `src.brokerage` now provides the disabled production-shaped execution
  boundary.
- `automation_scheduler` still contains compatibility wrappers and local
  simulation/ledger helpers.
- No live trading is activated.
- No deletion occurs in the audit step.

## High-level inventory
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
- `src/services/action_betting_service.py`
- `src/services/decision_engine.py`
- `src/api/betting_action_routes.py`
- `src/api/automation_institutional_lab_routes.py`
- `main.py`

## Classification model
- `MIGRATE_TO_SRC_BROKERAGE`
- `MIGRATE_TO_SRC_SERVICES`
- `MIGRATE_TO_SRC_CORE`
- `COMPATIBILITY_WRAPPER_ONLY`
- `DELETE_READY_AFTER_PROOF`
- `ACTIVE_RUNTIME_DEPENDENCY`
- `ACTIVE_TEST_DEPENDENCY`
- `UNSAFE_TO_TOUCH`

## Delete-candidate queue
- `DELETE_READY_AFTER_PROOF`: none
- Blocked files remain preserved.

## Explicit non-candidates
- `main.py is not a deletion candidate.`
- `streamlit_app.py is not a deletion candidate.`
