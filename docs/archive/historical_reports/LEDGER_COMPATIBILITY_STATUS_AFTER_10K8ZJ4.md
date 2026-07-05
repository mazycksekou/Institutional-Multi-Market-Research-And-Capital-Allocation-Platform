# Ledger Compatibility Status After 10K8ZJ4

- Local in-memory ledger events remain canonical in `src.brokerage.ledger`.
- File-backed compatibility ledgers remain preserved.
- `src.services.ledger_service` remains the canonical local audit/performance store.
- Live ledger persistence remains disabled.

