# Odds Data Delete Readiness After 10K8ZGH

## Delete-Ready After Future Connector Proof
These legacy surfaces remain the strongest delete candidates, but not yet in this phase:
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`

## Not Delete-Ready Yet
- `src/connectors/odds_data/*` canonical disabled connector surfaces
- `src/providers/sportsbooks/*`
- `src/services/*`
- `src/api/*`
- `main.py`
- `streamlit_app.py`

## Why No Deletion Occurred
The connector-owned disabled surfaces are in place, but the legacy odds/sportsbook runtime still exists and remains importable. Deletion is deferred until downstream redirection and proof are complete.

## What Remains Before Deletion
- redirection of any remaining runtime consumers
- compatibility proof for legacy imports
- full local test gate proof after any later deletion batch

## Next Recommended Phase
Redirect remaining odds/sportsbook runtime consumers to the new connector-owned disabled surfaces, then prove the legacy live-client files are delete-ready.
