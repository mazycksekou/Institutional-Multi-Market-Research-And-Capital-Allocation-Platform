# Final Execution Blocker Import Scan After 10K8ZIW

Runtime imports were redirected away from the legacy wrappers.

Active runtime consumers now use `src.brokerage.readiness` from:
- `automation_scheduler/__init__.py`
- `automation_scheduler/strategy_score_aggregator.py`
- `automation_scheduler/strategy_promotion.py`

The deleted wrappers are no longer required by runtime code.

Paper ledger modules remain runtime dependencies because they own local file-backed ledgers.
