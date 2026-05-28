# Later Auto Execution

The `automation_scheduler/later` package exists to document future execution policy boundaries without enabling live execution.

Current state:

- `auto_execution_enabled = false`
- `auto_bet_enabled = false`
- `auto_trade_enabled = false`
- `paper_execution_only = true`
- `human_approval_required = true`

The v1 scheduler does not place bets, submit orders, or expose live execution endpoints.

## Future Requirements Before Any Enablement

- intentional configuration changes
- explicit human approval controls
- audited paper-trading validation
- provider credential onboarding
- execution guardrail review
- execution readiness checks passing

Until then, readiness remains `not_ready`.
