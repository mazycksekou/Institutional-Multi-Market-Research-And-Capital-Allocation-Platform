# ODDS Disabled Method Behavior After 10K8ZGJ

## Purpose
Document the disabled-shell contract now used by the legacy odds modules.

## Behavior Table

| Module | Method | New behavior |
| --- | --- | --- |
| `sharp_client.py` | `get_sharp_active_events(...)` | Raises `ConnectorDisabledError` |
| `sharp_client.py` | `get_sharp_event_odds(...)` | Raises `ConnectorDisabledError` |
| `betting_providers/sharp_api.py` | `get_supported_sports(...)` | Raises `ConnectorDisabledError` |
| `betting_providers/sharp_api.py` | `get_active_events(...)` | Raises `ConnectorDisabledError` |
| `betting_providers/sharp_api.py` | `get_event_odds(...)` | Raises `ConnectorDisabledError` |
| `betting_providers/sharp_api.py` | `get_first_event_odds(...)` | Raises `ConnectorDisabledError` |
| `betting_providers/the_odds_api.py` | `get_supported_sports(...)` | Raises `ConnectorDisabledError` |
| `betting_providers/the_odds_api.py` | `get_odds_events(...)` | Raises `ConnectorDisabledError` |
| `betting_providers/the_odds_api.py` | `get_active_events(...)` | Raises `ConnectorDisabledError` |
| `betting_providers/the_odds_api.py` | `get_event_odds(...)` | Raises `ConnectorDisabledError` |
| `betting_providers/the_odds_api.py` | `get_first_event_odds(...)` | Raises `ConnectorDisabledError` |
| `betting_providers/sportsgameodds.py` | `get_active_events(...)` | Raises `ConnectorDisabledError` |
| `automation_scheduler/sharp_sportsbook_adapter.py` | `fetch_events(...)` | Raises `ConnectorDisabledError` |
| `automation_scheduler/sharp_sportsbook_adapter.py` | `fetch_odds(...)` | Raises `ConnectorDisabledError` |
| `automation_scheduler/sharp_sportsbook_adapter.py` | `fetch_player_props(...)` | Raises `ConnectorDisabledError` |
| `automation_scheduler/sharp_sportsbook_adapter.py` | `fetch_sports(...)` | Raises `ConnectorDisabledError` |
| `automation_scheduler/sharp_sportsbook_adapter.py` | `fetch_snapshot(...)` | Returns disabled placeholder snapshot |
| `providers/sharp_provider.py` | `enrich_with_sharp(...)` | Returns disabled enrichment metadata |

## Disabled Metadata Delegation
- Module-level odds connector metadata still comes from `src.connectors.odds_data`
- Connector readiness remains disabled
- Connector configuration remains read-only and vendor-neutral

## Runtime Guarantees
- No live odds HTTP calls are made
- No credentials are read at import time
- No request signing is performed
- No bet execution or broker logic is introduced

## Test Implications
- Direct live-method calls should now fail fast with an explicit disabled error
- Snapshot and enrichment callers should see disabled placeholder results rather than live payloads

