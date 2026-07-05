# ODDS Legacy Live-Method Retirement Map After 10K8ZGJ

## Big-Picture Architecture
- `src.connectors.odds_data` owns the canonical odds connector boundary
- `src.providers` owns provider normalization and routing
- `automation_scheduler` remains a compatibility/orchestration surface while callers are retired

## Legacy Module Map

| File | Retired live behavior | New compatibility behavior | Connector metadata source |
| --- | --- | --- | --- |
| `sharp_client.py` | Active events and event odds requests | Raises `ConnectorDisabledError` | `src.connectors.odds_data` |
| `providers/sharp_provider.py` | Sharp enrichment live fetch | Returns disabled enrichment metadata | `src.connectors.odds_data` |
| `betting_providers/sharp_api.py` | Sportsbook live fetch methods | Raises `ConnectorDisabledError` | `src.connectors.odds_data` |
| `betting_providers/the_odds_api.py` | Sportsbook live fetch methods | Raises `ConnectorDisabledError` | `src.connectors.odds_data` |
| `betting_providers/sportsgameodds.py` | SportsGameOdds live fetch | Raises `ConnectorDisabledError` | `src.connectors.odds_data` |
| `automation_scheduler/sharp_sportsbook_adapter.py` | Live sportsbook snapshot/fetch methods | Returns disabled snapshot; fetch methods raise | `src.connectors.odds_data` |
| `automation_scheduler/sportsbook_odds_provider.py` | Snapshot summarization/writing bridge | Remains a disabled snapshot bridge | `src.connectors.odds_data` |

## What Changed
- Live fetch bodies were removed from the legacy odds modules
- Import compatibility was preserved
- Connector readiness/configuration metadata is now the only shared odds boundary

## What Did Not Change
- No files were deleted
- No legacy import paths were renamed
- No new live access was added
- No credential reads were added

## Compatibility Notes
- `ConnectorDisabledError` is raised for direct live-method calls
- `fetch_snapshot()` on the sportsbook adapter returns a disabled placeholder so scheduler flows can keep running
- The odds connector package remains the canonical source of readiness/configuration metadata

## Remaining Deletion Readiness Work
- Proof that all downstream callers have been redirected away from the legacy odds live-method bodies
- Proof that the remaining compatibility shell imports are no longer required by runtime or tests

