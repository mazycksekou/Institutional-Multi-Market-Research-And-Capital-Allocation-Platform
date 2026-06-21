# Prediction Market Connector Disabled Live Behavior After 10K8ZGG

## Disabled Live Behavior
The connector-owned live-client shape is present, but disabled:
- configuration is data-only
- auth requirements are declarative
- signing methods raise `ConnectorDisabledError`
- transport methods raise `ConnectorDisabledError`
- readiness reports show disabled state
- disabled client shells raise `ConnectorDisabledError`

## No Import-Time Credentials
No connector-owned prediction-market module reads credentials or environment secrets at import time.

## No Network Behavior
No connector-owned prediction-market module imports or uses live network libraries such as `requests`, `httpx`, `websocket`, `yfinance`, `selenium`, or `playwright`.

## Connector-Owned Modules
- `src/connectors/prediction_market_data/configuration.py`
- `src/connectors/prediction_market_data/auth.py`
- `src/connectors/prediction_market_data/signing.py`
- `src/connectors/prediction_market_data/transport.py`
- `src/connectors/prediction_market_data/readiness.py`
- `src/connectors/prediction_market_data/disabled_client.py`

## Required Statement
Prediction-market live-client migration is connector-owned but disabled in this phase. This phase does not authorize live API calls, credential reads at import time, request signing, scraping, broker execution, AI/LLM calls, route rewrites, or deletion of legacy modules.

## Safety Summary
No live behavior is enabled. No deletion occurred.
