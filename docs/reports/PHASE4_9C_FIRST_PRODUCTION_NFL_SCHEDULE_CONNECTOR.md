# Phase 4.9C - First Production NFL Schedule Connector

## Summary

Phase 4.9C implements the first production connector path for the canonical NFL schedule research asset, `dataset.sports.nfl.schedule`.
The connector is deterministic/offline-capable for validation, but it is structured as the reusable production path that future provider-backed acquisition can extend.

## What Changed

- introduced `src.connectors.feeds.nfl_schedule`
- wired the NFL schedule population path through the shared acquisition runtime
- preserved raw acquisition cache usage
- preserved field-level provenance
- preserved integrity validation
- preserved normalization into event-centric schedule rows
- preserved research asset certification
- preserved dataset certification
- preserved lifecycle advancement
- updated the coverage planner so the first remaining target advances to the next missing asset after the schedule connector is in place

## Source And Provider Role

- provider id: `nflverse`
- provider name: `nflverse schedules/results`
- provider role: `primary_acquisition`
- source access type: `open_github_release`
- execution mode: `deterministic_fixture`

## Field-Level Provenance

The connector preserves provenance for the minimum NFL schedule fields:

- season
- week
- game_id
- event_id
- league
- home_team
- away_team
- event_start_time
- venue
- timezone
- neutral_site
- game_status

Each field retains source mapping, acquisition timestamp, raw payload reference, lineage id, and quality metadata when available.

## Runtime Path

Provider / local fixture
-> Connector
-> Raw Acquisition Cache
-> Integrity Validation
-> Normalization
-> Research Asset Certification
-> Dataset Certification
-> Lifecycle Update
-> Historical Research Database
-> Coverage Planner
-> Dashboard / Readiness Snapshot

## Verified Minimum-Slice Behavior

The implemented path supports the minimum offline NFL schedule slice used by the repository:

- raw acquisition cache is used
- integrity validation runs
- normalization produces event-centric schedule rows
- certification completes for the schedule asset
- lifecycle advancement is aligned to the shared runtime
- dashboard/readiness snapshots include the connector state

## Query And Worldview Readiness

The connector preserves enough metadata for future research query and evidence packages:

- asset identity
- lineage
- certification state
- lifecycle state
- provider capability metadata
- field-level provenance

That keeps the schedule asset queryable later for joins to results, odds, weather, injuries, and team statistics.

## Validation

- compileall: passed
- focused connector/runtime/docs tests: passed
- smoke: passed
- architecture: passed
- document lifecycle: passed
- ops workflow check: passed, and the final end-task preflight passed after commit and push

## Next Phase

Phase 4.9D now focuses on the NFL results research asset population using the same shared runtime pattern.
