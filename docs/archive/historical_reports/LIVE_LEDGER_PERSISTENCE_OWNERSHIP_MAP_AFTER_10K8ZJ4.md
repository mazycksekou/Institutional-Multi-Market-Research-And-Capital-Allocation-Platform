# Live Ledger Persistence Ownership Map After 10K8ZJ4

| File | Role | Status |
| --- | --- | --- |
| `src/brokerage/ledger.py` | Local in-memory/model ledger events | Canonical and disabled |
| `src/services/ledger_service.py` | File-backed audit/performance persistence | Canonical local storage |
| `automation_scheduler/paper_trade_ledger.py` | Compatibility trade ledger | Preserved |
| `automation_scheduler/paper_decision_ledger.py` | Compatibility decision ledger | Preserved |
| `bet_log.py` | Root-level compatibility bet log | Preserved |
| `src.data` | Local data/storage contracts | Canonical planning layer |

