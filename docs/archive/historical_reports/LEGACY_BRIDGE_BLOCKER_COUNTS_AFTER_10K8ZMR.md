# Legacy Bridge Blocker Counts After 10K8ZMR

## Removed blockers

- Direct active imports into `src.automation_scheduler_legacy.security_policy`: 0
- Direct active imports into `src.automation_scheduler_legacy.secret_safety`: 0

## Current state

- The legacy package still exists for the broader bridge decommission.
- These two security modules are no longer blockers for deletion.
- Their logic is now owned by `src.security`.

