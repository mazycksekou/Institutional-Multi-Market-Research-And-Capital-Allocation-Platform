# Data Flow Map

## Canonical Flow

```mermaid
flowchart LR
  Source[External source / local fixture] --> Raw[Raw record]
  Raw --> Normalized[Normalized dataset]
  Normalized --> FeatureSnapshot[Feature snapshot]
  Normalized --> Backtest[Backtest dataset]
  FeatureSnapshot --> ModelRun[Model / analysis run]
  FeatureSnapshot --> Dashboard[Dashboard view]
  FeatureSnapshot --> Research[Research artifact]
  Backtest --> Analytics[Backtest / governance report]
  ModelRun --> Analytics
  Dashboard --> Analytics
  Research --> Analytics
```

## Ownership

- Raw and normalized data contracts live under `src.data`
- Feature snapshots are owned by the canonical data platform and reused by backtesting and dashboards
- Reports consume canonical data rather than creating their own duplicate storage
- Historical and versioned records should preserve lineage so the full transformation path remains reproducible

## Governance

- Every record should be traceable from source to downstream usage.
- Any new data path should first ask whether the repo already has a canonical owner for that responsibility.
