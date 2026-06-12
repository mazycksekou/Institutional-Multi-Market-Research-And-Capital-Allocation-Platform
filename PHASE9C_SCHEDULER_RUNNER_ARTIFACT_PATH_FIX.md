# Phase 9C Scheduler Runner Artifact Path Fix

Generated: 2026-06-12T18:56:24

- Restored broken insertion.
- Preserved `from __future__ import annotations` at the top of the file.
- Inserted helper after the complete import block.
- `review_queue_write_path` now resolves to an existing project-root/data path when possible.
- `paper_ledger_write_path` now resolves to an existing project-root/data path when possible.

PATCH_APPLIED: `True`
