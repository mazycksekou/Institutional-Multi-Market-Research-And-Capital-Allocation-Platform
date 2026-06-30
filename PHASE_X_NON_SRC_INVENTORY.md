# PHASE X Non-Src Inventory

- Total tracked non-src Python files: 552
- Delete-ready after proof: 541
- Remaining blockers: 11

## Non-Delete-Ready Files

| Path | Classification | Canonical Target | Runtime Imports | Test Imports | Script Imports | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| api_server.py | UNSAFE_TO_TOUCH, ACTIVE_TEST_DEPENDENCY | src.api.server | 0 | 1 | 0 | preserve |
| main.py | UNSAFE_TO_TOUCH, ACTIVE_RUNTIME_DEPENDENCY | src.api.app | 1 | 0 | 0 | preserve |
| scripts/analyze_json_data.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | src.scripts | 0 | 1 | 1 | review |
| scripts/daily_data_hygiene.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | src.scripts | 0 | 1 | 1 | review |
| scripts/init_sports_master_db.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | src.scripts | 0 | 1 | 1 | review |
| scripts/ops_check.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | src.scripts | 0 | 1 | 1 | review |
| scripts/r2_archive_pipeline.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | src.scripts | 0 | 1 | 1 | review |
| scripts/smoke_test.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | src.scripts | 0 | 1 | 1 | review |
| streamlit_app.py | UNSAFE_TO_TOUCH | src.services.streamlit_dashboard_facade | 0 | 0 | 0 | preserve |
| tests/support/action_imports.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | src.tests.support | 0 | 61 | 0 | review |
