# MODEL GOVERNANCE V1

This release adds a project-wide governance layer for sport, stock, prediction-market, institutional, cross-book, Kelly, scheduler, review queue, alerts, provider, and research workflows.

Safety defaults:
- human_approval_required=true
- auto_bet_enabled=false
- auto_trade_enabled=false
- auto_execution_enabled=false
- paper_execution_only=true
- full_kelly_auto_execution_allowed=false

Activation tiers enforce selective scoring and no autonomous execution.
