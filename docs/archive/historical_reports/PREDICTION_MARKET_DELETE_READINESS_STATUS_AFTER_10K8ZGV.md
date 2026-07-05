# Prediction-Market Delete Readiness Status After 10K8ZGV

## Decision Summary
No legacy prediction-market shell is deleted in this phase.

The six compatibility-oriented tests have been redirected, but the legacy shells still have historical evidence references and therefore remain on disk.

| File | Delete-readiness decision | Remaining blocker |
| --- | --- | --- |
| `kalshi_client.py` | `compatibility-blocked` | Historical proof and evidence references still mention the file |
| `providers/kalshi_provider.py` | `compatibility-blocked` | Historical proof and evidence references still mention the file |
| `betting_providers/kalshi_api.py` | `compatibility-blocked` | Historical proof and evidence references still mention the file |
| `automation_scheduler/kalshi_readonly_adapter.py` | `compatibility-blocked` | Historical proof and evidence references still mention the file |
| `automation_scheduler/kalshi_market_provider.py` | `compatibility-blocked` | Historical proof and evidence references still mention the file |

## What Changed
The active compatibility-oriented tests no longer preserve legacy shell ownership. Runtime ownership is now validated through the canonical bridge, connector, and provider layers.

## Why Deletion Did Not Occur
Deletion is still deferred because the repository retains historical evidence and compatibility proof files from earlier phases.

## Next Recommended Phase
Run the next prediction-market delete-readiness proof after the updated tests pass and the remaining historical evidence surface is re-evaluated.

