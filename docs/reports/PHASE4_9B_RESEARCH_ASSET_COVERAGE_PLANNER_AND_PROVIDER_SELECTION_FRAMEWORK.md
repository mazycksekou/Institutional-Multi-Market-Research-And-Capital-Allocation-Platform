# Phase 4.9B - Research Asset Coverage Planner And Provider Selection Framework

## Summary

Phase 4.9B adds the read-only planning layer that decides what research assets are still missing, which provider candidates can close those gaps, and what acquisition targets should come next.

The phase does not download data and does not implement connectors.

## Implemented Runtime

- `src/market_intelligence/research_asset_coverage_planner.py`

## What The Planner Does

- builds a research asset coverage registry
- builds a provider coverage registry
- scores provider candidates across coverage, depth, reliability, licensing, cost, and reproducibility
- builds a coverage gap engine
- emits acquisition plans
- exposes a dashboard snapshot
- exposes a future Worldview / Research Query surface

## Key Coverage Result

The planner now identifies the first remaining NFL connector-upgrade target as:

- `dataset.nfl.results`

The NFL schedule asset is already serviced by the first production connector path, so it is no longer the active coverage gap. The planner advances to the next missing asset while keeping the schedule connector pattern reusable for future markets.

First production connector target:

- `dataset.nfl.results`

## Provider Selection Result

The planner ranks the source families that can close the minimum-schema gap:

- schedule / games: `nflverse`, `nflreadr`, `nflfastr`, `manual_schedule_import`
- results / outcomes: `nflverse`, `nflreadr`, `nflfastr`, `official_gamebook_import`
- odds: `the_odds_api`, `sportsgameodds`, `odds_api_io`, `oddsmagnet`
- weather: `open_meteo`, `national_weather_service`, `noaa_public_datasets`, `weatherapi`, `weatherstack`
- injuries: `nflverse_injuries`, official team reporting lanes
- coaching: `wikidata_coaching_seed`, `wikipedia_coaching_seed`, `open_github_nfl_coaches_dataset`, official team/news lanes
- officials: official gamebook and manual import lanes

## Acquisition Planning

The output remains planning-only.
It explains which assets are certified, which are partially complete, and which provider combinations best close the remaining gaps.

## Worldview Readiness

The phase preserves the metadata needed for future query and evidence packages:

- certification status
- lifecycle state
- readiness state
- missing components
- quality score
- provider provenance
- connector recommendation

## Next Phase

Phase 4.9C completed the first production connector for the NFL schedule asset. Phase 4.9D should now populate the NFL results asset using the same canonical runtime path.
