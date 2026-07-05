# Final Odds Delete Readiness After 10K8ZGN

## Delete-Readiness Matrix
| Target | Historical proof-history blocker | Explicit compatibility-proof blocker | Delete-ready now | Reason |
| --- | --- | --- | --- | --- |
| `sharp_client.py` | no | yes | no | still required by explicit compatibility-proof tests |
| `providers/sharp_provider.py` | no | yes | no | still required by explicit compatibility-proof tests |
| `betting_providers/sharp_api.py` | no | yes | no | still required by explicit compatibility-proof tests |
| `betting_providers/the_odds_api.py` | no | yes | no | still required by explicit compatibility-proof tests |
| `betting_providers/sportsgameodds.py` | no | yes | no | still required by explicit compatibility-proof tests |
| `automation_scheduler/sharp_sportsbook_adapter.py` | no | yes | no | still required by explicit compatibility-proof tests |
| `automation_scheduler/sportsbook_odds_provider.py` | no | yes | no | still required by explicit compatibility-proof tests |

## What Changed
- Proof-history references were reclassified as historical evidence only.
- The remaining blockers are explicit compatibility-proof tests.
- The canonical runtime path stays unchanged:
  - `src.services.odds_runtime_bridge`
  - `src.connectors.odds_data`
  - `src.providers.sportsbooks`

## Why Deletion Did Not Occur
The legacy odds shells are still import targets for the dedicated compatibility-proof tests.
That is a deliberate compatibility choice, not a proof-history artifact.

## Delete-Ready Outcome
No odds shell is delete-ready in this phase.

## Next Recommended Phase
Redirect or retire the explicit compatibility-proof tests, then re-run this delete-readiness review.
