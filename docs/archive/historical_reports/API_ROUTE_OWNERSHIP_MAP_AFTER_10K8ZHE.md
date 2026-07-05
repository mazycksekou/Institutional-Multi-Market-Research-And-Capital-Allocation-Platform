# API Route Ownership Map After 10K8ZHE

| Route File | Current Dependency Shape | Classification | Notes |
| --- | --- | --- | --- |
| `src/api/system_routes.py` | local health/ping shell | `API_LAYER_ONLY` | Thin bootstrap/health routes. |
| `src/api/quant_routes.py` | injected core functions | `API_LAYER_ONLY` | Routes expose core helpers only. |
| `src/api/betting_action_routes.py` | provider router + services | `API_LAYER_ONLY` | Route exposure only; no ownership of math. |
| `src/api/market_metadata_routes.py` | provider router | `API_LAYER_ONLY` | Thin provider metadata route shell. |
| `src/api/market_utility_routes.py` | provider router + model service | `API_LAYER_ONLY` | Legacy odds route names remain compatibility-facing. |
| `src/api/model_card_service.py` | provider router + core backtester | `API_LAYER_ONLY` | Canonical service object under API package. |
| `src/api/performance_routes.py` | automation scheduler injection | `COMPATIBILITY_SHIM_CANDIDATE` | Route shell over legacy scheduler orchestration. |
| `src/api/debug_routes.py` | env/debug readout | `API_LAYER_ONLY` | Diagnostics-only route shell. |
| `src/api/governance_routes.py` | governance reporting | `API_LAYER_ONLY` | API exposure only. |
| `src/api/bet_csv_routes.py` | local bet CSV helpers | `API_LAYER_ONLY` | Storage/ledger surface only. |
| `src/api/betting_metadata_routes.py` | metadata helper routing | `API_LAYER_ONLY` | API exposure only. |
| `src/api/provider_status_routes.py` | `automation_scheduler` health/registry calls | `UNSAFE_TO_TOUCH` | Main remaining API-layer blocker. |
| `src/api/automation_core_routes.py` | `automation_scheduler` injection | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy orchestration route shell. |
| `src/api/automation_data_source_routes.py` | `automation_scheduler` injection | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy orchestration route shell. |
| `src/api/automation_deepseek_routes.py` | `automation_scheduler` injection | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy orchestration route shell. |
| `src/api/automation_institutional_lab_routes.py` | `automation_scheduler` injection | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy orchestration route shell. |
| `src/api/automation_manifold_routes.py` | `automation_scheduler` injection | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy orchestration route shell. |
| `src/api/automation_review_outcomes_routes.py` | `automation_scheduler` injection | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy orchestration route shell. |
| `src/api/automation_run_once_routes.py` | `automation_scheduler` injection | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy orchestration route shell. |
| `src/api/automation_small_account_routes.py` | `automation_scheduler` injection | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy orchestration route shell. |
| `src/api/automation_sport_impact_routes.py` | `automation_scheduler` injection | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy orchestration route shell. |

## Service Dependencies

- `src.api.model_card_service.ModelCardService` -> `src.providers.provider_router.ProviderRouter`, `src.core.backtester`, `src.core.math_utils`, `src.sports.nba_features`
- `src.api.betting_action_routes.register_betting_action_routes` -> injected service dependencies only
- `src.api.market_metadata_routes.register_market_metadata_routes` -> injected provider router only
- `src.api.market_utility_routes.register_market_utility_routes` -> injected provider router and model card service

## Safe Cleanup Order

1. Remove `automation_scheduler` from `provider_status_routes.py` only after canonical provider health/registry and bridge responses fully cover the route contract.
2. Redirect automation route bundles to services/core where safe and local-only.
3. Keep the thin API-only route shells intact.
