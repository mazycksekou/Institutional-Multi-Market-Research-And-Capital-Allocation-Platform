
# Model Registry Architecture

## Scope

The registry tracks:

- models
- feature packs
- training versions
- evaluation runs
- calibration runs
- paper trading runs
- backtests

## Registry Records

| Record type | Purpose |
| --- | --- |
| `model` | Stable model identity and artifact pointer. |
| `feature_pack` | Input feature bundle identity. |
| `training_run` | Training metadata and source versions. |
| `evaluation_run` | Offline evaluation results. |
| `calibration_run` | Calibration metadata and curves. |
| `paper_trading_run` | Simulated deployment trail. |
| `backtest_run` | Backtest linkage and leakage evidence. |

## Rules

- No model implementation is defined here; this is registry architecture only.
- Every model artifact must link back to its input feature pack and dataset versions.
- Registry history must be queryable by version id and lineage id.
