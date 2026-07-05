# SECURITY CLUSTER Caller Scan

## Direct legacy-module refs

- `src.automation_scheduler_legacy.ai_provider_security`: 0
- `src.automation_scheduler_legacy.hard_gate_policy`: 0
- `src.automation_scheduler_legacy.security_readiness_report`: 0

## Inventory heuristic snapshot

The targeted inventory scan still classifies the three files as compatibility wrappers and, because of package-root compatibility resolution, reports non-zero wrapper-style counts for each file:

- runtime importers: 3
- test importers: 12
- internal importers: 1

## Notes

The repo still contains other legacy bridge modules, but none of them actively import the three deleted security-cluster files anymore.
