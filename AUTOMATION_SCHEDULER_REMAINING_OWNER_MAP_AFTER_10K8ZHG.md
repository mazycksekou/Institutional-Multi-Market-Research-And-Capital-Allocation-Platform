# Automation Scheduler Remaining Owner Map After 10K8ZHG

| File | Classification | Why |
| --- | --- | --- |
| `automation_scheduler/scheduler_runner.py` | `UNSAFE_TO_TOUCH` | Runtime orchestration remains too coupled for this phase. |
| `automation_scheduler/calibration_collector.py` | `SERVICE_ORCHESTRATION_OWNER` | Local orchestration/reporting; candidate for future service migration. |
| `automation_scheduler/settlement_discovery.py` | `MIGRATE_TO_SRC_SERVICES` | Discovery/reporting work that should live in services. |
| `automation_scheduler/prediction_market_outcome_candidates.py` | `MIGRATE_TO_SRC_SERVICES` | Outcome evidence selection belongs in services. |
| `automation_scheduler/streamlit_dashboard_data.py` | `DASHBOARD_LAYER_ONLY` | Dashboard display and report shaping. |
| `automation_scheduler/provider_allowlist.py` | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy provider classification helper. |
| `automation_scheduler/data_source_registry.py` | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy registry shell; not yet delete-ready. |
| `automation_scheduler/kalshi_monitor.py` | `COMPATIBILITY_SHIM_CANDIDATE` | Historical compatibility surface. |
| `automation_scheduler/kalshi_scoring.py` | `COMPATIBILITY_SHIM_CANDIDATE` | Historical compatibility surface. |
| `automation_scheduler/kalshi_readonly_readiness.py` | `COMPATIBILITY_SHIM_CANDIDATE` | Readiness/reporting shell. |
| `automation_scheduler/collector_scheduled_runner.py` | `SERVICE_ORCHESTRATION_OWNER` | Scheduler orchestration wrapper. |
| `automation_scheduler/kalshi_adapter_contract.py` | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy adapter contract surface. |
| `automation_scheduler/sportsbook_adapter_contract.py` | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy adapter contract surface. |

## Decommission Note

- The scheduler basket still owns orchestration and compatibility shells.
- The next phase should continue moving safe orchestration into `src.services` and leave the historical shells untouched until proof is complete.
