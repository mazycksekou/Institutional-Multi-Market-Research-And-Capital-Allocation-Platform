# PREDICTION_MARKET_COMPATIBILITY_DELETE_READINESS_AFTER_10K8ZGS

## Delete-Readiness Decision
No legacy prediction-market compatibility shell is delete-ready yet.

| File | Decision | Reason |
| --- | --- | --- |
| `kalshi_client.py` | `test-blocked`, `compatibility-blocked` | Historical tests still import it and `src/api/market_utility_routes.py` still references it as evidence text. |
| `providers/kalshi_provider.py` | `test-blocked`, `compatibility-blocked` | Historical tests still import it and patch `providers.kalshi_provider.requests.get`. |
| `betting_providers/kalshi_api.py` | `test-blocked`, `compatibility-blocked` | Historical tests still import it. |
| `automation_scheduler/kalshi_readonly_adapter.py` | `runtime-blocked`, `test-blocked`, `compatibility-blocked` | Scheduler runtime modules still import it; historical tests still import and patch it. |
| `automation_scheduler/kalshi_market_provider.py` | `runtime-blocked`, `test-blocked` | Scheduler runtime modules still import it; historical tests still import it. |

## Why Deletion Did Not Occur
Deletion would still break runtime scheduler imports and historical proof tests. The canonical bridge and connector owners are in place, but the compatibility-shell layer still has remaining references.

## Canonical Ownership
The canonical flow is already established as:

`src.services.prediction_market_runtime_bridge` -> `src.providers.prediction_markets` -> `src.connectors.prediction_market_data`

## Next Recommended Phase
Redirect or retire the remaining runtime scheduler dependencies and the historical compatibility tests that still touch the legacy prediction-market shells. After that, re-run delete-readiness proof for the five target files.
