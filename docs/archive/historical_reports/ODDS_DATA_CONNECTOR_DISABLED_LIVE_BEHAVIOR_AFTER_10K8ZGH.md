# Odds Data Connector Disabled Live Behavior After 10K8ZGH

## Disabled Live Behavior
The connector-owned live-client shape is present, but disabled:
- configuration is data-only
- auth requirements are declarative
- transport methods raise `ConnectorDisabledError`
- readiness reports show disabled state
- disabled client shells raise `ConnectorDisabledError`
- source profile metadata stays vendor-neutral

## No Import-Time Credentials
No connector-owned odds-data module reads credentials or environment secrets at import time.

## No Network Behavior
No connector-owned odds-data module imports or uses live network libraries such as `requests`, `httpx`, `websocket`, `yfinance`, `selenium`, or `playwright`.

## Connector-Owned Modules
- `src/connectors/odds_data/configuration.py`
- `src/connectors/odds_data/auth.py`
- `src/connectors/odds_data/transport.py`
- `src/connectors/odds_data/readiness.py`
- `src/connectors/odds_data/source_profile.py`
- `src/connectors/odds_data/live_client.py`
- `src/connectors/odds_data/disabled_client.py`

## Required Statement
Odds-data live-client migration is connector-owned but disabled in this phase. This phase does not authorize live API calls, credential reads at import time, scraping, broker execution, bet execution, AI/LLM calls, route rewrites, or deletion of legacy modules.

## Safety Summary
No live behavior is enabled. No deletion occurred.
