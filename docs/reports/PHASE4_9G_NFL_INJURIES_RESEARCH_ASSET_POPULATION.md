# Phase 4.9G - NFL Injuries Research Asset Population

## Summary

Phase 4.9G implements and certifies `dataset.nfl.injury_snapshots` through the existing local-first acquisition architecture.
It preserves the shared raw acquisition cache, the canonical normalization path, the research-asset certification runtime, the lifecycle runtime, the coverage planner, and the dashboard readiness owner.

## What Changed

- introduced `src.data.nfl_injuries_research_asset_population`
- introduced the canonical `nfl_injury_snapshots` table contract and local storage owner
- introduced focused injuries population runtime and documentation tests
- wired the NFL injuries population path through the shared acquisition runtime
- preserved raw acquisition cache usage
- preserved field-level provenance
- preserved integrity validation
- preserved normalization into event-centric injury snapshot rows
- preserved schedule/results/odds/weather join validation
- preserved research asset certification
- preserved dataset certification
- preserved lifecycle advancement
- preserved explicit separation between forecast weather and realized weather by joining only to the certified forecast-weather asset
- normalized the shared certification catalog and coverage planner to the repository's `_snapshots` injury asset id

## Source And Provider Role

- provider id: `nflverse_injuries`
- provider name: `nflverse injuries`
- provider role: `primary_acquisition`
- source access type: `open_dataset`
- execution mode: `deterministic_fixture`
- verification providers: `official_team_reports`, `official_team_press_releases`
- fallback providers: `manual_import`, `official_nfl_staff_or_news_pages`

## Field-Level Provenance

The injuries population path preserves provenance for the minimum NFL injury fields:

- report_status
- availability_status
- practice_status
- report_primary_injury
- injury_category
- report_time
- report_source
- timing_confidence
- source_snapshot_time
- snapshot_time
- decision_time

Each field retains source mapping, acquisition timestamp, raw payload reference, lineage id, and quality metadata when available.
Manual evidence support remains explicit in the provider metadata and does not bypass the raw cache or local certification path.

## Runtime Path

Provider / deterministic local injury fixture or approved manual evidence
-> Shared Injuries Connector Metadata
-> Raw Acquisition Cache
-> Integrity Validation
-> Normalization
-> Schedule + Results + Odds + Weather Join Validation
-> Research Asset Certification
-> Dataset Certification
-> Lifecycle Update
-> Historical Research Database
-> Coverage Planner
-> Dashboard / Readiness Snapshot

## Verified Minimum-Slice Behavior

The implemented path supports the minimum offline NFL injuries slice used by the repository:

- raw acquisition cache is used
- integrity validation runs
- normalization produces event-centric injury snapshot rows
- certification completes for the injuries asset only when the schedule/results/odds/weather backbone is certified
- post-decision or orphaned injuries cannot certify
- lifecycle advancement is aligned to the shared runtime
- dashboard/readiness snapshots include the connector state and manual-evidence support
- the coverage planner advances its remaining minimum-schema gap to team statistics after injuries are certified
- forecast weather and realized weather remain separated because injuries reuse only the certified forecast-weather backbone

## Query And Worldview Readiness

The injuries asset preserves enough metadata for future research query and evidence packages:

- asset identity
- lineage
- certification state
- lifecycle state
- provider capability metadata
- field-level provenance
- explicit report-time timestamps

That keeps the injuries asset queryable later for joins to schedule, results, odds, weather, team statistics, player statistics, and betting splits.

## Senior Systems Engineer Review

The injuries phase reuses the canonical acquisition, certification, lifecycle, and coverage owners correctly instead of introducing a parallel injuries-only pipeline.
The main architectural strength is that the asset remains local-first and deterministic while still carrying provider capability metadata, field-level provenance, an explicit manual-evidence fallback, and a strict report-time boundary.

The main risk is identity granularity.
The lifecycle layer still tracks the certified injuries asset through a representative injury identity while the row-level alignment evidence is preserved separately per injury snapshot.
That compromise is acceptable for the minimum slice because the shared runtime stays authoritative, the per-row alignment evidence remains queryable, and no duplicate lifecycle owner was introduced.

Recommendation:

- Preferred: keep the current shared-runtime design and preserve injuries as report-time evidence only.
- Acceptable: add richer revision handling later if each update remains point-in-time safe and locally certifiable.
- Not Recommended: mix postgame availability changes or realized-weather context into the same certified pregame evidence path.

## Worldview Intelligence Review

The injuries asset materially improves future evidence packaging because it preserves asset identity, lineage, certification state, lifecycle state, provider capability metadata, field-level provenance, and a clear report-time evidence boundary.
That gives a future research-query layer enough structure to explain why an injury asset is ready or blocked and to return evidence packages that can be joined to schedule, results, odds, weather, and future research assets.

Recommendation:

- Preferred: continue using the canonical metadata path so future Worldview queries can reason over certified evidence instead of live provider state.
- Acceptable: add a small query-surface note later if the research-query layer needs an explicit injuries capability summary.
- Not Recommended: defer report-time discipline until a later phase.

## Validation

- compileall: passed
- focused injuries runtime tests: passed
- focused injuries documentation tests: passed
- smoke: passed
- root markdown: passed
- OpenAPI contract: passed
- architecture: passed
- audit lifecycle: passed
- document lifecycle: advisory, `working_documents_needing_attention:6`, no clear violations
- ops workflow check: passed with the expected pre-commit dirty-worktree note before final git synchronization
- full repository test gate: passed

## Readiness For Phase 4.9H

Phase 4.9H may begin with the NFL team statistics research asset population using the same shared runtime pattern and the same point-in-time discipline.
The coverage planner still reports `dataset.nfl.team_stats_snapshots` as the remaining unresolved minimum-schema gap, and the canonical next action advances to team statistics.
