# PHASE10K8ZIL Settlement Canonicalization

## Summary
Canonical settlement helper ownership now lives in:

- `src.brokerage.settlement`
- `src.services.settlement_service`

The scheduler modules remain on disk as import-compatible wrappers only.

## What moved

- `compare_settlement_rules` moved to `src.brokerage.settlement`
- `load_pending_outcome_rows`, `load_imported_outcome_rows`, `summarize_pending_outcome_rows`
- `classify_kalshi_settlement`, `discover_kalshi_settlements_for_pending_rows`
- `validate_imported_outcome_rows`, `build_outcome_completion_report`
- `write_outcome_completion_candidates`

## What remains preserved

- `automation_scheduler/settlement_rule_checker.py`
- `automation_scheduler/settlement_discovery.py`

These files now import from canonical modules and do not own the logic.

## Why no deletion occurred

Runtime and proof tests still import the wrapper paths, so deletion is not yet proof-backed.
This phase is canonicalization and compatibility preservation only.

## Next recommended phase

Redirect the remaining runtime/test references to the canonical service modules, then
re-run delete-readiness proof for the wrapper files.
