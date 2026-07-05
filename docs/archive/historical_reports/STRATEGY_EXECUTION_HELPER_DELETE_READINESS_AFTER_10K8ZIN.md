# Strategy / Execution Helper Delete Readiness After 10K8ZIN

## Decision

No strategy/execution helper wrapper is classified `DELETE_READY_AFTER_PROOF` in this phase.

## Wrapper classifications

- `automation_scheduler/broker_quality_scoring.py` - `ACTIVE_RUNTIME_DEPENDENCY`
- `automation_scheduler/small_account_strategy.py` - `ACTIVE_RUNTIME_DEPENDENCY`
- `automation_scheduler/manifold_no_bet_detector.py` - `ACTIVE_RUNTIME_DEPENDENCY`
- `automation_scheduler/institutional_execution_desk.py` - `ACTIVE_RUNTIME_DEPENDENCY`

## Blockers

- Runtime code still imports the wrapper paths
- Proof tests still cover wrapper compatibility
- The canonical service exists, but wrapper deletion is not yet proof-backed

## Next step

Redirect remaining runtime and test call sites to `src.services.execution_service`, then re-run delete proof.
