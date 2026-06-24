# Settlement Ownership Map After 10K8ZIL

| File | Current status | Canonical owner | Delete-readiness |
| --- | --- | --- | --- |
| `automation_scheduler/settlement_rule_checker.py` | Compatibility wrapper only | `src.brokerage.settlement` | Not delete-ready |
| `automation_scheduler/settlement_discovery.py` | Runtime wrapper / compatibility surface | `src.services.settlement_service` | Not delete-ready |
| `src/brokerage/settlement.py` | Canonical helper | `src.brokerage` | N/A |
| `src/services/settlement_service.py` | Canonical service helper | `src.services` | N/A |

## Ownership notes

- Settlement rule comparison is now brokerage-owned because it is a pure deterministic execution-adjacent helper.
- Read-only settlement discovery is service-owned because it orchestrates local classification, file-backed discovery, and compatibility output.
- The wrapper files remain because callers and proof tests still reference them.
