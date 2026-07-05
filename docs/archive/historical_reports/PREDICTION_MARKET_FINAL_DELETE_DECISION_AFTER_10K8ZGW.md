# PREDICTION_MARKET_FINAL_DELETE_DECISION_AFTER_10K8ZGW

## Delete-Readiness Decision Per Shell
| Shell | Decision | Reason |
| --- | --- | --- |
| `kalshi_client.py` | `test-blocked` | Historical proof tests still import it; `src/api/market_utility_routes.py` still lists the filename as evidence-only metadata. |
| `providers/kalshi_provider.py` | `test-blocked` | Historical proof tests still import it. |
| `betting_providers/kalshi_api.py` | `test-blocked` | Historical proof tests still import it. |
| `automation_scheduler/kalshi_readonly_adapter.py` | `test-blocked` | Historical proof tests still import it; runtime ownership has already moved away from it. |
| `automation_scheduler/kalshi_market_provider.py` | `test-blocked` | Historical proof tests still import it; runtime ownership has already moved away from it. |

## Conclusion
No legacy prediction-market shell is delete-ready in this phase.

The canonical runtime chain is already in place:

`src.services.prediction_market_runtime_bridge` -> `src.connectors.prediction_market_data` -> `src.providers.prediction_markets`

The remaining blocker is the active historical proof/test surface.

