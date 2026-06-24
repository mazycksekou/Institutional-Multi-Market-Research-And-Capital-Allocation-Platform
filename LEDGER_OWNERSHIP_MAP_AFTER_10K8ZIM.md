# Ledger Ownership Map After 10K8ZIM

| File | Current status | Canonical owner | Delete-readiness |
| --- | --- | --- | --- |
| `automation_scheduler/audit_ledger.py` | Active compatibility/runtime wrapper | `src.services.ledger_service` | Not delete-ready |
| `automation_scheduler/institutional_audit_ledger.py` | Active compatibility/runtime wrapper | `src.services.ledger_service` | Not delete-ready |
| `automation_scheduler/strategy_performance_ledger.py` | Compatibility wrapper only | `src.services.ledger_service` | Not delete-ready |
| `src/services/ledger_service.py` | Canonical service helper | `src.services` | N/A |
| `src/brokerage/ledger.py` | Canonical disabled brokerage event ledger | `src.brokerage` | N/A |

## Ownership notes

- File-backed audit/performance ledgers belong in the service layer.
- `src.brokerage.ledger` remains the live-shaped disabled event ledger for broker-shaped events.
