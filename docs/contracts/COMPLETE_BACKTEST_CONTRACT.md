# Complete Backtest Contract

## Canonical runtime modules

- `src.backtesting.backtest_schema`
- `src.backtesting.historical_bridge`
- `src.backtesting.strategy_profiles`
- `src.backtesting.__init__`

## Backtest surfaces discovered

- dataset contract
- replay plan contract
- simulation plan contract
- leakage detection
- future timestamp detection
- historical bridge from SQLite odds rows
- dashboard summary builders

## Required data shape

| Field group | Role |
|---|---|
| Decision-time fields | model input and snapshot boundary |
| Outcome fields | evaluation and settlement only |
| Leakage fields | never allowed in features |
| Version fields | reproducibility and comparison |

## Backtest invariants

- No future timestamps in a decision-time feature set.
- No settlement or closing fields in the input feature vector.
- Every replay must carry enough metadata to reproduce the dataset version.
