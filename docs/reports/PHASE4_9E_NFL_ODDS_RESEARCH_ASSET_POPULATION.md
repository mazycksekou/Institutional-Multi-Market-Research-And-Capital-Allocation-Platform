# Phase 4.9E - NFL Odds Research Asset Population

## Summary

Phase 4.9E implements and certifies `dataset.nfl.odds_snapshots` through the existing local-first acquisition architecture.
It preserves the shared raw acquisition cache, the canonical normalization path, the research-asset certification runtime, the lifecycle runtime, the coverage planner, and the dashboard readiness owner.

## What Changed

- introduced `src.connectors.odds_data.nfl`
- introduced `src.data.nfl_odds_research_asset_population`
- wired the NFL odds population path through the shared acquisition runtime
- preserved raw acquisition cache usage
- preserved field-level provenance
- preserved integrity validation
- preserved normalization into event-centric odds rows
- preserved schedule/results join validation
- preserved research asset certification
- preserved dataset certification
- preserved lifecycle advancement
- updated the coverage planner so the first remaining NFL minimum-schema target advances to weather after odds is certified

## Source And Provider Role

- provider id: `the_odds_api`
- provider name: `The Odds API`
- provider role: `primary_acquisition`
- source access type: `free_key`
- execution mode: `deterministic_fixture`

## Field-Level Provenance

The odds connector preserves provenance for the minimum NFL odds fields:

- season
- week
- game_id
- event_id
- league
- home_team
- away_team
- kickoff_time
- book
- market
- selection
- line_value
- american_odds
- decimal_odds
- implied_probability
- market_label
- freshness_score
- source_snapshot_time
- snapshot_time
- decision_time

Each field retains source mapping, acquisition timestamp, raw payload reference, lineage id, and quality metadata when available.

## Runtime Path

Provider / deterministic local fixture
-> Connector
-> Raw Acquisition Cache
-> Integrity Validation
-> Normalization
-> Schedule + Results Join Validation
-> Research Asset Certification
-> Dataset Certification
-> Lifecycle Update
-> Historical Research Database
-> Coverage Planner
-> Dashboard / Readiness Snapshot

## Verified Minimum-Slice Behavior

The implemented path supports the minimum offline NFL odds slice used by the repository:

- raw acquisition cache is used
- integrity validation runs
- normalization produces event-centric odds rows
- certification completes for the odds asset only when the schedule/results backbone is certified
- lifecycle advancement is aligned to the shared runtime
- dashboard/readiness snapshots include the connector state
- the coverage planner advances to weather as the next unresolved minimum-schema asset

## Query And Worldview Readiness

The connector and asset preserve enough metadata for future research query and evidence packages:

- asset identity
- lineage
- certification state
- lifecycle state
- provider capability metadata
- field-level provenance

That keeps the odds asset queryable later for joins to schedule, results, weather, injuries, team statistics, and player statistics.

## Senior Systems Engineer Review

The odds phase reuses the canonical acquisition, certification, lifecycle, and coverage owners correctly instead of introducing a parallel odds-only pipeline.
The main architectural strength is that the asset remains local-first and deterministic while still carrying provider capability metadata and field-level provenance.

The main risk is the multi-row odds asset shape: the lifecycle layer is intentionally row-stable, so this phase should remain disciplined about using one canonical lifecycle identity while the shared storage layer keeps the additional normalized market rows.

Recommendation:

- Preferred: keep the current shared-runtime design and preserve the odds asset as a deterministic connector-backed population phase.
- Acceptable: split future market-specific odds expansions into separate certified research assets if row-level lifecycle identity becomes too expensive.
- Not Recommended: create a second odds-specific storage or certification stack.

## Worldview Intelligence Review

The odds asset materially improves future evidence packaging because it preserves asset identity, lineage, certification state, lifecycle state, provider capability metadata, and field-level provenance.
That gives a future research-query layer enough structure to explain why an odds asset is ready or blocked and to return evidence packages that can be joined to schedule, results, weather, and future research assets.

Recommendation:

- Preferred: continue using the canonical metadata path so future Worldview queries can reason over certified evidence instead of live provider state.
- Acceptable: add a small query-surface note later if the research-query layer needs an explicit odds capability summary.
- Not Recommended: defer provenance or lineage capture until a later phase.

## Validation

- compileall: passed
- focused connector/runtime/docs tests: passed
- smoke: passed
- architecture: passed
- document lifecycle: passed
- ops workflow check: passed, and the final end-task preflight passed after commit and push

## Readiness For Phase 4.9F

Phase 4.9F may begin with the NFL weather research asset population using the same shared runtime pattern and the same decision-time discipline.
