# Final Prediction-Market Delete Readiness After 10K8ZGX

## Delete-Readiness Decision by Shell
| Legacy shell | Decision | Reason |
| --- | --- | --- |
| `kalshi_client.py` | delete-ready | Active runtime/test ownership has moved to canonical bridge/connector/provider surfaces; remaining reference is evidence-only in the final proof file. |
| `providers/kalshi_provider.py` | delete-ready | Canonical provider ownership is now `src.providers.prediction_markets`; remaining reference is evidence-only. |
| `betting_providers/kalshi_api.py` | delete-ready | Disabled connector-owned surfaces now cover the live-client shape; remaining reference is evidence-only. |
| `automation_scheduler/kalshi_readonly_adapter.py` | delete-ready | Scheduler/runtime imports were redirected; remaining reference is evidence-only. |
| `automation_scheduler/kalshi_market_provider.py` | delete-ready | Scheduler/runtime imports were redirected; remaining reference is evidence-only. |

## Remaining Active Reference
Only `tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py` still touches the shell names, and only as historical evidence.

## Why No Deletion Occurs
This phase proves readiness only. Deletion is deferred to a later, dedicated deletion phase.

## Required Statement
“Proof-test references must not preserve legacy prediction-market shells unnecessarily. This phase reclassifies historical evidence and proves delete readiness, but does not delete legacy prediction-market modules.”
