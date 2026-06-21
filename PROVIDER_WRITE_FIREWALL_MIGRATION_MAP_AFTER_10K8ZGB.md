# Provider Write Firewall Migration Map After 10K8ZGB

| Old Owner | New Owner | Compatibility Wrapper | Migration Status | Deletion Readiness |
| --- | --- | --- | --- | --- |
| `automation_scheduler/provider_write_firewall.py` | `src.providers.policy.write_firewall` | `automation_scheduler/provider_write_firewall.py` | runtime behavior redirected; shim only | not yet delete-ready |

## Canonical Behavior
- The canonical policy module owns `check_provider_write_attempt` and related scaffold helpers.
- The legacy file re-exports canonical symbols only.

## Compatibility Wrapper Scope
- Keeps legacy imports working for historical tests and any downstream compatibility callers.

## Migration Status
- Runtime consumers are redirected.
- The legacy module no longer owns runtime behavior.
- compatibility-only wrapper remains on disk for legacy import paths.

## Next Step
- Redirect or retire the remaining legacy-path tests before any deletion batch.
