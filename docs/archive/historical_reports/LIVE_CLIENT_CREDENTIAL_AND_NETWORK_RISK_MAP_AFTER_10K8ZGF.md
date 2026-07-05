# Live Client Credential and Network Risk Map After 10K8ZGF

## Risk Map

| Surface | Credential risk | Network risk | Evidence | Future bucket |
|---|---|---|---|---|
| `kalshi_client.py` | `CREDENTIAL_RISK` (import-time `KALSHI_BASE_URL` env access) | `NETWORK_RISK` (`requests`) | raw HTTP client functions | `src.connectors.prediction_market_data` |
| `providers/kalshi_provider.py` | `CREDENTIAL_RISK` (`KALSHI_ENABLED`, `KALSHI_BASE_URL`) | `NETWORK_RISK` (`requests`) | enrichment helper calls live markets | `src.connectors.prediction_market_data` for live half, `src.providers.prediction_markets` for normalization half |
| `sharp_client.py` | `CREDENTIAL_RISK` (caller-supplied API key) | `NETWORK_RISK` (`requests`) | raw sportsbook client functions | `src.connectors.odds_data` |
| `providers/sharp_provider.py` | `CREDENTIAL_RISK` (`SHARP_API_KEY`, `SHARP_API_BASE_URL`) | `NETWORK_RISK` (`requests`) | enrichment helper calls live odds | `src.connectors.odds_data` for live half |
| `betting_providers/kalshi_api.py` | `CREDENTIAL_RISK` (`KALSHI_API_KEY_ID`, `KALSHI_PRIVATE_KEY`) | `NETWORK_RISK` (`requests`) | live vendor adapter | `src.connectors.prediction_market_data` |
| `betting_providers/sharp_api.py` | `CREDENTIAL_RISK` (`SHARP_API_KEY`, `SHARP_API_BASE_URL`) | `NETWORK_RISK` (`requests`) | live vendor adapter | `src.connectors.odds_data` |
| `betting_providers/the_odds_api.py` | `CREDENTIAL_RISK` (`THE_ODDS_API_KEY`, `ODDS_API_KEY`, default envs) | `NETWORK_RISK` (`httpx.AsyncClient`) | async sportsbook client | `src.connectors.odds_data` |
| `betting_providers/sportsgameodds.py` | `CREDENTIAL_RISK` (`SPORTSGAMEODDS_API_KEY`, `SPORTSGAMEODDS_BASE_URL`) | `NETWORK_RISK` (`httpx.AsyncClient`) | async sportsbook client | `src.connectors.odds_data` |
| `automation_scheduler/kalshi_readonly_adapter.py` | `CREDENTIAL_RISK` (`KALSHI_API_KEY`, `KALSHI_API_SECRET`, related envs) | `NETWORK_RISK` (`httpx`) | read-only adapter still performs live fetches | `src.connectors.prediction_market_data` |
| `automation_scheduler/kalshi_market_provider.py` | `CREDENTIAL_RISK` via read-only adapter | `NETWORK_RISK` via read-only adapter | snapshot getter calls live adapter | `src.connectors.prediction_market_data` |
| `automation_scheduler/sharp_sportsbook_adapter.py` | `CREDENTIAL_RISK` (`SHARP_API_KEY`, `SHARP_API_BASE_URL`, related envs) | `NETWORK_RISK` (`httpx`) | sportsbook adapter still performs live fetches | `src.connectors.odds_data` |
| `automation_scheduler/sportsbook_odds_provider.py` | `CREDENTIAL_RISK` via sportsbook adapter | `NETWORK_RISK` via sportsbook adapter | snapshot getter calls live adapter | `src.connectors.odds_data` |
| `src/api/provider_status_routes.py` | none directly | bridge-only | depends on `automation_scheduler` health/registry | service orchestration only |
| `src/api/market_metadata_routes.py` | none directly | none directly | route bridge to canonical `ProviderRouter` | service orchestration only |
| `src/api/model_card_service.py` | none directly | none directly | canonical router consumer | service orchestration only |
| `src/services/enrichment_service.py` | none directly | bridge-only | uses legacy provider enrichers | service orchestration only |
| `screenshot_intake.py` | none directly | none directly | parses and enriches screenshots | service orchestration only |
| `main.py` | `CREDENTIAL_RISK` (`ACTION_API_KEY`) | `NETWORK_RISK` via imported runtime stack | entrypoint/orchestration shell | unsafe to touch |
| `streamlit_app.py` | none directly | `NETWORK_RISK` via dashboard/runtime stack | dashboard shell | unsafe to touch |

## Findings
- The highest-risk files are the live client and adapter modules that both read credentials and make HTTP calls.
- The bridge layers do not own the live clients, but they remain coupled to them and therefore are not deletion candidates in this batch.
- `main.py` and `streamlit_app.py` remain runtime-critical shells and are explicitly not deletion candidates.

