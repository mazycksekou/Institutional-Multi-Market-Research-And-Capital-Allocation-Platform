# PHASE 10K8ZGP Odds Compatibility Shell Deletion

## Executive Summary
This phase deletes only the seven proof-backed legacy odds compatibility shells after the final compatibility-proof tests were retired in 10K8ZGO.

The canonical odds flow remains:
- `src.services.odds_runtime_bridge`
- `src.connectors.odds_data`
- `src.providers.sportsbooks`

Legacy odds shells are removed only after import proof, deletion proof, and local regression proof were established in prior phases.

## Current HEAD
`2f95c3e6ced8ef45259de98fdbf0003694d91dbd`

## Purpose
Delete the seven proof-backed legacy odds compatibility shells without changing runtime behavior.

## Scope
In scope:
- delete the seven approved legacy odds compatibility shells
- prove the deleted files are gone
- prove canonical odds flow still imports and stays disabled
- prove no active test imports deleted odds modules
- prove no tracked runtime file imports deleted odds modules

Out of scope:
- live API calls
- credential reads at import time
- connector activation
- broker execution
- bet execution
- AI/LLM calls
- dashboard rewrites
- main entrypoint rewrites

## Non-Goals
- No runtime behavior changes
- No live API calls
- No credential reads at import time
- No requests/httpx/websocket activation
- No scraping
- No connector activation
- No AI/LLM or brokerage work
- No unrelated file deletion

## Big-Picture Architecture
- `src.services.odds_runtime_bridge` owns the runtime odds bridge
- `src.connectors.odds_data` owns the disabled odds connector boundary
- `src.providers.sportsbooks` owns canonical sportsbook normalization and validation

## Proof Source From 10K8ZGO
The deletion proof is grounded in:
- `tests/test_phase10k8zgo_odds_compatibility_test_retirement.py`
- `ODDS_COMPATIBILITY_TEST_RETIREMENT_MAP_AFTER_10K8ZGO.md`
- `ODDS_FINAL_IMPORT_SCAN_AFTER_10K8ZGO.md`
- `FINAL_ODDS_SHELL_DELETE_PROOF_AFTER_10K8ZGO.md`

## Import Scan Before Deletion
Before deletion, the final proof trail had already reclassified the legacy shells as delete-ready and retired compatibility tests had been redirected away from shell retention.

## Import Scan After Deletion
After deletion, the active Python files no longer import the seven deleted odds shells, and the remaining textual references are historical evidence only.

## Tests Run
- `python -m py_compile tests/test_phase10k8zgo_odds_compatibility_test_retirement.py tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py`
- `pytest tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py tests/test_phase10k8zgo_odds_compatibility_test_retirement.py tests/test_phase10k8zgn_odds_proof_history_cleanup.py tests/test_phase10k8zgm_odds_historical_test_redirection.py tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py -q`

## Behavior Preserved
- Canonical odds flow remains intact.
- Disabled connector behavior remains disabled.
- No live odds access is enabled.
- No credentials are read at import time.

## Remaining Legacy Odds / Runtime Files Not Touched
- `src.services.odds_runtime_bridge`
- `src.connectors.odds_data`
- `src.providers.sportsbooks`
- `main.py`
- `streamlit_app.py`
- `quant_engine.py`
- `risk_engine.py`
- `src.services.enrichment_service`
- `src.api` routing and dashboard support files

## Next Recommended Phase
Continue cleanup of historical odds evidence docs only if desired; no further odds shell deletion is required for the compatibility shell batch.

## Required Statement
Only the seven proof-backed legacy odds compatibility shells are deleted in this phase. Runtime modules, dashboard files, entrypoints, connector scaffolds, AI scaffolds, brokerage scaffolds, and prediction-market legacy modules are preserved.
