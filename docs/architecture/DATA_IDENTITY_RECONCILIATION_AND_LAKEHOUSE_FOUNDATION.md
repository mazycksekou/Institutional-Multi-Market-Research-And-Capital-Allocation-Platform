# Data Identity, Reconciliation And Lakehouse Foundation

The Data Identity, Reconciliation and Lakehouse Foundation layer is the governed shared data-contract surface above the certified NFL production implementation.
It preserves the certified NFL chain as immutable reference behavior while adding deterministic identity, reconciliation, quarantine, revision, Parquet, and readiness capabilities that future controlled vendor ingest work can reuse.

## Canonical Ownership

- `src.data.data_identity_lakehouse` owns deterministic identity mapping, matching, reconciliation, quarantine, revision, and lakehouse publication behavior.
- `src.market_intelligence.data_identity_lakehouse_foundation` owns the governed audit, readiness snapshot, artifact persistence, and phase handoff state.
- `src.storage.local_store` owns the canonical SQLite and Parquet storage interfaces and the persisted manifest tables.
- `src.data.historical_dataset_acquisition_runtime` remains the raw acquisition owner.
- `src.data.historical_research_database` remains the certified normalized historical dataset owner.
- `src.data.historical_research_asset_certification_runtime` remains the research-asset certification owner.
- `src.data.research_asset_lifecycle_runtime` remains the lifecycle owner.
- `src.data.source_event_links` and `src.data.market_identity_resolver` remain the canonical event, market, and selection identity helpers.
- `src.data.validation` and `src.analytics.model_governance.data_lineage` remain the shared validation, lineage, and provenance owners.
- `src.services.streamlit_dashboard_data` owns the thin dashboard adapter for the phase snapshot.
- `src.data.nfl_p0_foundation` owns the P0 readiness rollup that now extends through the data identity foundation handoff.

## Inputs

The layer consumes only certified outputs and canonical repository state from:

- certified NFL research assets
- deterministic historical dataset population
- deterministic feature snapshot population
- deterministic mathematical engine population
- deterministic signal population
- deterministic decision row generation
- deterministic baseline backtesting
- deterministic pipeline validation
- deterministic Research Intelligence
- Universal Market Framework parity surfaces
- NFL Production Completion parity and production-readiness surfaces

The layer does not regenerate research assets, dataset rows, feature snapshots, math outputs, signals, decision rows, or backtest results.

## Responsibilities

The layer is responsible for:

- deterministic identity mapping and approval evidence
- deterministic matching with manual-review routing
- identity reconciliation separate from observation and value reconciliation
- point-in-time and revision-safe identity records
- quality-event, quarantine, and manual-review persistence
- Bronze, Silver, and Gold lifecycle mapping on top of the existing lifecycle owners
- deterministic Parquet publication and manifest persistence
- Delta-compatible metadata without requiring Delta or Spark
- dashboard-ready readiness surfaces
- query-ready capability-audit and lakehouse manifests
- sequencing handoff to the First Controlled NFL Vendor Ingest phase

## Persisted Surfaces

The runtime persists the canonical tables:

- `identity_mappings`
- `identity_match_candidates`
- `identity_reconciliation_results`
- `data_quality_events`
- `quarantine_records`
- `manual_review_queue`
- `mapping_approvals`
- `lakehouse_partitions`
- `data_identity_foundation_runs`
- `data_identity_foundation_audit_items`

The runtime also writes deterministic artifacts under `data_identity_foundation_artifacts`:

- `report.json`
- `summary.md`
- `dashboard.json`

## Deterministic Contracts

The identity contract preserves stable internal IDs for:

- market families
- sports and leagues
- teams
- players
- events
- venues
- canonical markets
- selections and outcomes
- providers
- vendor entities
- future companies, securities, and listings
- future prediction-market events and contracts

Each persisted mapping carries provider, external identifier, internal identifier, entity type, validity bounds, mapping status, match method, confidence, review state, revision metadata, and approval evidence.

The matching hierarchy is deterministic:

- `approved_existing_mapping`
- `stable_external_identifier`
- `exact_composite_identity`
- `normalized_exact_match`
- `controlled_fuzzy_match`
- `manual_review`

The point-in-time and revision contract standardizes:

- `event_time`
- `published_at`
- `observed_at`
- `processed_at`
- `valid_from`
- `valid_to`
- `revision_number`
- `is_latest`
- `source_published_at`
- `system_observed_at`

## Bronze, Silver, And Gold Mapping

The physical storage tiers map onto the existing lifecycle rather than replacing it:

- Bronze publishes immutable `raw_records` payload evidence and acquisition metadata.
- Silver publishes normalized `historical_events`, `historical_markets`, `historical_selections`, `identity_mappings`, and `identity_reconciliation_results`.
- Gold publishes certified `historical_dataset_rows` and `feature_snapshots`.

This mapping preserves the existing acquisition, certification, and lifecycle owners while making the analytical storage surface queryable and reproducible.

## Parquet And Delta Compatibility

`LocalStorageEngine` now exposes deterministic Parquet write and read interfaces with:

- schema-versioned manifests
- content digests
- file checksums
- row counts
- deterministic file identities
- idempotent writes
- reproducible roundtrips
- compaction-safe physical layouts

`lakehouse_partitions` manifests expose the metadata needed for later Delta adoption, including schema-evolution readiness, versioned-table readiness, correction and upsert readiness, and time-travel handoff metadata.
Spark remains deferred until measured scale requires distributed execution.

## Readiness And Boundaries

When the blocking audit requirements are complete and validated, the layer reports:

- lifecycle state: `data_identity_lakehouse_foundation_complete`
- readiness: `first_controlled_nfl_vendor_ingest_ready`

The layer preserves:

- deterministic execution
- point-in-time integrity
- lineage
- provenance
- certification
- reproducibility
- queryability

The layer does not:

- ingest the vendor dataset
- collapse sportsbook books into one arbitrary canonical line
- accept ambiguous low-confidence matches
- alter certified NFL outputs
- implement covariance or the risk engine
- implement another market
- implement paper trading
- implement live execution

## Dashboard And Query Views

The canonical dashboard surface exposes:

- summary cards
- capability audit matrix
- identity-resolution readiness
- reconciliation readiness
- quarantine and manual-review readiness
- Bronze, Silver, and Gold readiness
- Parquet readiness
- Delta compatibility status
- Spark deferral evidence
- first-vendor-ingest readiness

The canonical query interfaces expose:

- `list_identity_mappings`
- `list_reconciliation_results`
- `list_lakehouse_partitions`
- `inspect_capability_audit_matrix`
- `inspect_first_vendor_ingest_readiness`
