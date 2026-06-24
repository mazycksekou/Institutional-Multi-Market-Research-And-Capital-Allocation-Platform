# Backtesting Leakage Validation After 10K8ZHK

## Canonical Leakage Rules

- rows must not contain future timestamps relative to the evaluation time
- leakage checks are deterministic and local-only
- simulation plans must not enable trade execution

## Reported Failure Modes

- future timestamps
- missing timestamps are skipped rather than treated as live data
- malformed rows can be reported by the calling layer

## Behavior

- leakage checks do not fetch data
- leakage checks do not execute trades
- leakage checks produce structured reports only

