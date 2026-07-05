# Odds Legacy Delete Readiness After 10K8ZGI

## Target Files
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`

## Current Readiness Status
These files are compatibility-preserving runtime consumers with canonical connector metadata redirection. They are closer to deletion proof, but they are not deleted in this phase.

## Delete-Readiness Assessment
| file | status | blocker |
| --- | --- | --- |
| `sharp_client.py` | compatibility-only, not yet delete-safe | live helper bodies still exist |
| `providers/sharp_provider.py` | compatibility-only, not yet delete-safe | enrichment still reaches legacy sharp flow |
| `betting_providers/sharp_api.py` | compatibility-only, not yet delete-safe | live adapter body still exists |
| `betting_providers/the_odds_api.py` | compatibility-only, not yet delete-safe | live adapter body still exists |
| `betting_providers/sportsgameodds.py` | compatibility-only, not yet delete-safe | live adapter body still exists |
| `automation_scheduler/sharp_sportsbook_adapter.py` | compatibility-only, not yet delete-safe | scheduler adapter body still exists |
| `automation_scheduler/sportsbook_odds_provider.py` | compatibility-only, not yet delete-safe | scheduler snapshot helpers still exist |
| `src/providers/provider_router.py` | canonical bridge, not a delete target | still provides runtime compatibility routing |

## What Was Proven
- Canonical odds connector metadata can be imported from the remaining odds runtime consumers.
- Legacy odds modules remain importable after the redirection.
- Import-time credential access was not introduced.

## What Remains Before Deletion
- Live-method bodies still need a later retirement proof.
- Route- and service-level consumers still need later behavioral redirection if the legacy odds modules are to disappear.

## No-Deletion Statement
No deletion occurred. The proof shows the path to later deletion, but the legacy odds modules are still preserved in this phase.
