# PHASE10K8ZIM Ledger Canonicalization

## Summary

Canonical ledger ownership now lives in `src.services.ledger_service`.
The scheduler files remain import-compatible wrappers only.

## What moved

- `append_security_event`, `load_security_audit_records`
- `append_audit_record`, `load_audit_records`
- `append_strategy_performance_record`, `load_strategy_performance_ledger`
- `summarize_strategy_performance`

## Canonical targets

- `src.services.ledger_service`
- `src.brokerage.ledger` remains the disabled brokerage event ledger for broker-shaped events

## Preserved wrappers

- `automation_scheduler/audit_ledger.py`
- `automation_scheduler/institutional_audit_ledger.py`
- `automation_scheduler/strategy_performance_ledger.py`

## Why no deletion occurred

The wrappers are still referenced by runtime code and tests, so deletion is not proof-backed yet.

## Next recommended phase

Redirect any remaining direct wrapper imports to `src.services.ledger_service` and then re-run
delete-readiness proof.
