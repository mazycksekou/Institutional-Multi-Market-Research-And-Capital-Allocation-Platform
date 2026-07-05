# Active Runtime Test Gate

The active gate now focuses on current product behavior instead of historical migration evidence.

Included:

- `tests/test_architecture_src_only_runtime.py`
- `tests/test_architecture_no_legacy_executable_refs.py`
- `tests/test_architecture_no_ignored_source_files.py`
- `tests/test_architecture_docs_paths.py`
- active behavior tests such as `tests/test_audit_log.py`
- active local-platform coverage such as `tests/test_phase3b_local_data_platform.py`
- smoke and ops checks

Excluded from the active gate:

- archived migration-proof tests marked `architecture_archive`

