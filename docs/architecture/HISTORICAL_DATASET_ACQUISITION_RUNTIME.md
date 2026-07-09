# Historical Dataset Acquisition Runtime

This document defines the reusable runtime owner for the raw acquisition cache stage.
It is architecture only. It does not download data, authenticate with providers, or perform live ingestion.

The runtime exists so historical acquisition can pass through a durable raw cache before certification touches the historical research database.

## Purpose

The runtime answers one question: how does the repository stage immutable raw acquisition payloads, validate them, and prepare handoff bundles for normalization and certification without creating a parallel provider system?

It keeps the following responsibilities on one canonical path:

- raw acquisition cache staging
- immutable payload preservation
- acquisition timestamp capture
- source metadata capture
- provider metadata capture
- checksum generation
- integrity validation handoff
- normalization handoff
- research asset certification handoff
- dataset certification handoff
- dataset registry integration
- dataset versioning integration
- lineage capture
- raw readiness reporting

## Canonical Ownership

The runtime reuses the existing canonical owners rather than introducing a new acquisition stack:

- `src.data.local_platform.py` owns the dataset contract, dataset registry, versioning, raw/normalized record lifecycle, validation handoff, and dataset-level readiness reporting.
- `src.data.historical_dataset_acquisition_runtime.py` owns raw acquisition cache staging, integrity validation, and the normalization/certification handoff interface.
- `src.storage.local_store.py` owns the physical table families used by the dataset registry, versioning, raw records, normalized records, lineage edges, and validation results.
- `src.data.validation.py` owns reusable row-level validation helpers.
- `src.data.historical_research_asset_certification_runtime.py` owns research asset certification, certification scoring, and the asset-level handoff into dataset certification.
- `src.data.historical_research_database.py` owns dataset certification and the event-centric historical research database that consumes the handoff bundles.
- `src.services.streamlit_dashboard_data.py` owns the dashboard-facing readiness adapter.

The runtime does not own provider integrations.
Providers remain acquisition mechanisms only.

## Canonical Acquisition Lifecycle

The reusable acquisition lifecycle is:

Provider -> Raw Acquisition Cache -> Integrity Validation -> Normalization -> Research Asset Certification -> Dataset Certification -> Historical Research Database

The runtime is the stage that makes the first two transitions concrete.

## Raw Acquisition Cache Contract

Every raw acquisition cache entry must be able to report:

- dataset identifier
- dataset name
- market profile
- source name
- source type
- source key
- provider
- provider sources
- provider versions
- source bundle identifier
- acquisition timestamp
- schema version
- checksum
- lineage identifier
- storage location
- readiness state

The raw cache is immutable after staging.
The repository keeps the original raw payload so future normalization can be rerun without redownloading data.

## Integrity Validation Contract

The runtime validates the raw acquisition cache before handoff.

Validation concerns include:

- checksum validation
- required field validation
- timestamp validation
- schema validation
- duplicate detection
- corruption detection
- point-in-time safety
- profile compatibility

The runtime does not replace the canonical validation owners.
It prepares data for them and stores their results in shared storage.

## Normalization Handoff

The runtime does not normalize domain rows itself.
It prepares the normalized handoff bundle with:

- source tables
- raw row counts
- source table counts
- dataset version
- lineage identifiers
- validation results
- minimum schema targets

Normalization remains owned by the historical research database and the domain dataset owners.

## Certification Handoff

The runtime also prepares a certification handoff bundle with:

- dataset identifier
- dataset version
- source bundle metadata
- validation results
- raw record counts
- lineage identifiers
- research asset certification results
- certification scope

Research asset certification remains owned by `src.data.historical_research_asset_certification_runtime`.
Dataset certification remains owned by the historical research database.

## Multi-Provider Support

The runtime assumes one certified dataset may combine multiple providers.

Supported acquisition roles:

- primary acquisition
- verification
- fallback
- enrichment

The raw cache preserves provenance so the repository can explain which provider or source family contributed to each staged payload.

## Reuse Expectations

This runtime is reusable for:

- NFL
- MLB
- NBA
- prediction markets
- options / 0DTE

The reuse contract is:

provider -> raw acquisition cache -> integrity validation -> normalization -> certification -> historical research database

## Phase Boundary

Phase 4.7B builds the reusable historical dataset acquisition runtime with raw acquisition cache and integrity validation.
Phase 4.7C completes the historical research asset certification runtime and gates dataset certification on the required research assets.
Phase 4.9A populates the NFL schedule research asset after acquisition runtime and integrity validation are complete.

## Out Of Scope

This runtime does not:

- ingest data directly into the historical research database
- authenticate with providers
- implement provider-specific APIs
- normalize domain features
- build backtests
- build models
- execute trades

It only defines the reusable runtime relationship between governed acquisition stages.

## Worldview Compatibility

This runtime improves future Worldview compatibility by making raw payload retention, integrity validation, and provenance explicit.

Future Worldview requests should be able to ask:

- which raw payloads were staged
- which source bundle produced them
- which validation checks passed
- which normalization bundle should be reused
- which certification bundle should be reused
