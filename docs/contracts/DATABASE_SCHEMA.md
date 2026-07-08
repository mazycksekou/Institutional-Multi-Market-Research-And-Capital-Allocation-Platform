
# Database Schema

## Compatibility Targets

The local database abstraction must support:

- SQLite
- DuckDB
- future PostgreSQL compatibility

## Shared Columns

Every canonical table must include the following fields where the table is row-oriented:

| Column | Purpose |
| --- | --- |
| `schema_version` | Tracks schema compatibility. |
| `created_at` | Creation timestamp. |
| `updated_at` | Last modification timestamp. |
| `source` | Raw source identifier. |
| `provider` | Provider identifier. |
| `market` | Market name. |
| `market_type` | Market subtype. |
| `asset_class` | Asset class. |
| `snapshot_id` | Reproducibility key. |
| `lineage_id` | End-to-end provenance key. |
| `version_id` | Version pin for the record family. |
| `quality_score` | Validation and confidence score. |

## Canonical Table Families

| Table family | Purpose | Notes |
| --- | --- | --- |
| `dataset_registry` | Canonical dataset index. | One row per registered dataset. |
| `dataset_versions` | Version history for datasets. | Preserves lineage and compatibility. |
| `raw_records` | Raw acquisition cache records. | Append-only. |
| `normalized_records` | Canonical normalized records. | Preferred downstream read layer. |
| `feature_snapshots` | Materialized feature outputs. | Versioned by feature pack. |
| `lineage_edges` | Parent/child provenance edges. | Graph-friendly storage. |
| `validation_results` | Import and QA results. | Store failures and warnings. |
| `provider_metadata` | Provider contracts and mapping data. | No provider-specific execution logic. |
| `model_runs` | Training, evaluation, calibration, and paper-trading runs. | Supports registry views. |
| `backtest_runs` | Backtest execution metadata and outputs. | Requires leakage metadata. |
| `research_runs` | Experiments and studies. | Supports walk-forward and ablation. |
| `streamlit_layouts` | Dashboard layout versions. | Useful for cache invalidation. |
| `audit_events` | Immutable audit trail. | Append-only. |

## Indexing Guidance

- Index `snapshot_id`, `lineage_id`, and `version_id`.
- Index `market`, `market_type`, `asset_class`, and `provider` for queryable histories.
- Partition or cluster by `schema_version` when the backend supports it.
