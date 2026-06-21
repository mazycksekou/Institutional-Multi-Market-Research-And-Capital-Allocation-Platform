# Provider Registry Delete Readiness After 10K8ZGA

## Decision
`automation_scheduler/provider_registry.py` is delete-ready from the runtime dependency perspective after canonical redirection, but it is not deleted in this phase.

## Why
- Runtime callers now import `src.providers.registry`.
- Canonical registry behavior includes the legacy alias snapshot when requested.
- The compatibility shim remains importable for downstream safety.

## Remaining Blocker
- `automation_scheduler/provider_write_firewall.py`

## What Is Still Protected
- No deletion occurred in this phase.
- No runtime behavior changed.
- No live calls were introduced.
- No credentials were read at import time.

## Next Recommended Phase
- Prove whether `automation_scheduler/provider_write_firewall.py` can be retired, redirected, or reduced to compatibility-only behavior after this registry blocker is removed from the runtime path.
