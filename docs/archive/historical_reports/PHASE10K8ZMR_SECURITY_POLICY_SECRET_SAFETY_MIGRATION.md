# PHASE 10K8ZMR Security Policy / Secret Safety Migration

## Summary

Security policy and secret-safety logic now live under `src.security`:

- `src.automation_scheduler_legacy.security_policy` -> `src.security.policy`
- `src.automation_scheduler_legacy.secret_safety` -> `src.security.secret_safety`

The two legacy source files were deleted after the repo-wide import scan showed no direct active imports to those module paths.

## Canonical ownership

- `src.security.policy` owns safety flags, capability boundary checks, and execution-authority violation detection.
- `src.security.secret_safety` owns redaction, secret detection, and leak assertions.
- `src.security.__init__` re-exports the canonical symbols for convenience.

## Validation

- Canonical imports load without credential reads at import time.
- No runtime, test, or internal Python import still targets the deleted module paths.
- Security framework regression tests remain green.

