# Archived Migration Tests

Archived migration-proof tests are identified by `tests/conftest.py` when they:

- start with `test_phase`
- and reference retired legacy paths or root phase documents

Current archived count: `265`

Representative archived patterns:

- root `PHASE*.md` proof documents
- `src/automation_scheduler_legacy/...`
- `automation_scheduler_legacy`

Archived tests are still kept in the repository for historical audit value, but they no longer block the active product gate.
