# Current Dirty Worktree Inventory After 10K8ZMP

## Summary
- Modified files: 307
- Deleted files: 329
- Untracked files: 13

## High-level classification
- `VALID_AUTOMATION_SCHEDULER_REMOVAL`: top-level scheduler deletions and related redirect docs/tests
- `VALID_SRC_CANONICAL_MIGRATION`: canonical `src.*` modules updated to absorb scheduler ownership
- `VALID_TEST_REDIRECTION`: tests redirected away from top-level scheduler ownership
- `VALID_PHASE_DOC_UPDATE`: phase docs and blocker ledgers updated
- `VALID_PARITY_FIX`: compatibility and parity fixes in canonical helpers
- `UNTRACKED_BUT_REQUIRED`: `src/automation_scheduler_legacy/` and checkpoint proof docs
- `UNTRACKED_ACCIDENTAL`: none identified
- `UNRELATED_CHANGE`: none identified from the current inspection
- `DANGEROUS_OR_UNKNOWN`: none identified from the current inspection

## Notes
- The worktree is large because the scheduler removal touched many legacy and canonical surfaces.
- The untracked compatibility bridge is deliberate, not accidental.
