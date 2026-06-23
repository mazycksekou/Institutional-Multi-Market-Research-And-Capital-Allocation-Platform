# PHASE 10K8ZGS Prediction-Market Compatibility Shell Delete-Readiness Proof

## Executive Summary
The remaining prediction-market compatibility shells are not delete-ready yet.
Canonical ownership is in:
- `src.services.prediction_market_runtime_bridge`
- `src.providers.prediction_markets`
- `src.connectors.prediction_market_data`

However, runtime scheduler code and historical test coverage still depend on the legacy shell layer, so deletion is blocked in this phase.

This phase is proof-only. No files are deleted and no runtime behavior changes.

## Big-Picture Architecture
Prediction-market ownership now flows through the canonical chain:

`src.services.prediction_market_runtime_bridge` -> `src.providers.prediction_markets` -> `src.connectors.prediction_market_data`

Legacy prediction-market shell files are compatibility surfaces only. They should not own live behavior.

## Runtime Dependency Scan
Remaining runtime references still touch legacy shells through scheduler ownership:

- `automation_scheduler/__init__.py`
  - imports `KalshiReadonlyAdapter`
  - imports `get_kalshi_snapshot`, `summarize_kalshi_snapshot`, `validate_kalshi_snapshot`, `write_kalshi_snapshot`
- `automation_scheduler/scheduler_runner.py`
  - imports `KalshiReadonlyAdapter`
  - imports `get_kalshi_snapshot`, `summarize_kalshi_snapshot`
- `automation_scheduler/settlement_discovery.py`
  - imports `KalshiReadonlyAdapter`
- `automation_scheduler/calibration_collector.py`
  - imports `KalshiReadonlyAdapter`
- `automation_scheduler/prediction_market_outcome_candidates.py`
  - imports `KalshiReadonlyAdapter`

## Delete-Readiness Classification
| File | Classification | Blockers |
| --- | --- | --- |
| `kalshi_client.py` | `test-blocked`, `compatibility-blocked` | Historical compatibility tests still import it; `src/api/market_utility_routes.py` still references the filename as evidence text. |
| `providers/kalshi_provider.py` | `test-blocked`, `compatibility-blocked` | Historical prediction-market tests still import it; `tests/test_screenshot_analysis.py` patches `providers.kalshi_provider.requests.get`. |
| `betting_providers/kalshi_api.py` | `test-blocked`, `compatibility-blocked` | Historical prediction-market tests still import it; compatibility proof still touches the module. |
| `automation_scheduler/kalshi_readonly_adapter.py` | `runtime-blocked`, `test-blocked`, `compatibility-blocked` | Runtime scheduler modules still import it; historical tests still import and patch it. |
| `automation_scheduler/kalshi_market_provider.py` | `runtime-blocked`, `test-blocked` | Runtime scheduler modules still import it; historical tests still import it. |

## Canonical Ownership Verification
The verified runtime ownership chain remains:

1. `src.services.prediction_market_runtime_bridge`
2. `src.providers.prediction_markets`
3. `src.connectors.prediction_market_data`

Legacy modules no longer own live behavior. They remain for compatibility and evidence until runtime and test references are fully redirected.

## Compatibility Verification
Legacy prediction-market modules still:

- import successfully
- expose compatibility symbols
- return disabled metadata or raise `ConnectorDisabledError` for live paths
- avoid import-time credential reads

## Delete-Readiness Decision
No target is delete-ready in this phase.

- `kalshi_client.py`: blocked by historical tests and compatibility evidence
- `providers/kalshi_provider.py`: blocked by historical tests and patch-based compatibility coverage
- `betting_providers/kalshi_api.py`: blocked by historical tests and compatibility coverage
- `automation_scheduler/kalshi_readonly_adapter.py`: blocked by runtime imports plus historical tests
- `automation_scheduler/kalshi_market_provider.py`: blocked by runtime imports plus historical tests

## Next Phase
The next safe step is a targeted redirection pass for the remaining runtime scheduler imports and the historical compatibility tests that still mention the legacy prediction-market shells.

This phase does not authorize deletion.
