# Prediction Market Live Client Migration Map After 10K8ZGG

## Migration Map

| Legacy surface | Tag | Canonical destination | Status |
|---|---|---|---|
| `kalshi_client.py` | `RUNTIME_LIVE_CLIENT_OWNER` | `src.connectors.prediction_market_data.transport` / `disabled_client.py` | Transport shape only; disabled live behavior |
| `providers/kalshi_provider.py::enrich_with_kalshi` | `CONNECTOR_READY_WITH_STUBS` | `src.connectors.prediction_market_data.disabled_client` | Live half disabled; normalization split remains separate |
| `providers/kalshi_provider.py::normalize_kalshi_probability_market` | `PROVIDER_NORMALIZATION_ONLY` | `src.providers.prediction_markets` | Normalization only |
| `betting_providers/kalshi_api.py::KalshiApiAdapter` | `RUNTIME_LIVE_CLIENT_OWNER` | `src.connectors.prediction_market_data.configuration`, `auth`, `signing`, `transport` | Adapter shape now connector-owned but disabled |
| `automation_scheduler/kalshi_readonly_adapter.py::KalshiReadonlyAdapter` | `CONNECTOR_READY_WITH_STUBS` | `src.connectors.prediction_market_data.readiness`, `transport` | Read-only wrapper remains disabled |
| `automation_scheduler/kalshi_market_provider.py::normalize_kalshi_snapshot`, `validate_kalshi_snapshot`, `summarize_kalshi_snapshot` | `CONNECTOR_READY_INERT` | `src.providers.prediction_markets` | Pure local snapshot helpers |
| `automation_scheduler/kalshi_market_provider.py::get_kalshi_snapshot` | `RUNTIME_LIVE_CLIENT_OWNER` | `src.connectors.prediction_market_data.transport` | Live wrapper stays disabled |

## Connector-Owned Modules Created
- `configuration.py`
- `auth.py`
- `signing.py`
- `transport.py`
- `readiness.py`
- `disabled_client.py`

## Legacy Modules Remain
- `kalshi_client.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `providers/kalshi_provider.py`

## Compatibility and Deletion Notes
Legacy modules remain importable and are not deleted. Deletion is deferred until downstream consumers are redirected and the disabled connector behavior is fully proven.

## Required Statement
Prediction-market live-client migration is connector-owned but disabled in this phase. This phase does not authorize live API calls, credential reads at import time, request signing, scraping, broker execution, AI/LLM calls, route rewrites, or deletion of legacy modules.
