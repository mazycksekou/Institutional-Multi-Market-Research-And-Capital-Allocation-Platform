# Odds Runtime Consumer Redirection Map After 10K8ZGI

| file | legacy role | canonical connector surface imported | status | notes |
| --- | --- | --- | --- | --- |
| `sharp_client.py` | legacy sportsbook odds client helper | `src.connectors.odds_data.build_odds_data_connector_configuration`, `src.connectors.odds_data.describe_odds_data_connector_readiness` | redirection marker added | live helper bodies preserved |
| `providers/sharp_provider.py` | screenshot enrichment odds helper | same | redirection marker added | remains importable for screenshot enrichment |
| `betting_providers/sharp_api.py` | Sharp sportsbook adapter | same | redirection marker added | live adapter body preserved |
| `betting_providers/the_odds_api.py` | The Odds API adapter | same | redirection marker added | live adapter body preserved |
| `betting_providers/sportsgameodds.py` | SportsGameOdds adapter | same | redirection marker added | live adapter body preserved |
| `automation_scheduler/sharp_sportsbook_adapter.py` | scheduler sportsbook adapter | same | redirection marker added | scheduler body preserved |
| `automation_scheduler/sportsbook_odds_provider.py` | scheduler sportsbook snapshot helper | same | redirection marker added | snapshot helpers preserved |
| `src/providers/provider_router.py` | canonical runtime bridge | same | redirection marker added | bridge now references disabled connector boundary |

## Summary
The runtime consumer redirection is import-level and metadata-level. The canonical disabled odds connector boundary is now visible to the remaining odds/sportsbook runtime consumers without deleting legacy modules.

## What Remains
- Legacy live-method implementations remain for later retirement proof.
- No runtime consumer import path was removed.
- No public function was removed.
