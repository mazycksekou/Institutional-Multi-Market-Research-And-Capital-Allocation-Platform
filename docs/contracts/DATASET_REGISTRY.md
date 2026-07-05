
# Dataset Registry

## Purpose

The dataset registry is the single catalog for every dataset the repository can ingest, validate, snapshot, or consume.

## Required Fields

| Field | Meaning |
| --- | --- |
| `dataset_id` | Stable machine-readable identifier. |
| `dataset_name` | Human-readable name. |
| `owner` | Canonical owning package or service. |
| `market` | Market family. |
| `sport` | Sport name when applicable. |
| `asset_class` | Asset class. |
| `provider` | Source provider. |
| `storage_location` | Canonical storage path or URI. |
| `schema_version` | Schema version for the dataset. |
| `update_frequency` | Expected refresh cadence. |
| `feature_pack` | Feature pack dependency, if any. |
| `backtest_ready` | Boolean readiness flag. |
| `streamlit_ready` | Boolean readiness flag. |
| `status` | Lifecycle status. |

## Lifecycle States

- `scaffold`
- `registered`
- `validated`
- `active`
- `deprecated`
- `archived`

## Registry Rules

- One dataset id per logical dataset.
- No anonymous datasets.
- Every dataset points to a single canonical storage location.
- Every dataset links to one schema version and one owner.
- Registry entries must be versioned, not overwritten in place without history.
