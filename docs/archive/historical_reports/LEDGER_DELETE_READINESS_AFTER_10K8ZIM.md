# Ledger Delete Readiness After 10K8ZIM

## Decision

No ledger wrapper is classified `DELETE_READY_AFTER_PROOF` in this phase.

## Wrapper classifications

- `automation_scheduler/audit_ledger.py` - `ACTIVE_RUNTIME_DEPENDENCY`
- `automation_scheduler/institutional_audit_ledger.py` - `ACTIVE_RUNTIME_DEPENDENCY`
- `automation_scheduler/strategy_performance_ledger.py` - `COMPATIBILITY_WRAPPER_ONLY`

## Blockers

- Runtime code still imports the wrapper paths
- Proof tests still cover wrapper compatibility
- The canonical service exists, but the wrappers remain required for compatibility

## Next step

Redirect remaining runtime/test call sites to `src.services.ledger_service`, then re-run delete proof.
