# Odds Compatibility Delete Readiness After 10K8ZGK

## Executive Summary
The legacy odds compatibility shells are not delete-ready yet. The canonical odds connector boundary exists, but runtime and proof-test references still block deletion.

## Current HEAD
`88db1f3d6ab4cc7d0c8cd606062b165e702b6cf0`

## Purpose
Provide a file-by-file delete-readiness decision for the preserved legacy odds compatibility shells.

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
- No source migration
- No behavior expansion
- No live API calls
- No credential reads at import time

## Big-Picture Architecture
- `src.connectors.odds_data` owns the canonical odds connector boundary
- `src.providers` owns provider normalization and routing
- Compatibility shells stay on disk only while runtime and proof references still require them

## Delete Readiness Matrix
| File | Status | Reason |
| --- | --- | --- |
| `sharp_client.py` | Blocked | Still referenced by historical proof tests and compatibility evidence |
| `providers/sharp_provider.py` | Blocked | Still imported by `src/services/enrichment_service.py` |
| `betting_providers/sharp_api.py` | Blocked | Still referenced by historical proof tests |
| `betting_providers/the_odds_api.py` | Blocked | Still referenced by historical proof tests |
| `betting_providers/sportsgameodds.py` | Blocked | Still referenced by historical proof tests |
| `automation_scheduler/sharp_sportsbook_adapter.py` | Blocked | Still referenced by runtime scheduler code |
| `automation_scheduler/sportsbook_odds_provider.py` | Blocked | Still referenced by runtime scheduler code |

## Delete-Ready Files
None yet.

## Blocked Files
All seven legacy odds compatibility shells remain blocked.

## Why Deletion Did Not Occur
The phase is proof-only, and the remaining shells still have runtime or test references that have not been fully retired.

## Required Statement
Odds compatibility shell deletion is authorized only after runtime imports, test imports, compatibility proof, and full local gate proof are clean. This phase proves readiness only and does not delete legacy odds modules.

## Next Recommended Deletion Phase
Retire the remaining runtime scheduler and enrichment references, then rerun the proof slice before any deletion is attempted.
