# Data Layer Ownership Map After 10K8ZHI

## Target Canonical Owner
`src.data`

## Current Ownership Map

### Historical Data Ingestion and Storage
- `automation_scheduler/data_paths.py`
- `automation_scheduler/data_source_registry.py`
- `automation_scheduler/data_source_research_lanes.py`
- `automation_scheduler/data_availability_tiers.py`
- `automation_scheduler/data_intelligence_registry.py`
- `automation_scheduler/historical_data_sources.py`
- `automation_scheduler/historical_odds_importers.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `automation_scheduler/historical_backtest_bridge.py`
- `automation_scheduler/open_sports_history_sources.py`
- `automation_scheduler/open_sports_history_import.py`
- `automation_scheduler/open_sports_history_backfill.py`
- `automation_scheduler/outcome_store.py`
- `automation_scheduler/outcome_migration.py`
- `automation_scheduler/paper_trade_ledger.py`
- `automation_scheduler/paper_decision_ledger.py`

### Data Quality, Coverage, and Lineage
- `automation_scheduler/model_data_field_catalog.py`
- `automation_scheduler/model_input_coverage.py`
- `automation_scheduler/line_movement_import_contract.py`
- `automation_scheduler/review_queue.py`
- `automation_scheduler/data_lineage`-style logic in `model_governance/data_lineage.py`

### Market Research Stores
- `research/market_research_schema.py`
- `research/market_research_store.py`

## Why These Belong in `src.data`
- They ingest, normalize, persist, or catalogue historical data.
- They are not decision logic.
- They are not execution logic.
- They should be reusable by backtesting, analytics, and research layers.

## Current Risk
- Most of these files still live in `automation_scheduler` or root research folders.
- They should be moved only after backtesting and analytics boundaries are thinned enough to avoid circular imports.

