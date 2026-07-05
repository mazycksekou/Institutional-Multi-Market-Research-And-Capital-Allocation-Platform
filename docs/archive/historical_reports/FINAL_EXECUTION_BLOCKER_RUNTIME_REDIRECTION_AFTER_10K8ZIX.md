# Final Execution Blocker Runtime Redirection After 10K8ZIX

Runtime imports were redirected to canonical execution boundaries:
- `automation_scheduler/__init__.py`
- `automation_scheduler/strategy_score_aggregator.py`
- `automation_scheduler/strategy_promotion.py`

All three now rely on `src.brokerage.readiness`.
