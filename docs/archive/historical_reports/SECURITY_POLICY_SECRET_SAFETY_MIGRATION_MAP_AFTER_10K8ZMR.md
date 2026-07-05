# SECURITY POLICY / SECRET SAFETY Migration Map

## `src.automation_scheduler_legacy.security_policy`

Moved into `src.security.policy` with the same public API:

- `ALLOWED_AI_PROVIDERS`
- `DEFAULT_AI_PROVIDER`
- `AI_ALLOWED_CAPABILITIES`
- `AI_FORBIDDEN_CAPABILITIES`
- `EXECUTION_TRUE_FIELDS`
- `EXECUTABLE_PAYLOAD_KEYS`
- `FORBIDDEN_ACTION_VALUES`
- `env_bool`
- `locked_safety_flags`
- `kill_switch_state`
- `detect_execution_authority_violations`
- `enforce_ai_capability_boundary`

## `src.automation_scheduler_legacy.secret_safety`

Moved into `src.security.secret_safety` with the same public API:

- `REDACTED`
- `OMITTED`
- `SECRET_KEY_PARTS`
- `RAW_PAYLOAD_KEYS`
- `SECRET_VALUE_PATTERNS`
- `is_secret_key`
- `looks_like_secret_value`
- `redact_string`
- `contains_secret_like_content`
- `redact_sensitive`
- `secret_safety_fields`
- `assert_no_secret_leak`

