# PHASE 10K8ZGW Prediction-Market Final Delete-Readiness Proof

## Executive Summary
This phase runs the final delete-readiness proof for the remaining legacy prediction-market shell files.

The canonical prediction-market flow remains:

`src.services.prediction_market_runtime_bridge` -> `src.connectors.prediction_market_data` -> `src.providers.prediction_markets`

No deletion occurs in this phase. The purpose is to separate historical evidence from active runtime and test dependencies and to decide whether the five legacy shells are actually delete-ready.

> Prediction-market shell deletion is not authorized in this phase. This phase does not authorize live API calls, credential reads at import time, request signing, scraping, broker execution, AI/LLM calls, connector activation, or behavior expansion.

## Files Under Review
- `kalshi_client.py`
- `providers/kalshi_provider.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`

## Scan Method
- searched all tracked runtime Python files for imports and references to the five legacy shells
- searched all tracked tests for active imports, patch targets, and mock targets against the five legacy shells
- separated historical documentation references from active dependencies

## Runtime Ownership Check
The canonical prediction-market bridge/provider/connector stack still owns runtime behavior.

Runtime import dependency scan result:
- no tracked runtime Python file imports any of the five legacy shells

Runtime reference scan result:
- `src/api/market_utility_routes.py` still lists `kalshi_client.py` in a priority filename list
- `kalshi_client.py` still carries legacy metadata that names itself
- `automation_scheduler/kalshi_readonly_adapter.py` still carries legacy metadata that names itself

Those references are historical/evidence-only, not active runtime imports.

## Test Ownership Check
The remaining active test dependencies are the historical compatibility proof files from the prior phases.

The active test files that still import or otherwise touch the legacy prediction-market shells are:
- `tests/test_phase10k8zgv_prediction_market_compatibility_test_retirement.py`
- `tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`
- `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py`
- `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py`
- `tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py`
- `tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py`
- `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- `tests/test_phase10k8zfy_prediction_market_connector_batch_1.py`
- `tests/test_phase10k8zg2_legacy_deletion_readiness_audit.py`
- `tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py`
- `tests/test_phase10k8zgw_prediction_market_final_delete_readiness.py`

`tests/test_screenshot_analysis.py` only contains a historical test name that mentions `kalshi_client`; it is not counted as an active import, patch, or mock dependency.

## Delete-Readiness Decision
None of the five legacy shells is delete-ready yet.

The runtime path is canonical, but the historical compatibility proof tests still keep the legacy shell imports alive. That is the remaining blocker.

## Next Recommended Phase
Reclassify or retire the remaining historical proof tests that still import the legacy prediction-market shells, then run one more delete-readiness proof before any deletion is attempted.

