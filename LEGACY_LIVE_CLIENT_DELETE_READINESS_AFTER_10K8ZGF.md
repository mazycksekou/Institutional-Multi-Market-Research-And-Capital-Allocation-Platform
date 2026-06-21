# Legacy Live Client Delete Readiness After 10K8ZGF

## Delete-Ready After Connector Migration
These files are the strongest delete candidates, but only after connector transport and import proof:
- `kalshi_client.py`
- `sharp_client.py`
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`
- `betting_providers/kalshi_api.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`

## Connector-Wrapper Candidates With Stubs
These files should be transported or stubbed before any deletion discussion:
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`

## Not Delete-Ready Yet
These are service / orchestration surfaces and should stay in place for now:
- `src/services/enrichment_service.py`
- `src/api/provider_status_routes.py`
- `src/api/market_metadata_routes.py`
- `src/api/model_card_service.py`
- `screenshot_intake.py`
- `main.py`
- `streamlit_app.py`

## Delete-Readiness Findings
- The root live clients are delete-ready only after connector migration.
- The vendor adapters are delete-ready only after connector migration and downstream import redirection.
- The automation_scheduler live adapters are not delete-ready yet because they still anchor live adapter behavior and bridge logic.
- `main.py` and `streamlit_app.py` are explicitly not deletion candidates.

