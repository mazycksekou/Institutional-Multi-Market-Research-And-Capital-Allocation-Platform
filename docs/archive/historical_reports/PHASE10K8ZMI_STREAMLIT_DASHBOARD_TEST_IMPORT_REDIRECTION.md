# Phase 10K8ZMI Streamlit Dashboard Test Import Redirection

Target:
- `tests/test_streamlit_dashboard_data.py`

Goal:
- Move the streamlit dashboard test away from legacy `automation_scheduler` imports and onto canonical `src.*` modules.

Result:
- The target test file now has zero active `automation_scheduler` imports.
- No scheduler files were deleted in this phase.
- The import surface was redirected to canonical `src.services`, `src.data`, `src.backtesting`, `src.market_intelligence`, and `src.research` modules.

Validation path:
- `python -m py_compile tests/test_streamlit_dashboard_data.py tests/test_phase10k8zmi_streamlit_dashboard_test_import_redirection.py`
- Targeted pytest on the proof test and dashboard test
- Affected historical-data slice
- Local ops smoke
- Full gate
