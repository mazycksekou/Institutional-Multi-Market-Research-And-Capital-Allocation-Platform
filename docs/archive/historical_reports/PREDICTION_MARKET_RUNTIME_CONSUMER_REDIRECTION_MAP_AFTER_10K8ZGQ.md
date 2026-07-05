# Prediction-Market Runtime Consumer Redirection Map After 10K8ZGQ

## Runtime Consumer Map

| Current runtime consumer | Previous dependency | New canonical dependency | Status |
| --- | --- | --- | --- |
| `src/services/enrichment_service.py` | `providers.kalshi_provider.enrich_with_kalshi` | `src.services.prediction_market_runtime_bridge.enrich_with_kalshi` | redirected |
| `screenshot_intake.py` | `src.services.enrichment_service.EnrichmentService` | unchanged, now reaches the canonical bridge indirectly | preserved |

## Canonical Flow
`src.services.enrichment_service`
-> `src.services.prediction_market_runtime_bridge`
-> `src.connectors.prediction_market_data`
-> `src.providers.prediction_markets`

## Legacy Modules Preserved
- `providers/kalshi_provider.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `kalshi_client.py`

## Status Notes
- The runtime import was redirected.
- The legacy Kalshi shell is still present for compatibility and proof history.
- No deletion occurred.
