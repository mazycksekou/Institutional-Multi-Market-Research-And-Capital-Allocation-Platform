# Bet Log Migration Plan After 10K8ZHD

## Current State

`bet_log.py` is still the local bet ledger shell. It is importable and local-only, and it does not activate live execution.

## Classification

- `bet_log.py`: `COMPATIBILITY_SHIM_CANDIDATE`
- `create_bet_log_entry`: compatibility logging helper
- `append_bet_log_entry`: compatibility storage helper
- `read_bet_log_entries`: compatibility storage helper
- `update_bet_result`: compatibility storage helper
- `get_performance_summary`: compatibility reporting helper
- `get_bankroll_summary`: compatibility reporting helper
- `get_clv_report`: compatibility reporting helper

## Migration Notes

- Bet logging can remain root-level until a dedicated service/storage plan exists.
- Pure CLV and odds math should remain in `src.core`.
- No database rewrite, no external write, and no broker execution are authorized here.

## Next Step

When a dedicated storage service is introduced, `bet_log.py` can become a much thinner compatibility shell or be retired in a proof-backed batch.
