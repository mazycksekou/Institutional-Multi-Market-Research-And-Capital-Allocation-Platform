# Current Storage Implementation

## Canonical storage boundary

`src.storage.local_store` is the canonical local persistence boundary for the local data platform.

It provides a small engine abstraction that:

- uses SQLite by default
- imports DuckDB lazily if available
- remains import-safe when DuckDB is not installed
- creates the canonical tables used by the local platform

## Current tables

The engine provisions these canonical tables:

- `dataset_registry`
- `dataset_versions`
- `raw_records`
- `normalized_records`
- `feature_snapshots`
- `lineage_edges`
- `validation_results`
- `provider_metadata`
- `model_runs`
- `backtest_runs`
- `research_runs`
- `streamlit_layouts`
- `audit_events`

## Shared canonical columns

Every table is created with the canonical local-platform metadata columns when they do not already exist in the table definition:

- `schema_version`
- `created_at`
- `updated_at`
- `source`
- `provider`
- `market`
- `market_type`
- `asset_class`
- `snapshot_id`
- `lineage_id`
- `version_id`
- `quality_score`

Primary-key fields defined by the table itself remain authoritative.

## Supported backends

- `sqlite`
- `duckdb` when the package is installed

## Validation notes

- SQLite schema creation, row insertion, querying, upsert, and health reporting are working.
- DuckDB support is intentionally optional and currently unavailable in this environment.
- The engine does not own provider logic, market logic, or dashboard logic.

## Relationship to the canonical platform

- `src.data.local_platform` owns dataset contracts, registry/versioning, lineage, validation, and synthetic fixture proofs.
- `src.services.streamlit_dashboard_data` only exposes a thin dashboard adapter over that canonical local platform.
