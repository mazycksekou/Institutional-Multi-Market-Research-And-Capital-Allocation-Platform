# FULL Gate Failure Inventory After 10K8ZHI

## Executive Summary
The full-gate failures were all test-side regressions or stale proof assumptions.
No runtime code needed to be rewritten.

## Failure Inventory

| Category | Exact Test | Exact Failure | Root Cause | Recommended Resolution |
| --- | --- | --- | --- | --- |
| Migration-regression | `tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py::test_runtime_category_adapters_import_and_preserve_compatibility` | `namespace_pm != canonical_pm` because the `timestamp` field differed by 1 ms | Timestamped adapter output was compared with strict dict equality | Ignore `timestamp` for the equivalence check |
| Connector-disabled expectation | `tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py::test_canonical_bridge_and_connector_imports_are_safe_and_disabled` | Disabled client raised `ConnectorDisabledError`, but the assertion was reload-sensitive | Reloaded tests were comparing a stale exception class object | Assert disabled behavior via `RuntimeError` and class name |
| Connector-disabled expectation | `tests/test_phase10k8zgm_odds_historical_test_redirection.py::test_canonical_bridge_and_connector_imports_are_safe_and_disabled` | Same reload-sensitive disabled-exception mismatch | Same as above | Normalize to `RuntimeError` + class name |
| Connector-disabled expectation | `tests/test_phase10k8zgn_odds_proof_history_cleanup.py::test_canonical_bridge_and_connector_imports_are_safe_and_disabled` | Same reload-sensitive disabled-exception mismatch | Same as above | Normalize to `RuntimeError` + class name |
| Compatibility / historical evidence | `tests/test_phase10k8zgo_odds_compatibility_test_retirement.py::test_deleted_files_are_gone_and_canonical_flow_remains_safe` | Same reload-sensitive disabled-exception mismatch | Same as above | Normalize to `RuntimeError` + class name |
| Compatibility / historical evidence | `tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py::test_canonical_odds_flow_remains_safe_and_disabled` | Same reload-sensitive disabled-exception mismatch | Same as above | Normalize to `RuntimeError` + class name |
| Historical-proof | `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py::test_canonical_prediction_market_surfaces_import_and_legacy_shells_stay_disabled` | Same reload-sensitive disabled-exception mismatch | Same as above | Normalize to `RuntimeError` + class name |
| Scheduler-coupling | `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py::test_canonical_prediction_market_bridge_connectors_and_legacy_shells_remain_importable` | Same reload-sensitive disabled-exception mismatch | Same as above | Normalize to `RuntimeError` + class name |
| Historical-proof | `tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py::test_historical_prediction_market_redirection_uses_canonical_bridge_and_keeps_legacy_shells_importable` | Same reload-sensitive disabled-exception mismatch | Same as above | Normalize to `RuntimeError` + class name |
| Historical-proof | `tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py::test_canonical_prediction_market_modules_import_and_remain_disabled` | Same reload-sensitive disabled-exception mismatch | Same as above | Normalize to `RuntimeError` + class name |
| Historical-proof | `tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py::test_canonical_prediction_market_stack_imports_and_stays_disabled` | Same reload-sensitive disabled-exception mismatch | Same as above | Normalize to `RuntimeError` + class name |
| Historical-proof | `tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py::test_canonical_prediction_market_stack_imports_and_stays_disabled` | Same reload-sensitive disabled-exception mismatch | Same as above | Normalize to `RuntimeError` + class name |
| Historical-proof | `tests/test_phase10k8zgy_prediction_market_shell_deletion.py::test_canonical_prediction_market_stack_imports_and_stays_disabled` | Same reload-sensitive disabled-exception mismatch | Same as above | Normalize to `RuntimeError` + class name |

## Result
All failures were resolved with safe test-only changes.
No runtime production migration was required.
