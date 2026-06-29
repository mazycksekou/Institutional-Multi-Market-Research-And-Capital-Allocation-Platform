# PHASE X Classification

The current non-src cleanup leaves a small set of compatibility and entrypoint blockers.

- Delete-ready files: 539
- Non-delete-ready files: 10

## Blocked Files

| Path | Classification | Responsibility | Canonical Target | Deletion Risk |
| --- | --- | --- | --- | --- |
| api_server.py | UNSAFE_TO_TOUCH, ACTIVE_TEST_DEPENDENCY | ASGI deployment adapter. | src.api.server | high |
| main.py | UNSAFE_TO_TOUCH, ACTIVE_RUNTIME_DEPENDENCY | Application entrypoint | src.api.app | high |
| scripts/analyze_json_data.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | Read-only JSON/JSONL audit tool for betting-stock-api. | src.scripts | high |
| scripts/daily_data_hygiene.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | Maintenance script | src.scripts | high |
| scripts/init_sports_master_db.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | Initialize the local sports master SQLite database with mock NBA smoke data. | src.scripts | high |
| scripts/ops_check.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | Maintenance script | src.scripts | high |
| scripts/r2_archive_pipeline.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | Maintenance script | src.scripts | high |
| scripts/smoke_test.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | Maintenance script | src.scripts | high |
| streamlit_app.py | UNSAFE_TO_TOUCH | Local Streamlit operator dashboard. | src.services.streamlit_dashboard_facade | high |
| tests/support/action_imports.py | COMPATIBILITY_WRAPPER_ONLY, ACTIVE_TEST_DEPENDENCY | Test module | src.tests.support | high |
