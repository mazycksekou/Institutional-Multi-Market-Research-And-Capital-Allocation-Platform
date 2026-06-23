# Prediction-Market Proof-Test Retirement Map After 10K8ZGX

## Mapping Summary
The legacy-shell-heavy proof tests were reclassified as historical evidence only.

| Test file | New status | Canonical surface now validated |
| --- | --- | --- |
| `tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py` | historical evidence only | `src.services.prediction_market_runtime_bridge` |
| `tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py` | historical evidence only | `src.connectors.prediction_market_data` |
| `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py` | historical evidence only | `src.services.prediction_market_runtime_bridge` |
| `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py` | historical evidence only | `src.connectors.prediction_market_data` |
| `tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py` | historical evidence only | `src.services.prediction_market_runtime_bridge` |
| `tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py` | historical evidence only | `src.services.prediction_market_runtime_bridge` |
| `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py` | historical evidence only | `src.connectors.prediction_market_data` |
| `tests/test_phase10k8zfy_prediction_market_connector_batch_1.py` | historical evidence only | `src.connectors.prediction_market_data` |
| `tests/test_phase10k8zg2_legacy_deletion_readiness_audit.py` | historical evidence only | canonical provider/connector stacks |
| `tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py` | historical evidence only | `src.providers.prediction_markets` |
| `tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py` | final evidence-only proof file | canonical bridge / connector / provider stack |

## What Changed
Legacy-shell references were removed from active runtime assertions in the retired/reclassified proof tests.

## What Remains
Only the final delete-readiness proof file intentionally references legacy shell names, and only as evidence.

## Delete-Readiness Conclusion
The legacy prediction-market shell names are delete-ready from a dependency perspective.

## Required Statement
“Proof-test references must not preserve legacy prediction-market shells unnecessarily. This phase reclassifies historical evidence and proves delete readiness, but does not delete legacy prediction-market modules.”
