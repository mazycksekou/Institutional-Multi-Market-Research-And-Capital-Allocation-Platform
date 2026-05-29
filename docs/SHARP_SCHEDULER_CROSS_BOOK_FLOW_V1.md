## Sharp Scheduler Cross-Book Flow v1

- The scheduler remains `dry_run=true`, `human_approval_required=true`, `auto_execution_enabled=false`.
- Sharp snapshots are fetched in read-only mode only when:
  - `provider_enabled=true`
  - `live_calls_enabled=true`
  - `credential_status=ok`
  - `auto_execution_enabled=false`
- Only normalized records are consumed.
- Raw provider payloads are not exposed through default API responses.

### Candidate types

- `best_line_available`
- `positive_ev_candidate` only when probability input exists
- `no_vig_market_context` when no-vig probability exists
- `book_disagreement_candidate`
- `arbitrage_candidate` only with valid opposing outcomes
- `middle_candidate` only with a real line corridor and strong market identity
- `watch_recheck` for valid but insufficient cross-book context

### Compact default responses

Default scheduler and queue responses include compact summaries and exclude full boards/raw payloads.
