# Odds Data Connector Migration Map After 10K8ZFZ

## Executive Summary
This map records the first inert odds-data connector batch and the remaining deferred live behavior.

## Canonical Connector Surface
- `src/connectors/odds_data/__init__.py`
- `src/connectors/odds_data/client.py`
- `src/connectors/odds_data/read_only.py`
- `src/connectors/odds_data/adapter.py`
- `src/connectors/odds_data/models.py`
- `src/connectors/odds_data/payloads.py`
- `src/connectors/odds_data/contracts.py`

## What the Wrapper Does
- Normalizes supplied odds payloads.
- Builds local-only snapshot and record models.
- Exposes disabled fetch methods that raise `ConnectorDisabledError`.
- Stays vendor-neutral.

## What Was Deferred
- Live odds fetching.
- Credential reads.
- External retries and transport.
- Vendor-specific runtime behavior.

## Legacy Modules Reviewed
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `sharp_client.py`
- `providers/odds_provider_router.py`
- `betting_providers/provider_router.py`

## Compatibility Notes
- Legacy imports continue to resolve unchanged.
- No legacy module was deleted.
- No runtime behavior was activated.
