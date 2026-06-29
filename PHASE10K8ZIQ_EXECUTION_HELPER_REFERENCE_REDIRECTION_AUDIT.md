# Phase 10K8ZIQ Execution Helper Reference Redirection Audit

## Big-Picture Architecture
Canonical execution flow:
`src.core -> src.services.decision_engine -> src.brokerage.orders -> src.brokerage.execution -> src.brokerage.ledger -> disabled broker boundary`

Canonical helper ownership:
`src.services.settlement_service`, `src.services.ledger_service`, `src.services.execution_service`, and `src.brokerage.settlement`.

## Scope Reviewed
The following remaining wrapper-only execution helpers were reviewed:
`automation_scheduler/settlement_rule_checker.py`
`automation_scheduler/settlement_discovery.py`
`automation_scheduler/audit_ledger.py`
`automation_scheduler/institutional_audit_ledger.py`
`automation_scheduler/strategy_performance_ledger.py`
`automation_scheduler/broker_quality_scoring.py`
`automation_scheduler/small_account_strategy.py`
`automation_scheduler/manifold_no_bet_detector.py`
`automation_scheduler/institutional_execution_desk.py`

Relocated compatibility equivalents:
`src/automation_scheduler_legacy/settlement_rule_checker.py`
`src/automation_scheduler_legacy/settlement_discovery.py`
`src/automation_scheduler_legacy/audit_ledger.py`
`src/automation_scheduler_legacy/institutional_audit_ledger.py`
`src/automation_scheduler_legacy/strategy_performance_ledger.py`
`src/automation_scheduler_legacy/broker_quality_scoring.py`
`src/automation_scheduler_legacy/small_account_strategy.py`
`src/automation_scheduler_legacy/manifold_no_bet_detector.py`
`src/automation_scheduler_legacy/institutional_execution_desk.py`

## Scan Results
Runtime references: none.
Test references: none.
Doc-only references: historical proof only.

## Delete-Readiness Classification
All nine wrappers are `DELETE_READY_AFTER_PROOF`.

## Canonical Replacement Map
- `settlement_rule_checker.py` -> `src.brokerage.settlement.compare_settlement_rules`
- `settlement_discovery.py` -> `src.services.settlement_service`
- `audit_ledger.py` -> `src.services.ledger_service`
- `institutional_audit_ledger.py` -> `src.services.ledger_service`
- `strategy_performance_ledger.py` -> `src.services.ledger_service`
- `broker_quality_scoring.py` -> `src.services.execution_service`
- `small_account_strategy.py` -> `src.services.execution_service`
- `manifold_no_bet_detector.py` -> `src.services.execution_service`
- `institutional_execution_desk.py` -> `src.services.execution_service`

## Required Statement
Only proof-backed wrapper-only execution helpers are deleted in the later deletion step. Runtime modules, dashboard files, entrypoints, live clients, AI modules, brokerage modules, and connector scaffolds remain preserved.
