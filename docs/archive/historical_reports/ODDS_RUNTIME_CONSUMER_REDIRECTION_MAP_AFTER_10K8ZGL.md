# Odds Runtime Consumer Redirection Map After 10K8ZGL

## Runtime File Map
| Runtime file | Former dependency | Canonical dependency | Status | Notes |
| --- | --- | --- | --- | --- |
| `src/services/enrichment_service.py` | `providers.sharp_provider` | `src.services.odds_runtime_bridge` | redirected | Sharp odds enrichment now flows through the canonical bridge |
| `automation_scheduler/scheduler_runner.py` | `automation_scheduler.sharp_sportsbook_adapter`, `automation_scheduler.sportsbook_odds_provider` | `src.services.odds_runtime_bridge` | redirected | Scheduler odds runtime now uses the canonical bridge |
| `automation_scheduler/__init__.py` | `automation_scheduler.sharp_sportsbook_adapter`, `automation_scheduler.sportsbook_odds_provider` | `src.services.odds_runtime_bridge` | redirected | Package-level runtime odds exports now come from the bridge |

## What Was Redirected
- Runtime odds enrichment
- Scheduler odds snapshot access
- Scheduler odds normalization helpers
- Package-level odds bridge exports

## Canonical Bridge Policy
The runtime bridge is a compatibility-preserving runtime bridge.
It keeps the redirected service and scheduler paths working without restoring live odds access.

## What Remains
- Legacy odds shells still exist for compatibility and proof history
- Historical tests still reference legacy odds shell paths
- Compatibility-shell deletion is still blocked by proof-only work

## Delete-Readiness Summary
- `src/services/enrichment_service.py`: not a delete target; redirect complete
- `automation_scheduler/scheduler_runner.py`: not a delete target; redirect complete
- `automation_scheduler/__init__.py`: not a delete target; redirect complete
- legacy odds shells: preserved, not deleted, not yet delete-ready in this phase

## Why No Deletion Occurred
This phase is redirection-only.
It establishes the canonical runtime dependency path before any deletion proof is claimed.

## Next Recommended Deletion Batch
Redirect remaining test/import references to the canonical bridge, then re-run delete-readiness proof for the legacy odds shells.
