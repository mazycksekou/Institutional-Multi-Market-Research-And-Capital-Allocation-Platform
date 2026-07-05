# Test Suite Architecture Cleanup

The legacy migration-proof test surface was separated from the active product gate.

## Active tests

- Product and architecture enforcement tests remain active
- `tests/test_phase1_legacy_inventory.py` remains active
- `tests/test_phase3b_local_data_platform.py` remains active

## Archived migration-proof tests

- Historical `test_phase10k*` migration-proof tests that reference retired legacy paths or root phase documents are archived by `tests/conftest.py`
- Archived tests are marked `architecture_archive`
- Archived tests do not block the current active gate

## Outcome

- Active behavior tests continue to run
- Historical migration evidence remains available
- Deleted file expectations no longer block product development
