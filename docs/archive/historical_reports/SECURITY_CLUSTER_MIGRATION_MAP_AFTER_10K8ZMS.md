# SECURITY CLUSTER Migration Map

## `src.automation_scheduler_legacy.ai_provider_security`

Migrated to `src.security.ai_provider_security`.

- `AI_PROVIDER_SELECTED`
- `AI_PROVIDER_REJECTED`
- `FORBIDDEN_PROVIDER_REJECTED`
- `_timeout_seconds`
- `get_ai_provider_config`
- `evaluate_ai_provider`

## `src.automation_scheduler_legacy.hard_gate_policy`

Migrated to `src.security.hard_gate_policy`.

- `HARD_GATE_NAMES`
- `VALID_EXECUTION_MODES`
- `ANALYSIS_PROVIDER_CLASSES`
- `_truthy`
- `_provider_allowlist_passed`
- `evaluate_hard_gates`

## `src.automation_scheduler_legacy.security_readiness_report`

Migrated to `src.services.security_readiness`.

- `build_security_readiness_report`

## Supporting canonical helpers

- `src.security.owner_approval_gate`
- `src.security.risk_limit_guard`

