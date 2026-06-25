# Automation Scheduler Runtime Redirection Map After 10K8ZL9A

| Runtime file | Removed scheduler import(s) | New `src.*` target(s) |
| --- | --- | --- |
| `main.py` | `automation_scheduler`, `automation_scheduler.data_paths`, `automation_scheduler.response_compactor` | `src.services.automation_scheduler_facade` |
| `streamlit_app.py` | `automation_scheduler.streamlit_dashboard_data`, `source_event_link_resolver`, `feature_ablation_lab`, `zero_dte_fixture_template`, `model_data_field_catalog`, `historical_data_sources` | `src.services.streamlit_dashboard_facade` |
| `src/api/automation_review_outcomes_routes.py` | local imports of `automation_scheduler.collector_scheduled_runner.validate_cron_token` | `src.api.automation_security.validate_cron_token` already imported at module scope |
| `src/api/provider_status_routes.py` | `automation_scheduler`, `automation_scheduler.response_compactor` | `src.services.automation_scheduler_facade` |
| `src/brokerage/readiness.py` | scheduler approval/security/allowlist helpers | `src.brokerage.readiness_support`, `src.providers.policy.write_firewall`, `src.research.maturity`, `src.services.ledger_service` |
| `src/services/execution_service.py` | scheduler execution, scoring, and queue helpers | `src.services.execution_support`, `src.services.ledger_service` |
| `src/services/ledger_service.py` | scheduler data-path and security helpers | `src.services.ledger_support` |
| `src/services/settlement_service.py` | scheduler data-path and outcome helpers | `src.services.settlement_support`, `src.brokerage.settlement`, `src.services.prediction_market_runtime_bridge` |

The direct `automation_scheduler` imports were replaced with `src.*` bridge modules or with existing canonical service imports.
