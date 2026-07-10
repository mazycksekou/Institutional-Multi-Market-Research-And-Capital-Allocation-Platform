# Phase 4.9F - NFL Weather Research Asset Population

## Summary

Phase 4.9F implements and certifies `dataset.nfl.weather_snapshots` through the existing local-first acquisition architecture.
It preserves the shared raw acquisition cache, the canonical normalization path, the research-asset certification runtime, the lifecycle runtime, the coverage planner, and the dashboard readiness owner.

## What Changed

- introduced `src.data.nfl_weather_research_asset_population`
- introduced focused weather population tests
- wired the NFL weather population path through the shared acquisition runtime
- preserved raw acquisition cache usage
- preserved field-level provenance
- preserved integrity validation
- preserved normalization into event-centric forecast rows
- preserved schedule/results/odds join validation
- preserved research asset certification
- preserved dataset certification
- preserved lifecycle advancement
- normalized the shared certification catalog to the repository's `_snapshots` weather and team-stat asset IDs

## Source And Provider Role

- provider id: `open_meteo`
- provider name: `Open-Meteo`
- provider role: `primary_acquisition`
- source access type: `open_public`
- execution mode: `deterministic_fixture`

## Field-Level Provenance

The weather population path preserves provenance for the minimum NFL weather fields:

- location
- forecast_time
- weather_condition
- temperature_f
- wind_mph
- wind_gust_mph
- precipitation_pct
- humidity_pct
- pressure_hpa
- indoor_flag
- forecast_freshness
- source_snapshot_time
- snapshot_time
- decision_time

Each field retains source mapping, acquisition timestamp, raw payload reference, lineage id, and quality metadata when available.
The derived `location` alias remains mapped back to `venue_name`, `venue_city`, and `venue_state`.

## Runtime Path

Provider / deterministic local forecast fixture
-> Shared Market-Data Connector Metadata
-> Raw Acquisition Cache
-> Integrity Validation
-> Normalization
-> Schedule + Results + Odds Join Validation
-> Research Asset Certification
-> Dataset Certification
-> Lifecycle Update
-> Historical Research Database
-> Coverage Planner
-> Dashboard / Readiness Snapshot

## Verified Minimum-Slice Behavior

The implemented path supports the minimum offline NFL weather slice used by the repository:

- raw acquisition cache is used
- integrity validation runs
- normalization produces event-centric forecast rows
- certification completes for the weather asset only when the schedule/results/odds backbone is certified
- post-decision or orphaned weather cannot certify
- lifecycle advancement is aligned to the shared runtime
- dashboard/readiness snapshots include the connector state
- the coverage planner advances its remaining minimum-schema gap to team statistics after weather is certified

## Query And Worldview Readiness

The weather asset preserves enough metadata for future research query and evidence packages:

- asset identity
- lineage
- certification state
- lifecycle state
- provider capability metadata
- field-level provenance

That keeps the weather asset queryable later for joins to schedule, results, odds, injuries, team statistics, and player statistics.

## Senior Systems Engineer Review

The weather phase reuses the canonical acquisition, certification, lifecycle, and coverage owners correctly instead of introducing a parallel weather-only pipeline.
The main architectural strength is that the asset remains local-first and deterministic while still carrying provider capability metadata, field-level provenance, and an explicit forecast-only evidence role.

The main risk is schema interpretation: the shared storage table preserves venue fields while the research-asset layer exposes a derived `location` alias.
That is acceptable for the minimum slice because lineage remains explicit and no duplicate storage owner was introduced.

Recommendation:

- Preferred: keep the current shared-runtime design and preserve weather as a forecast-only research asset.
- Acceptable: add more forecast horizons later if each remains point-in-time safe and locally certifiable.
- Not Recommended: mix observed postgame weather into the same certified evidence path.

## Worldview Intelligence Review

The weather asset materially improves future evidence packaging because it preserves asset identity, lineage, certification state, lifecycle state, provider capability metadata, field-level provenance, and a clear forecast-only evidence boundary.
That gives a future research-query layer enough structure to explain why a weather asset is ready or blocked and to return evidence packages that can be joined to schedule, results, odds, and future research assets.

Recommendation:

- Preferred: continue using the canonical metadata path so future Worldview queries can reason over certified evidence instead of live provider state.
- Acceptable: add a small query-surface note later if the research-query layer needs an explicit weather capability summary.
- Not Recommended: defer forecast-versus-observation discipline until a later phase.

## Validation

- compileall: passed
- focused weather runtime/docs tests: passed
- smoke: passed
- architecture: passed
- document lifecycle: passed
- ops workflow check: passed

## Readiness For Phase 4.9G

Phase 4.9G may begin with the NFL injuries research asset population using the same shared runtime pattern and the same report-time discipline.
The coverage planner still reports `dataset.nfl.team_stats_snapshots` as the remaining unresolved minimum-schema gap, but the roadmap and canonical next action advance to injuries as the next named phase.
