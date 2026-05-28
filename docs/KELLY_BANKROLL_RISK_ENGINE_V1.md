# Kelly + Bankroll/Risk Engine V1

This module adds review-only stake sizing controls.

## Safety Defaults
- human_approval_required: true
- auto_bet_enabled: false
- auto_trade_enabled: false
- auto_execution_enabled: false
- paper_execution_only: true
- full_kelly_auto_execution_allowed: false

## Components
- `automation_scheduler/kelly_staking.py`
- `automation_scheduler/stake_confidence.py`
- `automation_scheduler/drawdown_controls.py`
- `automation_scheduler/exposure_limits.py`
- `automation_scheduler/risk_of_ruin.py`
- `automation_scheduler/bankroll_state.py`

## Behavior
- Full Kelly is primary for review when all gates pass.
- Medium confidence falls back to half/quarter Kelly.
- Low confidence or hard risk failures return `no_stake`.
- Drawdown and exposure caps reduce or block stake.
- Outputs are evaluation only and require human approval.
