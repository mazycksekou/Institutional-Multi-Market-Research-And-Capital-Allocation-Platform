# Execution Blocker Import Scan After 10K8ZIG

## Runtime import references

- `automation_scheduler/__init__.py`
- `automation_scheduler/calibration.py`
- `automation_scheduler/calibration_collector.py`
- `automation_scheduler/scheduler_runner.py`
- `automation_scheduler/system_health.py`
- `automation_scheduler/settlement_discovery.py`
- `automation_scheduler/strategy_score_aggregator.py`
- `automation_scheduler/strategy_promotion.py`
- `automation_scheduler/institutional_execution_desk.py`
- `src/api/automation_review_outcomes_routes.py`
- `src/api/automation_institutional_lab_routes.py`
- `src/api/betting_action_routes.py`
- `tests/test_calibration_collector.py`
- `tests/test_scheduler_runner.py`
- `tests/test_paper_trade_ledger.py`
- `tests/test_paper_decision_ledger.py`
- `tests/test_bet_log.py`
- `tests/test_settlement_discovery.py`
- `tests/test_settlement_rule_checker.py`
- `tests/test_institutional_execution_desk.py`
- `tests/test_strategy_framework.py`
- `tests/test_security_framework.py`

## Compatibility imports

- `automation_scheduler.execution_gatekeeper`
- `automation_scheduler.execution_authorization`
- `automation_scheduler.paper_trade_ledger`
- `automation_scheduler.paper_decision_ledger`
- `bet_decision_engine`
- `bet_log`

## Result

Runtime import redirection is complete for the canonical broker boundary, but the compatibility modules remain referenced for preserved callers and tests.

