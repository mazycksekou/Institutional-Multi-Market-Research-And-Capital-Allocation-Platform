# Backtesting Foundation Ownership Map After 10K8ZHK

## Canonical Owner

`src.backtesting`

## Module Map

| Canonical Module | Responsibility | Notes |
| --- | --- | --- |
| `src/backtesting/__init__.py` | Package export surface | Import-safe umbrella |
| `src/backtesting/contracts.py` | Dataset/replay/simulation contracts | Pure dataclasses only |
| `src/backtesting/datasets.py` | Dataset order validation | Chronological ordering checks |
| `src/backtesting/leakage.py` | Leakage detection | Future timestamp detection |
| `src/backtesting/replay.py` | Replay planning | Local-only, no execution |
| `src/backtesting/simulation.py` | Simulation planning | No trade execution |

## Ownership Notes

- Backtest datasets belong here, not in services or API routes.
- Replay planning belongs here as a contract, not as execution.
- Simulation planning belongs here as a contract, not as a broker action.

## What Is Not Owned Here

- live data ingestion
- broker order submission
- strategy activation
- UI rendering
- API routes

