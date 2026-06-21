# Odds Data Live Client Migration Map After 10K8ZGH

## Migration Map

| Legacy surface | Tag | Canonical destination | Status |
|---|---|---|---|
| `sharp_client.py` | `RUNTIME_LIVE_CLIENT_OWNER` | `src.connectors.odds_data.transport` / `disabled_client.py` | Transport shape only; disabled live behavior |
| `providers/sharp_provider.py::enrich_with_sharp` | `CONNECTOR_READY_WITH_STUBS` | `src.connectors.odds_data.disabled_client` | Live half disabled; normalization split remains separate |
| `betting_providers/sharp_api.py::SharpApiAdapter` | `RUNTIME_LIVE_CLIENT_OWNER` | `src.connectors.odds_data.configuration`, `auth`, `transport` | Adapter shape now connector-owned but disabled |
| `betting_providers/the_odds_api.py::TheOddsApiAdapter` | `RUNTIME_LIVE_CLIENT_OWNER` | `src.connectors.odds_data.configuration`, `auth`, `transport` | Adapter shape now connector-owned but disabled |
| `betting_providers/sportsgameodds.py::SportsGameOddsAdapter` | `RUNTIME_LIVE_CLIENT_OWNER` | `src.connectors.odds_data.configuration`, `auth`, `transport` | Adapter shape now connector-owned but disabled |
| `automation_scheduler/sharp_sportsbook_adapter.py::SharpSportsbookAdapter` | `CONNECTOR_READY_WITH_STUBS` | `src.connectors.odds_data.readiness`, `transport` | Read-only wrapper remains disabled |
| `automation_scheduler/sportsbook_odds_provider.py::get_sportsbook_snapshot` | `RUNTIME_LIVE_CLIENT_OWNER` | `src.connectors.odds_data.transport` | Live wrapper stays disabled |
| `automation_scheduler/sportsbook_odds_provider.py::normalize_sportsbook_snapshot`, `validate_sportsbook_snapshot`, `summarize_sportsbook_snapshot` | `CONNECTOR_READY_INERT` | `src.providers.sportsbooks` | Pure local snapshot helpers |

## Connector-Owned Modules Created
- `configuration.py`
- `auth.py`
- `transport.py`
- `readiness.py`
- `source_profile.py`
- `live_client.py`
- `disabled_client.py`

## Legacy Modules Remain
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`

## Compatibility and Deletion Notes
Legacy modules remain importable and are not deleted. Deletion is deferred until downstream redirection and proof are complete.

## Required Statement
Odds-data live-client migration is connector-owned but disabled in this phase. This phase does not authorize live API calls, credential reads at import time, scraping, broker execution, bet execution, AI/LLM calls, route rewrites, or deletion of legacy modules.
