# PHASE10K8ZGK Odds Compatibility Shell Delete Readiness

## Executive Summary
`10K8ZGK` proves whether the preserved legacy odds compatibility shells are ready for deletion. The canonical odds boundary already lives under `src.connectors.odds_data`, and the legacy odds modules now behave as disabled shells. This phase does not delete anything; it only measures whether the remaining compatibility surfaces are still needed.

## Current HEAD
`88db1f3d6ab4cc7d0c8cd606062b165e702b6cf0`

## Purpose
Determine whether the legacy odds compatibility shells can be removed in a later phase without breaking runtime imports, test imports, or the disabled-shell contract.

## Scope
Targets reviewed:
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`

## Non-Goals
- No files deleted
- No files moved
- No source-function migration
- No public functions removed
- behavior unchanged
- No behavior expansion
- No live API calls
- No credential reads at import time
- No requests/httpx/websocket activation

## Big-Picture Architecture
- `src.connectors.odds_data` is the canonical odds connector boundary
- `src.providers` owns provider normalization and routing
- `automation_scheduler` remains an orchestration/compatibility surface until the remaining imports are proven unnecessary

## Imports/References Before Redirection
- `src/services/enrichment_service.py` still imports `providers.sharp_provider`
- `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py` still imports all seven legacy odds shell targets for proof
- `tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py` still imports the legacy odds shells to prove connector redirection
- `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py` still imports the legacy odds shells to prove disabled connector migration
- `tests/test_phase10k8zfz_odds_data_connector_batch_2.py` still imports the legacy odds shells as historical compatibility evidence
- `automation_scheduler/scheduler_runner.py` and `automation_scheduler/__init__.py` still instantiate the sportsbook adapter path

## Imports/Tests Redirected
- `tests/test_screenshot_analysis.py` now treats sharp enrichment as disabled-shell behavior instead of live sharp API behavior
- `tests/test_sharp_sportsbook_adapter.py` now verifies disabled-shell behavior instead of live sportsbook HTTP behavior

## Remaining References After Redirection
- Legacy odds shells remain importable and are still referenced by proof tests
- The enrichment service still depends on `providers.sharp_provider`
- The scheduler still depends on `automation_scheduler.sharp_sportsbook_adapter` and `automation_scheduler.sportsbook_odds_provider`

## Delete-Readiness Decisions
| File | Decision | Why |
| --- | --- | --- |
| `sharp_client.py` | Blocked | Still imported by proof tests and historical odds connector tests |
| `providers/sharp_provider.py` | Blocked | Still imported by `src/services/enrichment_service.py` |
| `betting_providers/sharp_api.py` | Blocked | Still imported by proof tests |
| `betting_providers/the_odds_api.py` | Blocked | Still imported by proof tests |
| `betting_providers/sportsgameodds.py` | Blocked | Still imported by proof tests |
| `automation_scheduler/sharp_sportsbook_adapter.py` | Blocked | Still imported by runtime scheduler code |
| `automation_scheduler/sportsbook_odds_provider.py` | Blocked | Still imported by runtime scheduler code |

## Which Files Are Delete-Ready
None yet.

## Which Files Remain Blocked
All seven target shells remain blocked.

## Why Deletion Did Not Occur
The phase is proof-only, and the remaining shells still have runtime or proof-test references that have not been fully retired.

## Compatibility Import Note
Legacy odds modules remain importable, but they are not delete-ready.

## Required Statement
Odds compatibility shell deletion is authorized only after runtime imports, test imports, compatibility proof, and full local gate proof are clean. This phase proves readiness only and does not delete legacy odds modules.

## Next Recommended Deletion Phase
Redirect the remaining runtime and historical test references off the legacy shells, then delete the shells only after the proof is clean.
