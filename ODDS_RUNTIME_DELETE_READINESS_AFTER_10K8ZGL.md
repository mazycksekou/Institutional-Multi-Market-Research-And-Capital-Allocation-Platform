# Odds Runtime Delete Readiness After 10K8ZGL

## Delete-Readiness Matrix
| Target | Runtime dependency removed from consumers | Still referenced by historical tests | Delete-ready now | Reason |
| --- | --- | --- | --- | --- |
| `sharp_client.py` | yes | yes | no | legacy import history and compatibility coverage remain |
| `providers/sharp_provider.py` | yes | yes | no | historical tests and compatibility proofs still touch the shell |
| `betting_providers/sharp_api.py` | yes | yes | no | preserved as a compatibility shell |
| `betting_providers/the_odds_api.py` | yes | yes | no | preserved as a compatibility shell |
| `betting_providers/sportsgameodds.py` | yes | yes | no | preserved as a compatibility shell |
| `automation_scheduler/sharp_sportsbook_adapter.py` | yes | yes | no | compatibility proof still needs the file on disk |
| `automation_scheduler/sportsbook_odds_provider.py` | yes | yes | no | compatibility proof still needs the file on disk |

## What Is Now Clear
- Runtime consumers are no longer the blocking dependency
- Canonical runtime ownership now flows through `src.services.odds_runtime_bridge`
- Canonical disabled connector metadata remains import-safe

## Why Deletion Did Not Occur
This phase only redirected runtime consumers.
The legacy odds shells still have historical test coverage and compatibility-preservation value, so they remain on disk.

## Delete-Ready Outcome
No legacy odds shell is deleted in this phase.
The proper follow-up is a dedicated shell delete-proof phase after test and import references are redirected.

## Next Recommended Phase
Redirect the remaining historical odds-shell tests to the canonical bridge and then re-evaluate the shell deletion queue.
