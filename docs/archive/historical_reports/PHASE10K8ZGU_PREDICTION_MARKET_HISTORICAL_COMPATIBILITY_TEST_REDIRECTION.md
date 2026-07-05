# PHASE 10K8ZGU Prediction-Market Historical Compatibility Test Redirection

Historical compatibility tests must not preserve legacy prediction-market shells unnecessarily. This phase redirects or reclassifies historical evidence only and does not delete legacy prediction-market modules.

## Executive Summary
Historical prediction-market compatibility tests have been reclassified so they no longer preserve the legacy shell layer as active runtime ownership.

The canonical flow remains:

`src.services.prediction_market_runtime_bridge` -> `src.connectors.prediction_market_data` -> `src.providers.prediction_markets`

Legacy prediction-market shells remain on disk, but the historical test proof now treats them as compatibility evidence instead of runtime owners.

## Big-Picture Architecture
- `src.services.prediction_market_runtime_bridge` owns the scheduler-facing prediction-market bridge.
- `src.connectors.prediction_market_data` owns the inert connector boundary.
- `src.providers.prediction_markets` owns provider normalization and validation.
- Historical compatibility tests now point at the canonical bridge/provider/connector surfaces where runtime behavior is actually exercised.

## Historical Tests / References Before Redirection
The following historical files still mentioned the legacy shells before this phase:

- `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py`
- `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py`
- `tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py`
- `tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py`
- `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- `tests/test_phase10k8zfy_prediction_market_connector_batch_1.py`
- `tests/test_kalshi_readonly_adapter.py`
- `tests/test_kalshi_readonly_readiness_contract.py`
- `tests/test_calibration_collector.py`
- `tests/test_scheduler_runner.py`
- `tests/test_kalshi_market_provider.py`
- `tests/test_screenshot_analysis.py`

## Tests Redirected or Reclassified
- `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py` now uses the canonical bridge for runtime assertions and keeps the legacy modules only as importability evidence.
- `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py` continues to verify the scheduler path uses the canonical bridge.
- `tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py`, `tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py`, `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`, and `tests/test_phase10k8zfy_prediction_market_connector_batch_1.py` are historical evidence files and are reclassified as compatibility evidence, not runtime ownership.
- Legacy adapter-oriented tests such as `tests/test_kalshi_readonly_adapter.py` and `tests/test_kalshi_readonly_readiness_contract.py` remain historical evidence until their assertions are separately rewritten against canonical surfaces.

## Remaining References After Cleanup
The legacy shells still appear in:

- the legacy shell modules themselves
- historical proof and compatibility tests
- a small number of compatibility evidence strings

They no longer own the scheduler runtime path.

## Delete-Readiness Decision
No prediction-market shell is delete-ready yet.

The runtime blockers were removed in the previous phase, but the historical test and compatibility surface still keeps the legacy files alive.

### Delete-readiness per shell
| File | Decision | Reason |
| --- | --- | --- |
| `kalshi_client.py` | `test-blocked`, `compatibility-blocked` | Historical tests and evidence strings still touch it. |
| `providers/kalshi_provider.py` | `test-blocked`, `compatibility-blocked` | Historical tests and compatibility evidence still touch it. |
| `betting_providers/kalshi_api.py` | `test-blocked`, `compatibility-blocked` | Historical tests still touch it. |
| `automation_scheduler/kalshi_readonly_adapter.py` | `test-blocked`, `compatibility-blocked` | Historical tests still touch it, even though runtime scheduler consumers have been redirected. |
| `automation_scheduler/kalshi_market_provider.py` | `test-blocked`, `compatibility-blocked` | Historical tests still touch it, even though runtime scheduler consumers have been redirected. |

## Why Deletion Did Not Occur
Deletion did not occur because the compatibility/test surface still references the legacy shells, and we have not yet completed the final compatibility cleanup pass.

## Next Recommended Phase
Reclassify the remaining compatibility-oriented tests and evidence files so the legacy prediction-market shells can be rechecked for final deletion readiness.

This phase does not authorize deletion.
