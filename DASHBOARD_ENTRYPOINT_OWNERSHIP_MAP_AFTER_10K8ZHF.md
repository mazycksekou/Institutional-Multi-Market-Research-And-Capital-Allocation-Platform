# Dashboard Entrypoint Ownership Map After 10K8ZHF

| File | Classification | Notes |
| --- | --- | --- |
| `main.py` | `KEEP_ENTRYPOINT_OR_DASHBOARD` | Bootstrap shell that wires services, routes, and compatibility wrappers together. |
| `streamlit_app.py` | `KEEP_ENTRYPOINT_OR_DASHBOARD` | Display/UI shell that orchestrates dashboard data and previews. |

## Observed Behavior

- `main.py` still performs bootstrap work and import-time configuration, so it should remain a shell boundary rather than a deletion candidate.
- `streamlit_app.py` still pulls display helpers from `automation_scheduler` and should remain a UI shell.
- Neither file should own provider, connector, or core math logic.

## Boundary Reminder

- Keep the dashboard thin.
- Keep entrypoints thin.
- Avoid moving connector or provider ownership into UI/bootstrap code.
