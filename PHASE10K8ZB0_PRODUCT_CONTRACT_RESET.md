# Product Contract Reset

## Executive Summary
10K8ZB0 completes the Paper-to-Research Backtest Migration by resetting the public dashboard language around market and product lanes, not fake-demo or testing-room copy. The product contract supersedes obsolete public-copy assertions while keeping legacy compatibility aliases in source for transition safety.

## Blocker Resolved
The obsolete public-copy blocker is resolved by moving the visible dashboard toward Data, Validation, Strategy Research, Backtest, Results / Metrics, and Research Mode language. Legacy aliases remain in `LEGACY_INTERNAL_MODE_ALIASES` for compatibility.

## Product Contract Decision
The public dashboard contract is now market-oriented:
- Sports
- Stocks / 0DTE
- Predictions

## Public Product Lanes
`PRODUCT_MARKET_LANES` is the public selector contract. `internal_model_mode_for_product_lane` maps each public lane to its internal mode key.
Local Data remains the contract for controlled fixture-backed research and backtest work.

## Legacy Compatibility Boundary
`LEGACY_INTERNAL_MODE_ALIASES` remains available for frozen compatibility checks, but it is not the public selector contract.

## Paper-to-Research Backtest Language Decision
The visible dashboard now uses Research/backtest mode only. No broker orders, live connectors, API calls, or database writes. The old synthetic-demo sentence is removed from the product-facing UI and retained only in compatibility source text where needed.

## Tests Updated
The focused contract test now checks:
- `PRODUCT_MARKET_LANES`
- `internal_model_mode_for_product_lane`
- new research/backtest workflow copy
- footprint/opening-range workflow copy
- compatibility aliases

## Safety Guardrails Preserved
Internal safety flags remain in place. No live execution behavior is added in this phase.

## Backtest Workflow Boundary
This phase only records the product contract for Data, Validation, Strategy Research, Backtest, and Results / Metrics. It does not add loaders, formulas, or execution logic.

## Live Model Testing Boundary
Later live model testing remains a future phase. This phase is still research/backtest contract only.

## Broker Boundary
No broker execution is added.

## Connector Boundary
No live connectors are added.

## API Boundary
No API calls are added.

## Database Write Boundary
No database writes are added.

## Footprint + Opening Range Backtest Workflow Contract
Large-flow activity is a market-state variable, not an automatic buy or sell signal.

The workflow asks whether footprint improves, degrades, or only conditionally helps the strategy. The contract records:
- Footprint + Opening Range Research
- Pre-run market-state features
- During-run execution-state metrics
- Post-run evaluation metrics
- Comparison experiments
- With footprint filter
- Without footprint filter
- Footprint confirms opening range
- Footprint disagrees with opening range
- Avoid when footprint appears
- Avoid when footprint is absent

### Universal Pre-Run Copy
- Opening Range Metrics
- Large-Flow Metrics
- Liquidity Metrics
- Volatility / News Regime
- Signal Count
- Expected Trade Count
- Estimated Costs

### Universal During-Run Copy
- Entry Price
- Fill Probability
- Slippage
- Spread Paid
- Position Size
- Time in Trade
- Mark-to-Market PnL
- Intraday Drawdown
- Time Under Water
- Stop/Exit Trigger

### Universal Post-Run Copy
- Net PnL
- Profit Factor
- Sharpe
- Sortino
- Max Drawdown
- Win Rate
- Expectancy
- Edge by Regime
- False Positive Rate
- Signal Decay Curve
- Out-of-Sample Stability
- Deflated Sharpe
- Probability of Backtest Overfitting

### 0DTE Footprint Copy
- Opening Range Return
- OR Break Direction
- Large Premium Trade Flag
- Sweep/Block Flag
- Volume / Average Volume
- Volume / Open Interest
- Delta Notional
- Gamma Exposure Estimate
- IV/RV Spread
- Spread Width %
- Time to Expiration
- Fill Price vs Mid
- Slippage per Contract
- Greeks at Entry
- Gamma PnL
- Theta Burn
- Underlying Drift After Flow
- Hedge Pressure Direction
- Edge With Large-Flow
- Edge Without Large-Flow
- OR + Flow Interaction
- Post-Flow Forward Return
- Tail Loss Frequency
- Fill-Adjusted Win Rate

### Prediction Market Footprint Copy
- Market Probability
- Large Trade Flag
- Trade Size / Market Volume
- Order Book Imbalance
- Price Impact per $1,000
- Liquidity Sweep %
- Cross-Market Spread
- Probability Zone
- Liquidity Refill Speed
- Exposure by Outcome
- Hedge Availability
- Settlement PnL
- Mark-to-Market PnL
- Brier Score
- Log Loss
- Calibration Error
- Edge With Whale Flow
- Edge Without Whale Flow
- Post-Whale Price Drift
- Liquidity-Adjusted ROI

### Sports Footprint Copy
- Opening Line
- Current Line
- Closing Line Estimate
- Public Bet %
- Money %
- Bet/Money Divergence
- Reverse Line Movement Flag
- Steam Move Flag
- Sharp Book Lead Flag
- Liquidity/Limit Level
- Injury/News Flag
- Bet Price
- Available Limit
- Odds Slippage
- Book Spread/Vig
- Kelly Fraction
- Exposure by Event
- Line Movement After Bet
- ROI
- CLV
- Win Rate by Odds Bucket
- Expected Value
- Risk of Ruin
- Edge With RLM
- Edge Without RLM
- CLV Persistence
- Closing Edge by Book

## Safety Guardrails Preserved
No guaranteed profit language. No assured profit language. No broker execution. No real trade execution. No live connectors. No API calls. No database writes.

## Next Phase Recommendation
Proceed to 10K8ZB1 Institutional Footprint Metric Coverage Audit.

## Implementation Reviewed In 10K8ZB0
implementation reviewed in 10K8ZB0
