# Backtesting Dataset Contracts After 10K8ZHK

## Canonical Dataset Contract

`src.backtesting.contracts.BacktestDatasetContract`

## Contract Properties

- dataset name
- source name
- rows
- timestamp field
- local-only flag
- arbitrary metadata

## Contract Guarantees

- rows are treated as local historical inputs
- ordering can be validated independently
- contract data is serializable to dictionaries

