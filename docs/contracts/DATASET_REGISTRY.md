
# Dataset Registry

## Purpose

The dataset registry is the single catalog for every dataset the repository can ingest, validate, snapshot, certify, version, or consume.

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

## Acquisition And Certification Fields

Historical dataset acquisition uses additional versioning and certification metadata beyond the base registry row.

| Field | Meaning |
| --- | --- |
| `dataset_version` | Human-readable version string for the certified dataset. |
| `dataset_revision` | Revision marker for corrections or enrichment of an existing version. |
| `provider_sources` | Ordered list of source families that contributed to the dataset. |
| `provider_versions` | Source-specific version labels or release identifiers. |
| `acquisition_timestamp` | When the acquisition job collected or materialized the dataset. |
| `certification_timestamp` | When the dataset passed repository certification. |
| `schema_version` | Schema contract used for the dataset. |
| `checksum` | Integrity checksum for the certified dataset payload. |
| `lineage_id` | Stable lineage chain identifier. |
| `certification_status` | Repository certification state for the dataset version. |
| `quality_score` | Repository-owned quality signal for the dataset version. |
| `coverage_score` | Repository-owned coverage signal for the dataset version. |

Rules:

- one logical dataset may have many versions
- one version may have many revisions
- one certified dataset may combine multiple provider sources
- certification status must be explicit
- quality and coverage scores belong to the certified dataset version, not to the provider claim
- this acquisition metadata complements the registry lifecycle states rather than replacing them

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
