# Next Connector Migration Sequence After 10K8ZGF

## Recommended Next 3 Phases

1. **Prediction-market connector migration batch**
   - Move `kalshi_client.py` transport into `src.connectors.prediction_market_data`
   - Redirect `providers/kalshi_provider.py::enrich_with_kalshi`
   - Redirect `betting_providers/kalshi_api.py`
   - Redirect `automation_scheduler/kalshi_readonly_adapter.py` and `automation_scheduler/kalshi_market_provider.py`

2. **Odds-data connector migration batch**
   - Move `sharp_client.py` transport into `src.connectors.odds_data`
   - Redirect `providers/sharp_provider.py::enrich_with_sharp`
   - Redirect `betting_providers/sharp_api.py`, `betting_providers/the_odds_api.py`, and `betting_providers/sportsgameodds.py`
   - Redirect `automation_scheduler/sharp_sportsbook_adapter.py` and `automation_scheduler/sportsbook_odds_provider.py`

3. **Bridge thinning batch**
   - Thin `src/services/enrichment_service.py`
   - Thin `src/api/provider_status_routes.py`
   - Thin `src/api/market_metadata_routes.py`
   - Thin `src/api/model_card_service.py`
   - Keep `main.py` and `streamlit_app.py` as entrypoint/dashboard shells

## Deletion Policy
- Delete only after import proof, test proof, and compatibility proof are clean.
- Do not delete live-client modules while they still own credential or network behavior.

## Strategic Notes
- `src.connectors.market_data` remains reserved for future stock / 0DTE live access.
- `automation_scheduler` remains a decommission target.

