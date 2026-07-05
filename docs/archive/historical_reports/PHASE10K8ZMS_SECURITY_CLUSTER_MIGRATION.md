# PHASE 10K8ZMS Security Cluster Migration

## Summary

The legacy security cluster has been split into canonical modules:

- `src.security.ai_provider_security`
- `src.security.hard_gate_policy`
- `src.security.owner_approval_gate`
- `src.security.risk_limit_guard`
- `src.services.security_readiness`

The legacy bridge files targeted by this phase were redirected to these canonical modules and then removed after direct import proof showed zero active references.

## Canonical ownership

- AI provider selection and allow/deny audit behavior now live under `src.security.ai_provider_security`.
- Hard gate evaluation now lives under `src.security.hard_gate_policy`.
- Security readiness report composition now lives under `src.services.security_readiness`.
- Owner approval and risk-limit helpers were lifted into `src.security` so the hard-gate path no longer needs the legacy package.

