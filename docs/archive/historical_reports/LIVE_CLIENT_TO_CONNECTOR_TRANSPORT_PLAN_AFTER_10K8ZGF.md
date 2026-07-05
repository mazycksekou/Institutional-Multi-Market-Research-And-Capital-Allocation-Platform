# Live Client to Connector Transport Plan After 10K8ZGF

## Transport Plan

### `src.connectors.prediction_market_data`
Transport here first:
- `kalshi_client.py`
- `providers/kalshi_provider.py::enrich_with_kalshi`
- `betting_providers/kalshi_api.py::KalshiApiAdapter`
- `automation_scheduler/kalshi_readonly_adapter.py::KalshiReadonlyAdapter`
- `automation_scheduler/kalshi_market_provider.py::get_kalshi_snapshot`

Notes:
- The normalization half of `providers/kalshi_provider.py` belongs in `src.providers.prediction_markets`.
- The pure snapshot normalization helpers in `automation_scheduler/kalshi_market_provider.py` can become inert connector wrappers or provider normalization helpers.

### `src.connectors.odds_data`
Transport here first:
- `sharp_client.py`
- `providers/sharp_provider.py::enrich_with_sharp`
- `betting_providers/sharp_api.py::SharpApiAdapter`
- `betting_providers/the_odds_api.py::TheOddsApiAdapter`
- `betting_providers/sportsgameodds.py::SportsGameOddsAdapter`
- `automation_scheduler/sharp_sportsbook_adapter.py::SharpSportsbookAdapter`
- `automation_scheduler/sportsbook_odds_provider.py::get_sportsbook_snapshot`

Notes:
- Snapshot normalization helpers from sportsbook modules can split to `src.providers.sportsbooks`.

### `src.connectors.market_data`
No reviewed live-client surface in this phase maps directly here. It is reserved for future stock / 0DTE live access wrappers.

### `src.providers.prediction_markets`
Provider normalization-only surfaces:
- `providers/kalshi_provider.py::normalize_kalshi_probability_market`
- `betting_providers/kalshi_api.py` normalization of events/markets
- `automation_scheduler/kalshi_market_provider.py::normalize_kalshi_snapshot`, `validate_kalshi_snapshot`, `summarize_kalshi_snapshot`

### `src.providers.sportsbooks`
Provider normalization-only surfaces:
- `betting_providers/the_odds_api.py` normalization of events/odds
- `betting_providers/sportsgameodds.py` sportsbook event shape handling
- `automation_scheduler/sharp_sportsbook_adapter.py::normalize_sportsbook_snapshot`, `validate_sportsbook_snapshot`, `summarize_sportsbook_snapshot`

### `src.services`
Service orchestration-only surfaces:
- `src/services/enrichment_service.py`
- `src/api/provider_status_routes.py`
- `src/api/market_metadata_routes.py`
- `src/api/model_card_service.py`
- `screenshot_intake.py`

### `UNSAFE_TO_TOUCH`
- `main.py`
- `streamlit_app.py`

## Transport Notes
- `CONNECTOR_READY_INERT`: pure normalization, validation, snapshot-writing, and status-shaping helpers that can become inert connector wrappers.
- `CONNECTOR_READY_WITH_STUBS`: live adapters that should be moved only if live methods are explicitly disabled or converted to inert errors.
- `DELETE_READY_AFTER_CONNECTOR_MIGRATION`: live-client wrappers and legacy vendor adapters that can be deleted only after the connector transport lands and downstream imports are redirected.

## Required Statement
Live-client functionality must be isolated into src.connectors before legacy live-client modules are deleted. This phase does not authorize live API calls, credential reads, scraping, broker execution, AI/LLM calls, source migration, or deletion.

