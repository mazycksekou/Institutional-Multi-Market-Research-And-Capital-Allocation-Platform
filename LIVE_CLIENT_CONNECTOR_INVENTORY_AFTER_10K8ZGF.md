# Live Client Connector Inventory After 10K8ZGF

## Inventory Overview

| Target | Classification tag | Current role | Future destination | Notes |
|---|---|---|---|---|
| `kalshi_client.py::get_kalshi_market`, `get_kalshi_orderbook`, `get_kalshi_market_snapshot` | `RUNTIME_LIVE_CLIENT_OWNER` | Root-level live prediction-market client | `src.connectors.prediction_market_data` | Uses `requests` and import-time base URL env. |
| `providers/kalshi_provider.py::normalize_kalshi_probability_market` | `PROVIDER_NORMALIZATION_ONLY` | Canonical normalization helper hidden in legacy file | `src.providers.prediction_markets` | Pure normalization, no network. |
| `providers/kalshi_provider.py::enrich_with_kalshi` | `CONNECTOR_READY_WITH_STUBS` | Legacy live enrichment helper | `src.connectors.prediction_market_data` | Live fetch + env gate. |
| `sharp_client.py::get_sharp_active_events`, `get_sharp_event_odds` | `RUNTIME_LIVE_CLIENT_OWNER` | Root-level live sportsbook client | `src.connectors.odds_data` | Uses `requests` and caller-supplied API key. |
| `providers/sharp_provider.py::enrich_with_sharp` | `CONNECTOR_READY_WITH_STUBS` | Legacy live enrichment helper | `src.connectors.odds_data` | Reads env and calls `requests`. |
| `betting_providers/kalshi_api.py::KalshiApiAdapter` | `RUNTIME_LIVE_CLIENT_OWNER` | Vendor client adapter | `src.connectors.prediction_market_data` | Reads API key/private key env. |
| `betting_providers/sharp_api.py::SharpApiAdapter` | `RUNTIME_LIVE_CLIENT_OWNER` | Vendor client adapter | `src.connectors.odds_data` | Reads API key env and calls `requests`. |
| `betting_providers/the_odds_api.py::TheOddsApiAdapter` | `RUNTIME_LIVE_CLIENT_OWNER` | Vendor client adapter | `src.connectors.odds_data` | Uses `httpx.AsyncClient` and API key env. |
| `betting_providers/sportsgameodds.py::SportsGameOddsAdapter` | `RUNTIME_LIVE_CLIENT_OWNER` | Vendor client adapter | `src.connectors.odds_data` | Uses `httpx.AsyncClient` and API key env. |
| `automation_scheduler/kalshi_readonly_adapter.py::KalshiReadonlyAdapter` | `CONNECTOR_READY_WITH_STUBS` | Read-only adapter shell | `src.connectors.prediction_market_data` | Health/config helpers are inert; fetch path still live. |
| `automation_scheduler/kalshi_market_provider.py::normalize_kalshi_snapshot`, `validate_kalshi_snapshot`, `write_kalshi_snapshot`, `summarize_kalshi_snapshot` | `CONNECTOR_READY_INERT` | Snapshot normalization/helpers | `src.providers.prediction_markets` / `src.connectors.prediction_market_data` | Pure local transforms and storage helpers. |
| `automation_scheduler/kalshi_market_provider.py::get_kalshi_snapshot` | `RUNTIME_LIVE_CLIENT_OWNER` | Live wrapper over read-only adapter | `src.connectors.prediction_market_data` | Unsafe until connector migration. |
| `automation_scheduler/sharp_sportsbook_adapter.py::SharpSportsbookAdapter` | `CONNECTOR_READY_WITH_STUBS` | Read-only sportsbook adapter shell | `src.connectors.odds_data` | Fetch path still live. |
| `automation_scheduler/sportsbook_odds_provider.py::normalize_sportsbook_snapshot`, `validate_sportsbook_snapshot`, `get_valid_normalized_records`, `write_sportsbook_snapshot`, `summarize_sportsbook_snapshot` | `CONNECTOR_READY_INERT` | Snapshot normalization/helpers | `src.providers.sportsbooks` / `src.connectors.odds_data` | Pure local transforms and storage helpers. |
| `automation_scheduler/sportsbook_odds_provider.py::get_sportsbook_snapshot` | `RUNTIME_LIVE_CLIENT_OWNER` | Live wrapper over sportsbook adapter | `src.connectors.odds_data` | Unsafe until connector migration. |
| `src/services/enrichment_service.py` | `SERVICE_ORCHESTRATION_ONLY` | Screenshot/ticket enrichment orchestration | `src.services` | Uses legacy provider enrichers. |
| `src/api/provider_status_routes.py` | `SERVICE_ORCHESTRATION_ONLY` | API bridge to provider health/registry | `src.services` / thin API shell | Still depends on `automation_scheduler`. |
| `src/api/market_metadata_routes.py` | `SERVICE_ORCHESTRATION_ONLY` | API bridge to provider routing | `src.services` / thin API shell | Uses canonical `ProviderRouter`. |
| `src/api/model_card_service.py` | `SERVICE_ORCHESTRATION_ONLY` | Model-card orchestration | `src.services` / thin API shell | Uses canonical `ProviderRouter`. |
| `screenshot_intake.py` | `SERVICE_ORCHESTRATION_ONLY` | Screenshot normalization/orchestration | `src.services` | No live fetch of its own. |
| `main.py` | `UNSAFE_TO_TOUCH` | Entrypoint/orchestration shell | remains as shell | Not an automatic deletion candidate. |
| `streamlit_app.py` | `UNSAFE_TO_TOUCH` | Dashboard shell | remains as shell | Not an automatic deletion candidate. |

## Notes
- `src.connectors.market_data` has no direct reviewed live-client owner in this batch; it remains reserved for future stock / 0DTE live access.
- `main.py` and `streamlit_app.py` are explicitly not automatic deletion candidates.

