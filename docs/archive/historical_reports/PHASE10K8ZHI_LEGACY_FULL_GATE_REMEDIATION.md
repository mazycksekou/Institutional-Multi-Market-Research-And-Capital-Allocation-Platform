# PHASE 10K8ZHI Legacy Full-Gate Remediation

## Executive Summary
This phase fixed the remaining legacy full-gate failures with test-only changes and produced a data/backtesting foundation audit.

No runtime provider, connector, or execution behavior was restored.
No live API calls, credential reads, AI logic, or brokerage logic were introduced.

The legacy shell migration work from earlier phases stayed intact.
The only code changes in this phase were safe test reclassifications and assertion normalization.

## Current HEAD
`d286051638fe441a63982dcbd4159531a34331fc`

## Purpose
1. Restore full-gate health by removing stale test assumptions.
2. Audit the data/backtesting foundation so the next migration order is explicit.

## Scope
1. Legacy full-gate test remediation.
2. Data ingestion and backtesting ownership audit.
3. Analytics, governance, and research layer mapping.

## Non-Goals
1. No backtesting implementation.
2. No new runtime migrations.
3. No deleted shell restoration.
4. No live behavior activation.
5. No credential access at import time.

## Full Gate Failure Inventory
The final full-gate blockers fell into four categories.

1. Migration-regression failure
   - `tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py::test_runtime_category_adapters_import_and_preserve_compatibility`
   - Failure: exact equality compared two adapter payloads whose timestamps differed by 1 ms.
   - Root cause: the test compared live `utcnow` timestamps rather than canonical payload content.
   - Resolution: compare payloads after removing timestamp fields.

2. Compatibility-wrapper and scheduler-coupling failures
   - `tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py::test_canonical_bridge_and_connector_imports_are_safe_and_disabled`
   - `tests/test_phase10k8zgm_odds_historical_test_redirection.py::test_canonical_bridge_and_connector_imports_are_safe_and_disabled`
   - `tests/test_phase10k8zgn_odds_proof_history_cleanup.py::test_canonical_bridge_and_connector_imports_are_safe_and_disabled`
   - `tests/test_phase10k8zgo_odds_compatibility_test_retirement.py::test_deleted_files_are_gone_and_canonical_flow_remains_safe`
   - `tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py::test_canonical_odds_flow_remains_safe_and_disabled`
   - `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py::test_canonical_prediction_market_surfaces_import_and_legacy_shells_stay_disabled`
   - `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py::test_canonical_prediction_market_bridge_connectors_and_legacy_shells_remain_importable`
   - `tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py::test_historical_prediction_market_redirection_uses_canonical_bridge_and_keeps_legacy_shells_importable`
   - `tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py::test_canonical_prediction_market_modules_import_and_remain_disabled`
   - `tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py::test_canonical_prediction_market_stack_imports_and_stays_disabled`
   - `tests/test_phase10k8zgx_prediction_market_proof_test_retirement.py::test_canonical_prediction_market_stack_imports_and_stays_disabled`
   - `tests/test_phase10k8zgy_prediction_market_shell_deletion.py::test_canonical_prediction_market_stack_imports_and_stays_disabled`
   - Failure: disabled bridge/client methods raised the expected disabled error, but the assertion was reload-sensitive.
   - Root cause: the tests compared the exact exception object after module reloads.
   - Resolution: assert `RuntimeError` plus `ConnectorDisabledError` class name.

3. Compatibility-wrapper scan failures
   - `tests/test_phase10k8zfz_odds_data_connector_batch_2.py::test_legacy_odds_imports_are_no_longer_active_dependencies`
   - `tests/test_phase10k8zgo_odds_compatibility_test_retirement.py::test_no_active_py_file_imports_deleted_odds_modules`
   - Failure: scans treated a historical proof file as an active dependency.
   - Root cause: proof-history files still contained deleted-shell import statements as evidence.
   - Resolution: reclassify the proof-history file as historical evidence only.

4. Stale test assumptions
   - `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py`
   - `tests/test_phase10k8zgo_odds_compatibility_test_retirement.py`
   - Failure: deleted shell files were still read as if they were live compatibility surfaces.
   - Root cause: historical evidence was being treated as active ownership.
   - Resolution: keep the evidence in docs/tests, but stop requiring it as a runtime dependency.

## Remediation Decisions
1. Safe fixes applied:
   - removed the timestamp equality dependency from the provider migration compatibility test
   - reclassified the historical proof file in the odds import scan
   - changed stale deleted-shell checks to deletion assertions
   - normalized disabled-method assertions to `RuntimeError` plus class-name checks

2. Intentionally preserved:
   - no deleted shell files were restored
   - no live access was enabled
   - no credential lookup was introduced
   - no connector boundary was weakened

## Data/Backtesting Foundation Audit
The next canonical foundation is the data/backtesting stack.

Current canonical or near-canonical anchors:
- `src.core.backtester`
- `src.services.model_backtest_service`
- `src.api.model_backtest_routes`
- `src.api.performance_routes`
- `automation_scheduler.backtesting_engine`
- `automation_scheduler.backtest_dataset_builder`
- `automation_scheduler.backtest_schema`
- `automation_scheduler.backtest_strategy_bankroll`
- `automation_scheduler.backtest_strategy_profiles`

Future canonical targets:
- `src.data`
- `src.backtesting`
- `src.analytics`
- `src.research`

## Tests Run
1. Targeted legacy-failure slice.
2. Full local gate.
3. Service/API/dashboard checkpoint regressions from prior phases.

## Smoke Results
- `python scripts/ops_check.py --mode local --output text --skip-network` passed.

## Next Recommended Phase
Begin the data/backtesting extraction sequence:
1. `src.data`
2. `src.backtesting`
3. `src.analytics`
4. `src.research`
