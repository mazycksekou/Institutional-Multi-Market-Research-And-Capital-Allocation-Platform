# Historical Research Asset Certification Runtime

This document defines the canonical runtime owner for certification of individual research assets before dataset certification completes.
It is architecture only. It does not download data, authenticate with providers, or perform live ingestion.

The runtime exists so the repository can trust each governed research asset on its own before a historical dataset is promoted to certified status.

## Purpose

The runtime answers one question: how does the repository certify each acquired research asset, preserve the evidence, and only then allow the dataset certification layer to promote the dataset?

It keeps the following responsibilities on one canonical path:

- research asset certification orchestration
- asset-level completeness tracking
- asset-level coverage scoring
- point-in-time safety evaluation
- lineage and provenance capture
- certification-state classification
- certification-failure classification
- dataset-gating handoff
- dashboard readiness reporting

## Canonical Ownership

The runtime reuses the existing canonical owners rather than introducing a duplicate certification stack:

- `src.data.historical_research_asset_certification_runtime` owns research-asset certification contracts, asset-level certification rows, dataset-gating handoff, and certification readiness summaries.
- `src.storage.local_store` owns the physical certification tables used by the asset and dataset certification ledgers.
- `src.data.validation` owns reusable row-level validation helpers.
- `src.data.historical_research_database` owns dataset certification orchestration after the required research assets pass.
- `src.services.streamlit_dashboard_data` owns the dashboard-facing readiness adapter.

The runtime does not own provider integrations.
Providers remain acquisition mechanisms only.

## Certification Sequence

The reusable certification sequence is:

Provider -> Raw Acquisition Cache -> Integrity Validation -> Research Asset Certification -> Dataset Certification -> Historical Research Database

The runtime is the stage that makes the asset-level promotion concrete before dataset-level certification happens.

## Research Asset Certification Contract

Every research asset certification entry must be able to report:

- research asset identifier
- asset type
- asset version
- schema version
- coverage
- completeness
- point-in-time safety
- lineage
- provider provenance
- checksum
- quality score
- certification score
- certification timestamp
- certification version
- certification status
- certification notes

## Certification States

The canonical certification states are:

- `UNKNOWN`
- `DISCOVERED`
- `ACQUIRED`
- `VALIDATED`
- `PARTIALLY_CERTIFIED`
- `CERTIFIED`
- `REJECTED`
- `SUPERSEDED`
- `REVOKED`

## Certification Failure Reasons

The canonical certification failure reasons are:

- `Missing Fields`
- `Coverage Failure`
- `Schema Failure`
- `Timestamp Failure`
- `Duplicate Records`
- `Corrupted Payload`
- `Failed Checksum`
- `Lineage Failure`
- `Provider Conflict`
- `Point-In-Time Violation`

## Dataset Gating Rule

A historical dataset may only become certified when:

- every required research asset passes certification,
- required relationships validate,
- coverage requirements validate,
- lineage validates,
- point-in-time safety validates,
- and the dataset-level certification record confirms the asset-level result.

## Multi-Provider Support

The runtime assumes one certified dataset may combine multiple providers.

Supported acquisition roles:

- primary acquisition
- verification
- fallback
- enrichment

The repository stores one certified truth while preserving the source evidence for review and replay.

## Readiness Reporting

The runtime exposes the following readiness concepts to dashboard and governance consumers:

- certification readiness
- failed certifications
- certification scores
- certification reasons
- missing research assets
- pending research assets
- dataset readiness

## Reuse Expectations

This runtime is reusable for:

- NFL
- MLB
- NBA
- prediction markets
- options / 0DTE

The reuse contract is:

provider -> raw acquisition cache -> integrity validation -> research asset certification -> dataset certification -> historical research database

## Phase Boundary

Phase 4.7C completes the historical research asset certification runtime and promotes the individual research assets required by the minimum certified historical dataset.
Phase 4.8 implements the research asset lifecycle runtime and time/entity alignment certification on top of certified assets and certified datasets.

## Out Of Scope

This runtime does not:

- download data directly into the historical research database
- authenticate with providers
- implement provider-specific APIs
- calculate features
- build backtests
- build models
- execute trades

It only defines the reusable runtime relationship between governed acquisition, asset certification, and dataset certification stages.

## Worldview Compatibility

This runtime improves future Worldview compatibility by making raw payload retention, asset-level certification evidence, and provenance explicit.

Future Worldview requests should be able to ask:

- which research assets were certified
- which research assets failed certification
- which research assets are still pending
- which provider bundle produced each asset
- which certification score supported the final dataset decision
