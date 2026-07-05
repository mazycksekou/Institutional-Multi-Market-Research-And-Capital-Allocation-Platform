# PHASE 10K8ZGY - Prediction-Market Shell Deletion Batch

## Executive Summary
This phase deletes only the five proof-backed legacy prediction-market shells after final delete-readiness proof:

* `kalshi_client.py`
* `providers/kalshi_provider.py`
* `betting_providers/kalshi_api.py`
* `automation_scheduler/kalshi_readonly_adapter.py`
* `automation_scheduler/kalshi_market_provider.py`

Canonical prediction-market ownership remains:

`src.services.prediction_market_runtime_bridge -> src.connectors.prediction_market_data -> src.providers.prediction_markets`

No runtime behavior changes are introduced.

## Files Deleted
The five approved legacy shells above are deleted in this phase and nothing else.

deleted files are limited to the approved five-shell set.

## Proof Source
The deletion is backed by the 10K8ZGX final proof-test retirement and the 10K8ZGW final delete-readiness proof.

## Import Scan Before Deletion
Before deletion, the final proof files and historical evidence docs showed the five shells were delete-ready and only evidence references remained.

## Import Scan After Deletion
After deletion, the canonical bridge, connector, and provider stacks remain import-safe, and the deleted shell modules no longer import.

## Tests Run
The phase uses deletion-proof tests plus the canonical connector/provider regression slice and the local ops smoke check.

## Behavior Preserved
The canonical prediction-market flow remains intact, and disabled live behavior stays disabled.

## Remaining Legacy Runtime Files Not Touched
Runtime, dashboard, entrypoint, connector scaffold, AI scaffold, brokerage scaffold, odds module, and market-data module files are preserved.

## Next Recommended Phase
Continue with any remaining legacy runtime owners only after their own delete-readiness proof is complete.

## Required Statement
“Only the five proof-backed prediction-market legacy shells are deleted in this phase. Runtime modules, dashboard files, entrypoints, connector scaffolds, AI scaffolds, brokerage scaffolds, odds modules, and market-data modules are preserved.”
