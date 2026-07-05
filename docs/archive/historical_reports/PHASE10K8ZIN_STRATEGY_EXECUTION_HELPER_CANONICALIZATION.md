# PHASE10K8ZIN Strategy / Execution Helper Canonicalization

## Summary

Canonical ownership for the reusable strategy and execution helper logic now lives in:

- `src.services.execution_service`
- `src.core.execution`
- `src.core.risk`
- `src.core.portfolio`

The legacy scheduler files remain as compatibility wrappers.

## What moved

- Broker quality scoring helpers
- Small-account review helpers
- Manifold no-bet trap detection helpers
- Institutional execution simulation helpers

## Preserved wrappers

- `automation_scheduler/broker_quality_scoring.py`
- `automation_scheduler/small_account_strategy.py`
- `automation_scheduler/manifold_no_bet_detector.py`
- `automation_scheduler/institutional_execution_desk.py`

## Why no deletion occurred

These wrappers are still used by runtime code and by legacy proof tests. The canonical service
exists, but wrapper deletion is not yet proof-backed.

## Next recommended phase

Redirect any remaining wrapper consumers to `src.services.execution_service` and re-run the
delete-readiness proof before considering wrapper deletion.
