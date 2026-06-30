# Provider Security Migration Map After 10K8ZMT

## `src.automation_scheduler_legacy.provider_allowlist`

Migrated to `src.providers.policy.allowlist`.

- `KALSHI_ORDER_HINTS`
- `classify_provider`
- `provider_allowlist_response`

## `src.automation_scheduler_legacy.security_event_types`

Retired as duplicate compatibility-only code.

## `src.automation_scheduler_legacy.owner_approval_gate`

Retired. Canonical implementation remains in `src.security.owner_approval_gate`.

## `src.automation_scheduler_legacy.risk_limit_guard`

Retired. Canonical implementation remains in `src.security.risk_limit_guard`.

