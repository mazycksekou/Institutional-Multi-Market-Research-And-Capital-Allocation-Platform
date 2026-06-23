# Odds Shell Delete Readiness After 10K8ZGM

## Delete-Readiness Matrix
| Target | Historical test dependency removed | Runtime dependency removed | Delete-ready now | Reason |
| --- | --- | --- | --- | --- |
| `sharp_client.py` | partially | yes | no | blocked by proof-history tests |
| `providers/sharp_provider.py` | partially | yes | no | blocked by proof-history tests |
| `betting_providers/sharp_api.py` | partially | yes | no | blocked by proof-history tests |
| `betting_providers/the_odds_api.py` | partially | yes | no | blocked by proof-history tests |
| `betting_providers/sportsgameodds.py` | partially | yes | no | blocked by proof-history tests |
| `automation_scheduler/sharp_sportsbook_adapter.py` | partially | yes | no | blocked by proof-history tests |
| `automation_scheduler/sportsbook_odds_provider.py` | partially | yes | no | blocked by proof-history tests |

## What Is Now Clear
- Historical behavior assertions are now anchored on canonical bridge/provider surfaces
- The legacy shells are no longer needed for the main sportsbook test path
- Proof-history files still block deletion
- Legacy odds modules remain importable

## Why Deletion Did Not Occur
This phase is still proof-only.
The compatibility and deletion trail is preserved so we can see exactly which remaining references must be retired next.

## Delete-Ready Outcome
No odds shell is deleted in this phase.
The next phase should focus on proof-history cleanup and a fresh delete-readiness pass.

## Next Recommended Phase
Re-run the compatibility-shell delete-readiness proof using the redirected historical tests, then decide whether any remaining odds shells can be removed safely.
