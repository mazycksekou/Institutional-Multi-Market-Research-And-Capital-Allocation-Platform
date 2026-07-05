# Scheduler Name Retirement Map

The legacy scheduler-named facade surface has been retired from active Python imports.

| Responsibility | Old Name | New Canonical Name | Status |
|---|---|---|---|
| Dashboard compatibility facade file | `src/services/automation_scheduler_facade.py` | `src/services/runtime_facade.py` | Renamed |
| Dashboard import alias in `main.py` | `automation_scheduler` | `dashboard_facade` | Renamed |
| Provider status route import alias | `automation_scheduler` | `dashboard_facade` | Renamed |
| Route dependency parameter name | `automation_scheduler_dep` | `dashboard_facade_dep` | Renamed |

Active executable imports no longer target the retired scheduler facade path.

