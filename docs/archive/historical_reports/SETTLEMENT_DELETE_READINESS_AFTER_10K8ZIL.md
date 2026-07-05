# Settlement Delete Readiness After 10K8ZIL

## Decision

No settlement wrapper is classified `DELETE_READY_AFTER_PROOF` in this phase.

## Wrapper classifications

- `automation_scheduler/settlement_rule_checker.py` - `COMPATIBILITY_WRAPPER_ONLY`
- `automation_scheduler/settlement_discovery.py` - `ACTIVE_RUNTIME_DEPENDENCY`

## Blockers

- Wrapper-path runtime imports remain in the scheduler package
- Proof tests still cover wrapper import compatibility
- The canonical paths are present, but the wrappers are still required for compatibility

## Next step

Redirect the remaining runtime and test call sites to `src.brokerage.settlement` and
`src.services.settlement_service`, then re-run delete-proof.
