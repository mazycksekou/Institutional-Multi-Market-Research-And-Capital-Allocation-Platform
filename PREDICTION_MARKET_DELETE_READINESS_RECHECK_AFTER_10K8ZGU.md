# PREDICTION_MARKET_DELETE_READINESS_RECHECK_AFTER_10K8ZGU

## Delete-Readiness Decision
No legacy prediction-market shell is delete-ready yet.

| File | Decision | Reason |
| --- | --- | --- |
| `kalshi_client.py` | `test-blocked`, `compatibility-blocked` | Still referenced by historical evidence and compatibility tests. |
| `providers/kalshi_provider.py` | `test-blocked`, `compatibility-blocked` | Still referenced by historical evidence and compatibility tests. |
| `betting_providers/kalshi_api.py` | `test-blocked`, `compatibility-blocked` | Still referenced by historical evidence and compatibility tests. |
| `automation_scheduler/kalshi_readonly_adapter.py` | `test-blocked`, `compatibility-blocked` | Still referenced by historical evidence and compatibility tests. |
| `automation_scheduler/kalshi_market_provider.py` | `test-blocked`, `compatibility-blocked` | Still referenced by historical evidence and compatibility tests. |

## Why Deletion Did Not Occur
The runtime scheduler has already moved to the canonical bridge, but the historical compatibility layer still has enough references to keep the shells on disk.

## Next Recommended Phase
Reclassify or retire the remaining compatibility-oriented tests and evidence files, then run one more delete-readiness proof for the five prediction-market shells.

This phase does not authorize deletion.
