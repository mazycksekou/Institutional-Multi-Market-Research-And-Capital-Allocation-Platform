# Odds Shell Delete Readiness After 10K8ZGM

## Delete-Readiness Matrix
| Target | Historical test dependency removed | Runtime dependency removed | Delete-ready now | Reason |
| --- | --- | --- | --- | --- |
| `sharp_client.py` | yes | yes | no | blocked by explicit compatibility-proof tests |
| `providers/sharp_provider.py` | yes | yes | no | blocked by explicit compatibility-proof tests |
| `betting_providers/sharp_api.py` | yes | yes | no | blocked by explicit compatibility-proof tests |
| `betting_providers/the_odds_api.py` | yes | yes | no | blocked by explicit compatibility-proof tests |
| `betting_providers/sportsgameodds.py` | yes | yes | no | blocked by explicit compatibility-proof tests |
| `automation_scheduler/sharp_sportsbook_adapter.py` | yes | yes | no | blocked by explicit compatibility-proof tests |
| `automation_scheduler/sportsbook_odds_provider.py` | yes | yes | no | blocked by explicit compatibility-proof tests |

## What Is Now Clear
- Historical behavior assertions are now anchored on canonical bridge/provider surfaces
- The legacy shells are no longer needed for the main sportsbook test path
- Proof-history files now describe historical evidence only
- Legacy odds modules are now only referenced by explicit compatibility-proof tests

## Why Deletion Did Not Occur
This phase is still proof-only.
The compatibility trail remains intact through the explicit compatibility-proof tests, while the historical proof trail is now informational.

## Delete-Ready Outcome
No odds shell is deleted in this phase.
The next phase should focus on proof-history cleanup and a fresh delete-readiness pass.

## Next Recommended Phase
Re-run the compatibility-shell delete-readiness proof using the redirected historical tests, then decide whether any remaining odds shells can be removed safely.
