# Cross-Book Opportunity Engine

This subsystem provides evaluation-only infrastructure for:

- EV line shopping
- no-vig pricing
- consensus pricing
- cross-book comparison
- arbitrage candidate detection
- middle candidate detection
- stake simulation
- settlement and liquidity risk checks
- CLV tracking

## Safety

- `auto_bet_enabled = false`
- `auto_trade_enabled = false`
- `auto_execution_enabled = false`
- `human_approval_required = true`

No live execution is implemented.

## Candidate Types

- `positive_ev`
- `best_line_available`
- `no_vig_ev`
- `consensus_ev`
- `stale_line_ev`
- `arbitrage_candidate`
- `middle_candidate`
- `clv_watch`

## Review Queue Fields

Stored review items include:

- books compared and best/worst books
- best/worst lines and odds
- model, implied, no-vig, and consensus probabilities
- EV and ROI estimates
- arbitrage implied sum
- middle zone and width
- break-even probability
- stake plan
- max loss and max gain
- market identity confidence
- settlement risk
- stale data risk
- liquidity and execution feasibility

## User-Facing Language

Blocked phrases:

- `lock`
- `guaranteed`
- `risk-free`
- `sure thing`
- `can't lose`
