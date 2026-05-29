# Provider Adapter Contracts v1

## Scope and Safety
- `provider_live_calls_enabled=false`
- `provider_credentials_required=false`
- `dry_run=true`
- `human_approval_required=true`
- `auto_bet_enabled=false`
- `auto_trade_enabled=false`
- `auto_execution_enabled=false`
- No external provider calls.

## Provider Types
- `sportsbook_odds`
- `player_props`
- `prediction_market`
- `stock_price`
- `stock_fundamentals`
- `news_events`
- `injury_weather`

## Added Modules
- `provider_contracts.py`: shared provider contract metadata and runtime directory helpers.
- `provider_adapter_base.py`: dry-run adapter base with capability/config/health/fetch/normalize/validate methods.
- `provider_payload_validator.py`: provider payload shape and staleness checks.
- `provider_health.py`: compact provider health summary.
- Adapter contracts:
  - `sportsbook_adapter_contract.py`
  - `player_props_adapter_contract.py`
  - `kalshi_adapter_contract.py`
  - `stock_price_adapter_contract.py`
  - `stock_fundamentals_adapter_contract.py`
  - `news_events_adapter_contract.py`
  - `injury_weather_adapter_contract.py`
- `provider_normalization_contract.py`: normalized schema contracts and dispatch.

## Local Data Paths
- `data/provider_health/`
- `data/provider_contracts/`
- `data/provider_payload_samples/`

All directories are created at runtime.

## API Endpoints
- `GET /api/providers/health`
- `GET /api/providers/registry`

Default output stays compact and omits raw provider payloads and credentials.

