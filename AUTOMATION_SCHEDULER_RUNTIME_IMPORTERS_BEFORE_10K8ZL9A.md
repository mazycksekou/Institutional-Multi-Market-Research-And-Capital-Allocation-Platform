# Automation Scheduler Runtime Importers Before 10K8ZL9A

The eight runtime files that directly referenced `automation_scheduler` before this phase were:

- `main.py`
- `streamlit_app.py`
- `src/api/automation_review_outcomes_routes.py`
- `src/api/provider_status_routes.py`
- `src/brokerage/readiness.py`
- `src/services/execution_service.py`
- `src/services/ledger_service.py`
- `src/services/settlement_service.py`

Observed pre-phase ownership:

- Dashboard/bootstrap code imported scheduler helpers directly.
- API route modules imported scheduler compaction and validation helpers directly.
- Brokerage readiness imported scheduler-owned approval and security helpers directly.
- Execution, ledger, and settlement services imported scheduler-owned helper modules directly.

No scheduler files were deleted in this batch.
