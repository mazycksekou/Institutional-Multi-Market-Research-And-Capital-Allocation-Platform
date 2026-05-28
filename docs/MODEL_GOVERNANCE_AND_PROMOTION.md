# Model Governance And Promotion

`model_governance` is the selective activation layer for sportsbook, stock, prediction-market, institutional, Kelly, cross-book, and automation models.

## Safety Defaults

- `human_approval_required = true`
- `auto_bet_enabled = false`
- `auto_trade_enabled = false`
- `auto_execution_enabled = false`
- `paper_execution_only = true`
- `full_kelly_auto_execution_allowed = false`
- `roi_target_is_filter_only = true`

## Activation Tiers

- `research_only`
- `backtest_ready`
- `paper_trade_ready`
- `review_queue_ready`
- `active_scoring_ready`
- `production_candidate`

Promotion is one tier at a time.

## Governance Gates

- model card completeness
- evidence quality
- input quality
- calibration
- backtest realism including vig, slippage, and transaction costs
- walk-forward stability
- drift monitoring
- risk controls
- Kelly eligibility
- review-queue eligibility
- champion/challenger comparison

## Operating Rule

Broad model coverage is allowed in the library.
Active scoring remains selective.

No model becomes active only because it exists in the codebase.
