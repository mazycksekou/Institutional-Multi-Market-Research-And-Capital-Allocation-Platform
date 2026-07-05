# LEGACY_RUNTIME_DEPENDENCY_REPORT_AFTER_10K8ZG2

## Executive Summary
The runtime dependency chain is still concentrated in `main.py`, `streamlit_app.py`, `src/api`, `src/services`, and the legacy vendor/provider modules.

Canonical `src/providers` and `src/connectors` are import-safe, but the application still depends on legacy runtime owner code.

No deletion occurs in this phase. This phase establishes deletion readiness evidence only.

## Search Methodology
Scans were performed across:
- `main.py`
- `streamlit_app.py`
- `src/api/*`
- `src/services/*`
- `tests/*`
- `providers/*`
- `betting_providers/*`
- `automation_scheduler/*`

Search terms included:
- `providers`
- `betting_providers`
- `automation_scheduler`
- `kalshi`
- `sharp`
- `provider_router`
- `odds_provider_router`
- `sportsbook_odds_provider`
- `provider_registry`
- `provider_health`
- `provider_contracts`

## High-Signal Runtime Dependencies
### `main.py`
- imports `betting_providers.aliases`
- imports `betting_providers.base.PREDICTION_MARKET`
- imports `betting_providers.provider_router.ProviderRouter`
- imports `automation_scheduler`
- imports `automation_scheduler.data_paths`
- imports `automation_scheduler.response_compactor`

### `streamlit_app.py`
- imports `automation_scheduler.streamlit_dashboard_data`
- imports `automation_scheduler.source_event_link_resolver`
- imports `automation_scheduler.feature_ablation_lab`
- imports `automation_scheduler.zero_dte_fixture_template`
- imports `automation_scheduler.model_data_field_catalog`
- imports `automation_scheduler.historical_data_sources`

### `src/api/provider_status_routes.py`
- calls provider health and registry functions through `automation_scheduler`
- still exposes `/api/providers/sharp/*` and `/api/providers/kalshi/*` endpoints through legacy scheduler snapshots

### `src/api/model_card_service.py`
- still imports `betting_providers.provider_router.ProviderRouter`

### `src/api/market_metadata_routes.py`
- still depends on the legacy betting/provider router path

### `src/services/enrichment_service.py`
- still imports `providers.kalshi_provider.enrich_with_kalshi`
- still imports `providers.sharp_provider.enrich_with_sharp`

### `src/services/action_betting_service.py`
- still depends on `betting_providers`

### `screenshot_intake.py`
- still imports `providers.odds_provider_router.enrich_ticket`

### Additional legacy runtime dependency paths
- `betting_providers/provider_router.py`
- `betting_providers/base.py`
- `betting_providers/normalization.py`
- `providers/base_provider.py`
- `providers/odds_provider_router.py`
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `automation_scheduler/provider_write_firewall.py`

## Legacy Runtime Modules That Still Own Behavior
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`
- `betting_providers/kalshi_api.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `kalshi_client.py`
- `sharp_client.py`

## Dependency Hotspots
- `requests` is still used by legacy provider/client modules.
- `httpx` is still used by legacy scheduler adapters.
- Environment credential reads still appear in live adapter / client paths.

## Evidence Summary
Line-hit counts from the search pass:
- `providers`: `251`
- `betting_providers`: `31`
- `automation_scheduler`: `885`
- `kalshi`: `920`
- `sharp`: `389`
- `provider_router`: `47`
- `odds_provider_router`: `11`
- `sportsbook_odds_provider`: `6`
- `provider_registry`: `51`
- `provider_health`: `60`
- `provider_contracts`: `36`

## Blocking Conclusion
The repository is not ready for legacy deletion because runtime consumers still depend on the legacy owner modules and the compatibility shims still service live paths.

## Acceptance Results
- Dependency report completed: yes
- No deletion occurred: yes
- No behavior changed: yes
- Repo remained import-safe during review: yes

## Next Phase Recommendation
Shrink only the wrapper layer first, then rewire the dependent API/service/UI entrypoints.
