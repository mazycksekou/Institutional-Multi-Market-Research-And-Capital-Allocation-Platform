# PHASE10K8ZIC Execution Ownership Migration

## What moved
- `automation_scheduler/execution_gatekeeper.py` now delegates to
  `src.brokerage.readiness.evaluate_future_execution_eligibility`.
- `automation_scheduler/execution_authorization.py` now delegates to
  `src.brokerage.readiness.evaluate_execution_authorization`.
- `automation_scheduler/paper_trade_ledger.py` and
  `automation_scheduler/paper_decision_ledger.py` now map to canonical
  brokerage ledger events while preserving file-backed compatibility.
- `src.services.decision_engine` can build a live-shaped execution plan with
  brokerage order/execution/readiness contracts.
- `src/brokerage/readiness.py` is the canonical execution-authorization and
  future-eligibility owner.

## Canonical ownership
- `src.brokerage.orders`
- `src.brokerage.execution`
- `src.brokerage.ledger`
- `src.brokerage.readiness`
- `src.services.decision_engine`

## Compatibility status
- Legacy scheduler modules remain importable.
- Public symbols remain available.
- No live trading is enabled.
- No separate paper-only canonical path exists.
