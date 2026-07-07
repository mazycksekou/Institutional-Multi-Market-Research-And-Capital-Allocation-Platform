# NFL Backtest Contract

This contract defines the minimum reproducible shape for an NFL backtest slice.
It is designed for point-in-time analysis and leakage control.

## Backtest Principles

- use only data available at decision time
- preserve cutoff timestamps
- version all inputs
- record all outputs
- store the exact feature snapshot used
- keep settled outcomes separate from decision-time features

## Required Input Layers

1. raw NFL records
2. normalized NFL records
3. feature snapshots
4. market snapshots
5. settled outcomes
6. calibration context
7. lineage metadata

## Required Backtest Fields

- `run_id`
- `backtest_row_id`
- `sport`
- `season`
- `week`
- `game_id`
- `market`
- `selection`
- `line_value`
- `decision_ts`
- `cutoff_ts`
- `feature_snapshot_id`
- `feature_pack_version`
- `model_version`
- `settled_outcome`
- `open_odds`
- `close_odds`
- `clv`
- `roi`
- `expected_value`
- `calibration_bucket`

## Leakage Protections

The backtest contract must prevent:

- future game results entering pregame features
- postgame odds leaking into the decision set
- settled outcomes being mixed with decision-time inputs
- missing-timepoint features being silently fabricated

## Required Validation Checks

- point-in-time cutoff verification
- schema version verification
- feature snapshot version verification
- duplicate key detection
- join key validation
- settlement outcome availability
- market compatibility
- sport compatibility

## Required Outputs

- per-row backtest results
- run-level summary
- calibration summary
- CLV summary
- ROI summary
- leakage audit summary
- reproducibility manifest

## Current Maturity

The repository has diagnostics and readiness pieces for NFL analysis, but it does not yet have a complete validated backtest dataset.

So the contract is:

- real
- explicit
- usable for planning
- not yet fully instantiated by data

## Related Minimum Contract

The minimum reusable decision-row shape is defined in:

- `docs/contracts/MINIMUM_BACKTEST_ROW_CONTRACT.md`
- `docs/contracts/NFL_MINIMUM_BACKTEST_ROW_CONTRACT.md`

Those documents define when a row is eligible to become backtest-ready.
