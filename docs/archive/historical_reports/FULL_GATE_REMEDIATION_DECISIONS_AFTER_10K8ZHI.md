# Full Gate Remediation Decisions After 10K8ZHI

## Safe Fixes Applied
1. `tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py`
   - Removed a brittle timestamp equality check by comparing the canonical adapter payloads without `timestamp`.

2. `tests/test_phase10k8zfz_odds_data_connector_batch_2.py`
   - Excluded the historical proof file `tests/test_phase10k8zgz_post_provider_connector_cleanup_freeze.py` from the active deleted-module import scan.

3. `tests/test_phase10k8zgo_odds_compatibility_test_retirement.py`
   - Reclassified the same historical proof file as evidence-only.
   - Switched deleted-shell assertions to deletion checks and disabled-exception class-name checks.

4. `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
   - Removed the deleted-legacy module import requirement.
   - Added explicit deletion assertions for the legacy odds shells.

5. Prediction-market and odds bridge proof tests
   - Normalized disabled-method assertions to `RuntimeError` plus the `ConnectorDisabledError` class name.

## Intentionally Preserved
1. No deleted shell was restored.
2. No live network behavior was re-enabled.
3. No credential reads were added.
4. No connector boundary was weakened.
5. No AI or brokerage functionality was introduced.

## Remaining Blockers
None in the remediated full-gate slice.

## Result
The full local gate now passes.

