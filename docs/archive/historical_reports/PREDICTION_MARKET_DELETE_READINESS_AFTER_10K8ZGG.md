# Prediction Market Delete Readiness After 10K8ZGG

## Delete-Ready After Future Connector Proof
These legacy surfaces remain the strongest delete candidates, but not yet in this phase:
- `kalshi_client.py`
- `providers/kalshi_provider.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`

## Not Delete-Ready Yet
- `src/connectors/prediction_market_data/*` canonical disabled connector surfaces
- `src/providers/prediction_markets/*`
- `src/services/*`
- `src/api/*`
- `main.py`
- `streamlit_app.py`

## Why No Deletion Occurred
The connector-owned disabled surfaces are in place, but the legacy prediction-market runtime still exists and remains importable. Deletion is deferred until downstream redirection and proof are complete.

## What Remains Before Deletion
- redirection of any remaining runtime consumers
- compatibility proof for legacy imports
- full local test gate proof after any later deletion batch

## Next Recommended Phase
Redirect remaining prediction-market runtime consumers to the new connector-owned disabled surfaces, then prove the legacy live-client files are delete-ready.
