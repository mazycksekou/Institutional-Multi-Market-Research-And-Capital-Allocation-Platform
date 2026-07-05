# Risk Function Validation (After 10K8ZH2)

## Test Coverage

- `sharpe_ratio` normal case
- `sharpe_ratio` zero volatility error
- `max_drawdown` normal equity curve
- `max_drawdown` no drawdown
- `portfolio_risk` using covariance matrix
- `exposure_summary` totals
- compatibility import from `risk_engine.py` (if wrappers added)
- no connector / provider / broker imports
