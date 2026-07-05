# PHASE10K8ZMT Provider Security Surface Retirement

## Scope

This batch retires the last provider/security compatibility wrappers that still lived under `src.automation_scheduler_legacy/`:

- `provider_allowlist.py`
- `security_event_types.py`
- `owner_approval_gate.py`
- `risk_limit_guard.py`

## Canonical ownership

- Provider allowlist and Kalshi classification now live in `src.providers.policy.allowlist`
- Owner-approval gating remains in `src.security.owner_approval_gate`
- Risk-limit gating remains in `src.security.risk_limit_guard`
- The old composite `security_event_types.py` wrapper is no longer needed and was removed

## Result

The active runtime and test import surface has been redirected away from the deleted wrappers.
The remaining legacy retirement work now shifts back to the larger market-intelligence and data subsystems.

