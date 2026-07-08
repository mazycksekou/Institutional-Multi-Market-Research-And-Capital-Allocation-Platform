# Phase 4.6 Minimum Certified Historical Dataset Acquisition Framework

## Summary

Phase 4.6 defines the reusable historical dataset acquisition framework that will prepare the repository for the minimum certified historical dataset.
No provider ingestion or runtime backfill was performed in this phase.

## Sources Evaluated

The phase reuses the existing dataset, lineage, and historical research owners already documented in the repository:

- `src.data.local_platform.DatasetContract`
- `src.data.local_platform.LocalDataPlatform`
- `src.data.historical_research_database.HistoricalResearchDatabase`
- `src.storage.local_store.LocalStorageEngine`
- `src.data.validation.validate_dataset_rows`
- `src.data.validation.validate_dataset_metadata`
- `src.data.market_profile_registry`
- `src.data.market_profile_contracts`
- `src.market_intelligence.market_profiles`

## Sources Selected for This Phase

Selected for the Phase 4.6 framework:

- the canonical dataset registry and versioning owner in `src.data.local_platform`
- the event-centric historical research database in `src.data.historical_research_database`
- shared local storage and validation layers
- existing NFL profile-aware contracts and lineage helpers

This phase does not activate live provider ingestion.

## Framework Delivered

The framework now documents:

- acquisition boundaries
- archive ownership
- normalization handoff
- certification handoff
- dataset versioning
- dataset metadata
- dataset lineage
- point-in-time safety
- quality assurance
- correction workflow
- dataset retirement

## Minimum NFL Dataset Contract

The first certified dataset remains the minimum NFL schema.
The framework describes the required metadata and table families without ingesting data:

- acquisition batch tracking
- event records
- market records
- selection records
- certification records
- dataset version and revision metadata
- provider source provenance
- quality and coverage scoring

## Multi-Provider Architecture

The framework documents how one repository-owned dataset can combine multiple provider sources while keeping the certified version reproducible.

The repository, not the provider, remains the canonical source of truth after certification.

## Shared Logic Reused

- `src.data.local_platform`
- `src.data.historical_research_database`
- `src.storage.local_store`
- `src.data.validation`
- `src.data.market_profile_contracts`
- `src.data.market_profile_registry`
- `src.market_intelligence.market_profiles`

## Duplicate Logic Avoided

- no new provider framework was created
- no market-specific acquisition engine was created
- no duplicate storage engine was created
- no duplicate validation system was created
- no duplicate lineage system was created
- no decision-row storage primitive was introduced

## Engineering Improvements

Implemented:

- the acquisition framework now names the canonical dataset registry owner and the historical research database owner explicitly
- dataset versioning is documented as a first-class acquisition concern
- the minimum NFL dataset is described as the first certification target
- multi-provider provenance and conflict-resolution expectations are explicit

Deferred:

- runtime helper refactors
- provider integration
- dataset ingestion
- certification execution
- feature population

## Validation Flow

The framework validates:

- required identifiers
- required timestamps
- lineage metadata
- source metadata
- point-in-time safety
- schema version consistency
- certification state
- dataset quality and coverage metadata

## Senior Systems Engineer Review

The framework is a good fit for the repository.

What is strong:

- it extends the existing dataset and historical research owners instead of creating a separate acquisition stack
- it keeps provider contributions separate from repository-owned certified datasets
- it documents versioning, lineage, and certification as first-class acquisition concerns
- it remains reusable for MLB, NBA, prediction markets, and options / 0DTE

What remains intentionally deferred:

- actual acquisition jobs
- provider-specific adapters
- certification execution against real data
- future market-specific enrichments

Overall recommendation:

- keep the acquisition framework small and canonical
- reuse `src.data.local_platform` for dataset registry and versioning
- reuse `src.data.historical_research_database` for event-centric historical certification
- do not create a new acquisition subsystem unless a second market proves the shared contract is insufficient

## Worldview Intelligence Review

This framework improves future Worldview compatibility by making dataset readiness, versioning, lineage, and certification rules explicit.

That improves:

- reproducibility
- evidence quality
- experiment readiness
- historical dataset governance
- future feature generation
- future mathematical implementation

## Readiness for Phase 4.7B - Historical Dataset Acquisition Runtime

The repository is ready for Phase 4.7B - Historical Dataset Acquisition Runtime to acquire and stage the minimum certified historical dataset using the canonical acquisition framework.
