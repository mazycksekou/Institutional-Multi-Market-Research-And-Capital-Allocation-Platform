# Historical Dataset Acquisition Framework

This document defines the canonical historical dataset acquisition framework for the repository.
It prepares the platform to ingest historical datasets without creating a parallel provider, storage, or validation system.
The concrete runtime owner for the raw acquisition cache stage is documented in [Historical Dataset Acquisition Runtime](./HISTORICAL_DATASET_ACQUISITION_RUNTIME.md).

## Purpose

The framework answers one question: how does the repository acquire, version, certify, and retire historical datasets in a reusable way?

It keeps the following responsibilities on one canonical path:

- dataset acquisition planning
- raw acquisition cache staging
- integrity validation handoff
- normalization handoff
- certification handoff
- dataset versioning
- dataset metadata
- dataset lineage
- point-in-time safety
- quality assurance
- correction workflow
- dataset retirement

The framework does not replace the canonical owners already established by the repository.
It connects them.

## Canonical Ownership

The framework reuses the existing runtime owners rather than creating a duplicate acquisition stack:

- `src.data.local_platform.py` owns the dataset contract, dataset registry, versioning, raw/normalized record lifecycle, validation handoff, and dataset-level readiness reporting.
- `src.data.historical_dataset_acquisition_runtime.py` owns raw acquisition cache staging, integrity validation, and the normalization/certification handoff interface.
- `src.storage.local_store.py` owns the physical table families used by dataset registry, versioning, raw records, normalized records, lineage edges, validation results, and historical acquisition stages.
- `src.data.historical_research_database.py` owns event-centric historical acquisition orchestration, certification, bootstrap, and readiness reporting for the historical research database.
- `src.data.validation.py` owns reusable row-level validation helpers.
- `src.services.streamlit_dashboard_data.py` owns the dashboard-facing readiness adapter.

The acquisition framework does not own provider integrations.
Providers remain acquisition mechanisms only.

## Canonical Acquisition Lifecycle

The reusable acquisition lifecycle is:

Provider -> Raw Acquisition Cache -> Integrity Validation -> Normalization -> Research Asset Certification -> Dataset Certification -> Historical Research Database -> Events -> Markets -> Selections -> Feature Snapshots -> Decision Rows

The lifecycle is reusable for sports, prediction markets, options / 0DTE, and future market families.

## Acquisition Boundaries

Each boundary has one owner:

| Boundary | Canonical owner |
| --- | --- |
| Acquisition | `src.data.historical_dataset_acquisition_runtime` and `src.data.local_platform` |
| Raw Acquisition Cache | `src.data.historical_dataset_acquisition_runtime` and `src.storage.local_store` |
| Integrity Validation | `src.data.historical_dataset_acquisition_runtime` and `src.data.validation` |
| Archive | `src.storage` |
| Normalization | `src.data.historical_dataset_acquisition_runtime` handoff plus domain-specific dataset owners |
| Research Asset Certification | `src.data.historical_research_asset_certification_runtime` |
| Dataset Certification | `src.data.historical_research_database` |
| Storage | `src.storage.local_store` |
| Validation | `src.data.validation` and `scripts` |
| Dataset versioning | `src.data.local_platform` |
| Dataset metadata | `src.data.local_platform` |
| Dataset lineage | `src.data.local_platform` and `src.data.historical_research_database` |
| Point-in-time safety | dataset-specific validation helpers, acquisition runtime guards, and profile contracts |
| Quality assurance | dataset validation and certification summaries |
| Correction workflow | dataset versioning plus certification reruns |
| Dataset retirement | dataset registry status and lifecycle policy |

## Dataset Versioning Contract

The acquisition framework uses dataset versioning metadata so a certified historical dataset can be reproduced later without depending on live providers.

Every versioned dataset record must be able to report:

| Field | Meaning |
| --- | --- |
| `dataset_id` | Permanent canonical dataset identifier. |
| `dataset_version` | Human-readable version string for the certified dataset. |
| `dataset_revision` | Revision marker for correction or enrichment of an existing version. |
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
- quality and coverage scores must be tied to the certified version, not to the provider claim
- versioning must remain compatible with the existing `DatasetContract`, `dataset_registry`, and `dataset_versions` owners

## Minimum Certified NFL Dataset

The first certified historical dataset is the minimum NFL schema.

It must support the minimum certified historical research path without introducing advanced metrics too early.

Required tables and repository-owned storage for the first certified dataset:

- `dataset_registry`
- `dataset_versions`
- `raw_records`
- `normalized_records`
- `validation_results`
- `lineage_edges`
- `historical_acquisition_batches`
- `historical_events`
- `historical_markets`
- `historical_selections`
- `historical_certifications`

Required minimum NFL metadata:

- `dataset_id`
- `dataset_name`
- `dataset_version`
- `dataset_revision`
- `profile_id`
- `profile_family`
- `market_profile`
- `source_name`
- `source_type`
- `source_key`
- `provider_sources`
- `provider_versions`
- `acquisition_timestamp`
- `certification_timestamp`
- `schema_version`
- `lineage_id`
- `quality_score`
- `coverage_score`
- `point_in_time_status`
- `certification_status`

Required minimum NFL relationships:

- one event owns one or more markets
- one market owns one or more selections
- shared event context must not be duplicated across selections
- all rows must remain point-in-time safe
- all rows must preserve lineage back to the certified source bundle

## Multi-Provider Support

The framework allows one repository-owned certified dataset to be composed from multiple provider sources.

Conflict resolution rules:

- prefer canonical repository-owned records over live provider claims once certification is complete
- keep provenance for each source contribution
- record provider version information on the certified dataset version
- if two sources disagree, preserve both source claims in provenance and resolve the certified value through the documented certification workflow
- do not overwrite an older certified version in place without creating a new revision or a documented deprecation path

## Quality Assurance

The framework requires certification evidence before a dataset can be considered ready.

Minimum evidence includes:

- source metadata
- lineage metadata
- schema version
- checksum
- point-in-time safety status
- quality score
- coverage score
- certification status

## Correction Workflow

If a certified dataset must be corrected or enriched:

1. create a new dataset revision or version
2. preserve the previous certified version
3. update provenance and lineage metadata
4. rerun validation and certification
5. record the rationale in the dataset history

## Dataset Retirement

Retirement is a repository-owned lifecycle decision, not a provider-owned decision.

Retirement rules:

- keep historical versions for auditability unless there is a documented correction or deletion policy
- mark deprecated datasets clearly
- do not silently replace certified history
- preserve lineage so future experiments can explain why a dataset changed

## Reuse Expectations

This framework is reusable for:

- NFL
- MLB
- NBA
- prediction markets
- options / 0DTE

The reuse contract is:

provider -> raw acquisition cache -> integrity validation -> normalization -> certification -> historical research database -> event -> market -> selection -> feature snapshot -> decision row

## Phase Boundary

Phase 4.6 defines the minimum certified historical dataset acquisition framework.
Phase 4.7B builds the reusable historical dataset acquisition runtime with raw acquisition cache and integrity validation.
Phase 4.7C completes the historical research asset certification runtime and gates dataset certification on the required research assets.
Phase 4.8 implements the research asset lifecycle runtime and time/entity alignment certification.
Phase 4.9A populates the NFL schedule research asset.
Phase 4.9B builds the research asset coverage planner and provider selection framework.
Phase 5.0 materializes the historical dataset population layer from certified historical research assets.
Phase 5.1 populates reusable features from the certified historical dataset layer and certified event context.

## Out Of Scope

This framework does not:

- ingest data
- implement provider integrations
- scrape sources
- run ETL jobs
- calculate features
- implement mathematical formulas
- build backtests
- train models
- execute trades

It only defines the reusable acquisition and certification relationship that future runtime owners must honor.
