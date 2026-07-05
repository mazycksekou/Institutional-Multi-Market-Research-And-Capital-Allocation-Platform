# Service Layer Ownership Map After 10K8ZHB

| Path | Classification | Why |
| --- | --- | --- |
| `src/services/decision_engine.py` | `SERVICE_ORCHESTRATION_OWNER` | Thin canonical decision engine over `src.core`. |
| `src/services/enrichment_service.py` | `SERVICE_ORCHESTRATION_OWNER` | Ticket enrichment orchestration over canonical bridge services. |
| `src/services/action_betting_service.py` | `SERVICE_ORCHESTRATION_OWNER` | Route-facing action service that shapes provider responses. |
| `src/services/bet_csv_service.py` | `SERVICE_ORCHESTRATION_OWNER` | Local CSV ledger shell. |
| `src/services/model_backtest_service.py` | `SERVICE_ORCHESTRATION_OWNER` | Local backtest orchestration shell. |
| `src/services/odds_runtime_bridge.py` | `SERVICE_ORCHESTRATION_OWNER` | Canonical odds bridge surface. |
| `src/services/prediction_market_runtime_bridge.py` | `SERVICE_ORCHESTRATION_OWNER` | Canonical prediction-market bridge surface. |
| `screenshot_intake.py` | `COMPATIBILITY_SHIM_CANDIDATE` | Root compatibility surface for screenshot parsing and model enrichment. |
| `bet_log.py` | `COMPATIBILITY_SHIM_CANDIDATE` | Root compatibility surface for logging and performance summaries. |
| `bet_decision_engine.py` | `COMPATIBILITY_SHIM_CANDIDATE` | Root compatibility surface for line evaluation and decision labels. |

## Direct Misplacement Review

- `MIGRATE_TO_SRC_CORE`: no remaining canonical service module was found to need this tag.
- `MIGRATE_TO_SRC_PROVIDERS`: no remaining canonical service module was found to need this tag.
- `MIGRATE_TO_SRC_CONNECTORS`: no remaining canonical service module was found to need this tag.
- `API_LAYER_ONLY`: route exposure continues in `src/api/*`, not in services.
- `DASHBOARD_LAYER_ONLY`: dashboard ownership is outside services.
- `DELETE_CANDIDATE_AFTER_PROOF`: not claimed here; the root shells remain compatibility shells for now.
- `UNSAFE_TO_TOUCH`: live execution and live connector paths remain deferred.

## Ownership Summary

- Core math/risk/pricing logic is already out of services.
- Service code is now mostly orchestration and shell management.
- Screenshot workflow remains the next clear service extraction target.
