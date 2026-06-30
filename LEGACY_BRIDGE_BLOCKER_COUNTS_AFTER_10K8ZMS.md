# Legacy Bridge Blocker Counts After 10K8ZMS

## Direct active import blockers

- `src.automation_scheduler_legacy.ai_provider_security`: 0
- `src.automation_scheduler_legacy.hard_gate_policy`: 0
- `src.automation_scheduler_legacy.security_readiness_report`: 0

## Heuristic inventory note

The targeted inventory scan still reports wrapper-style counts of `3` runtime importers, `12` test importers, and `1` internal importer for each file because the package-root compatibility bridge remains. Those counts are not direct references to the deleted files and no longer block deletion once the direct import scan is clean.
