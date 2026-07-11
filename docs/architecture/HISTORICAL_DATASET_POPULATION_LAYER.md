# Historical Dataset Population Layer

This document owns the first deterministic historical dataset layer that sits between certified research assets and future feature population.
It reuses the existing local-first storage, lineage, certification, lifecycle, coverage, and dashboard owners instead of introducing an NFL-only dataset framework.

## Purpose

The historical dataset population layer combines certified minimum-schema NFL evidence into one reproducible dataset batch that is ready for feature population.
The canonical dataset identifier is `dataset.sports.nfl.historical_dataset`.

Phase 5.0 owns:

- canonical dataset grain
- deterministic dataset-batch identity
- game-level decision cutoff policy
- point-in-time-safe source selection
- join cardinality validation
- dataset-row persistence
- immutable lineage
- evidence-package generation
- dataset certification
- readiness reporting

Phase 5.0 does not own feature engineering, mathematical engines, signals, decision rows, or backtesting.

## Canonical Ownership

- `src/data/historical_research_database.py` owns dataset population, point-in-time selection, diagnostics, evidence packaging, and certification handoff.
- `src/storage/local_store.py` owns `historical_dataset_batches`, `historical_dataset_rows`, and the persisted lineage edge storage used by dataset rows.
- `src/data/local_platform.py` owns reusable dataset registry, dataset versioning, and dataset-level readiness contracts.
- `src/data/historical_research_asset_certification_runtime.py` owns the asset-level certification preconditions that source batches must satisfy before dataset population can proceed.
- `src/data/nfl_p0_foundation.py` owns the NFL P0 readiness rollup that reports whether the certified source assets and the populated dataset layer are ready for later feature work.
- `src/market_intelligence/research_asset_coverage_planner.py` owns coverage-gap visibility, deferred enrichment tracking, and optional embedding of the historical dataset readiness snapshot.
- `src/services/streamlit_dashboard_data.py` owns the dashboard-facing adapter that reconstructs dataset readiness from persisted state.

## Dataset Grain And Identity

The canonical historical dataset grain reuses the minimum backtest row contract and stays anchored to one NFL event plus one market decision context per row.

For the current NFL minimum slice, each dataset row carries:

- dataset batch identity
- dataset row identity
- event identity
- season and week identity
- home and away team identity
- market type and selection context
- scheduled kickoff time
- decision cutoff time
- cutoff policy version
- selected source record identities
- source certification identities
- lineage identities
- predictor evidence fields
- realized label fields

Stable dataset row identities are derived from the deterministic game and market decision context.
Stable batch identities are derived from the dataset contract version, source asset batches, source certifications, cutoff policy, join policy, and event scope.
Identical reruns against identical certified inputs must reuse the same batch and row identities.

## Game-Level Decision Cutoff Policy

The dataset layer uses one canonical game-scoped cutoff:

`decision_cutoff = scheduled_kickoff_time - 5 minutes`

The cutoff is derived only from the scheduled kickoff.
It is never derived from:

- the selected odds snapshot
- the selected weather row
- the selected injury row
- the selected team-stat row
- the latest timestamp across assets
- or whichever asset updated most recently

The persisted row contract includes:

- `scheduled_kickoff_time`
- `decision_cutoff_time`
- `cutoff_policy_version`
- selected per-asset timestamps
- per-asset freshness at cutoff
- selected source record ids
- certification ids
- lineage ids
- missing required asset markers
- decision readiness status

## Source Eligibility And Selection

Only certified source evidence from the canonical minimum-schema assets is eligible:

- `dataset.sports.nfl.schedule`
- `dataset.sports.nfl.results`
- `dataset.nfl.odds_snapshots`
- `dataset.nfl.weather_snapshots`
- `dataset.nfl.injury_snapshots`
- `dataset.nfl.team_stats_snapshots`

Every predictor asset selects its latest eligible certified row independently at or before the shared game cutoff.
Asset observation times may differ and do not need to match one another.

### Schedule

Schedule rows define the canonical event identity, kickoff, venue, season, week, and home/away orientation.

### Results

Results remain label-only evidence.
They may occur after kickoff and after settlement, but they do not influence predictor selection, cutoff identity, or dataset readiness.

### Odds

The layer selects the latest eligible odds row for each supported market context at or before the cutoff and preserves:

- provider
- market
- sportsbook or venue where available
- snapshot time
- decision cutoff
- price or line
- source row identity
- certification identity
- lineage

### Weather

Weather selection preserves the distinction between forecast evidence and realized postgame observations.
Only the latest eligible predecision weather row may become predictor evidence.
Realized weather never becomes predecision forecast evidence.

### Injuries

Injuries select the latest eligible predecision report state at or before the cutoff without using later revisions.
Multiple contributing injury rows remain controlled child evidence rather than multiplying the canonical game row.

### Team Statistics

Team-statistics selection accepts only prior-game or predecision aggregates that exclude the target event.
Same-event live statistics, same-event final statistics, and rolling windows that include the target event are rejected.

Missing records do not move the cutoff.

## Cardinality Contract

The dataset layer declares expected join relationships before population:

- schedule to results: one-to-one label join
- schedule to odds: one-to-many controlled by market context
- schedule to weather: one selected eligible weather row per event
- event/team to injuries: one-to-many controlled contributing rows
- event/team to team statistics: one selected eligible row per team side

Population fails when observed joins exceed the declared contract and would create uncontrolled many-to-many expansion.
Late or otherwise ineligible evidence is recorded as rejected diagnostics rather than silently deduplicated into the predictor set.

## Persistence, Lineage, And Evidence Packages

The persisted dataset layer remains queryable through relational fields rather than opaque blobs.
The canonical storage retains:

- dataset batch rows
- dataset rows
- source certification references
- selected source row references
- selected timestamps
- freshness at cutoff
- unresolved missingness
- readiness state
- lineage edges
- evidence-package identity

Lineage must answer:

- which schedule row defined the event
- which result row supplied the realized label
- which odds row was selected
- which weather row was selected
- which injury rows contributed
- which home and away team-stat rows contributed
- which source certifications authorized those rows
- which cutoff and selection policy produced the final dataset row

## Coverage Planner And Dashboard Integration

The coverage planner distinguishes between the completed minimum-schema asset gap and the dataset-layer readiness state.
Optional enrichment assets remain visible but non-blocking.

Coverage planner embedding uses two distinct states:

- `not_embedded` when the planner snapshot was intentionally omitted
- `coverage_planner_snapshot_failed` when embedding was requested but the snapshot could not be built

The shared dashboard adapter reconstructs dataset readiness from persisted state and exposes:

- dataset identifier
- batch identity
- source asset counts
- eligible and rejected evidence counts
- final dataset row count
- join and cardinality validation status
- point-in-time validation status
- provenance completeness
- lineage completeness
- dataset certification state
- dataset readiness state
- unresolved blockers
- evidence-package identity

## Certification And Readiness

Dataset certification requires:

- certified source assets
- sufficient lifecycle states
- successful dataset population
- passed point-in-time validation
- passed join-integrity validation
- passed cardinality validation
- complete provenance
- complete lineage
- stable deterministic identities
- successful local persistence
- valid evidence-package content
- idempotent rerun behavior

The completed Phase 5.0 layer is ready for feature population.
It does not imply that features, mathematical engines, signals, decision rows, or backtests already exist.

## Query And Worldview Readiness

The historical dataset layer preserves enough structure for future deterministic query and evidence packaging:

- dataset discovery
- batch discovery
- event and team lookup
- season and week filtering
- selected snapshot inspection
- realized label inspection
- source lineage lookup
- source provenance lookup
- source certification visibility
- cutoff eligibility inspection
- rejected evidence inspection
- join diagnostics
- dataset certification visibility
- readiness inspection
- evidence-package retrieval

That gives the future Research Query Engine and Worldview layer a stable evidence substrate without allowing either layer to invent or bypass certified history.

## Phase Boundary

Phase 5.0 completes the historical dataset population layer from certified research assets.
Phase 5.1 reuses this layer to populate reusable features from certified dataset rows and certified event context.
