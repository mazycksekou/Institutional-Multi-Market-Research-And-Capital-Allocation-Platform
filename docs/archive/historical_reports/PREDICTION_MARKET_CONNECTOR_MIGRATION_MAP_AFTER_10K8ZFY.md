# Prediction Market Connector Migration Map After 10K8ZFY

## Executive Summary
This map records the first inert prediction-market connector batch and the remaining deferred live behavior.

## Canonical Connector Surface
- `src/connectors/prediction_market_data/__init__.py`
- `src/connectors/prediction_market_data/client.py`
- `src/connectors/prediction_market_data/read_only.py`
- `src/connectors/prediction_market_data/adapter.py`
- `src/connectors/prediction_market_data/models.py`
- `src/connectors/prediction_market_data/payloads.py`
- `src/connectors/prediction_market_data/contracts.py`

## What the Wrapper Does
- Normalizes supplied prediction-market payloads.
- Builds local-only snapshot and record models.
- Exposes disabled fetch methods that raise `ConnectorDisabledError`.
- Stays vendor-neutral.

## What Was Deferred
- Live market fetching.
- Credential signing.
- External retries and transport.
- Vendor-specific runtime behavior.

## Legacy Modules Reviewed
- `providers/kalshi_provider.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `kalshi_client.py`

## Compatibility Notes
- Legacy imports continue to resolve unchanged.
- No legacy module was deleted.
- No runtime behavior was activated.

