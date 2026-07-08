# Phase 4.7A Research Asset Source Discovery And Connector Mapping

## Summary

Phase 4.7A documents the canonical discovery relationship between research assets, candidate providers, connector families, and certification readiness.
It is discovery-only.
No data was acquired and no connectors were activated.

## Sources Evaluated

This phase reused the existing canonical ownership layers already established in the repository:

- `src.data.data_source_registry`
- `src.data.historical_sources`
- `src.data.open_sports_history_sources`
- `src.data.source_quality_scoring`
- `src.providers`
- `src.connectors`
- `src.data.local_platform`
- `src.data.historical_research_database`
- `src.services.streamlit_dashboard_data`
- `docs/discovery/NFL_PROVIDER_INVENTORY.md`
- `docs/discovery/NFL_CAPABILITY_MATRIX.md`
- `docs/reports/NFL_PROVIDER_SOURCE_MATRIX.md`
- `docs/reports/NFL_PROVIDER_SOURCE_MAPPING.md`
- `docs/reports/NFL_RESEARCH_BLUEPRINT.md`
- `docs/reports/NFL_GAP_ANALYSIS.md`

## Sources Selected For The Minimum NFL Schema

The minimum certified NFL schema is still the right baseline for the first reproducible slice.

Selected as canonical source families for the minimum NFL path:

- `nflverse` for schedule, results, and core team/game history
- `nflfastr` as a verification / redundancy source
- `nflreadr` as a secondary verification / redundancy source
- `the_odds_api` for odds snapshots where API-key and terms review are acceptable
- `sportsgameodds` and `odds_api_io` as secondary odds candidates
- `open_meteo` for weather forecasts
- `national_weather_service` and `noaa_public_datasets` for weather verification and archival context
- computed rest / travel context from certified event and venue data

## Optional Enrichment Sources

The following lanes remain discovery facts and optional enrichment sources, not part of the minimum baseline:

- injury and availability lanes that require explicit timestamp discipline
- officials and assignment lanes
- coaching / staff continuity lanes
- depth chart lanes
- player statistics lanes
- paid or budget-gated odds / context lanes

These are useful future research assets, but they do not need to block the first certified minimum schema.

## Connector Mapping Summary

The repository should map assets to connector families, not invent a new acquisition stack:

- open datasets -> `src.connectors.feeds`
- odds snapshots -> `src.connectors.odds_data`
- market-context feeds -> `src.connectors.market_data`
- web-scraped lanes -> `src.connectors.web_scraping` only when terms allow
- manual imports -> local import / certification paths
- computed features -> no external connector

## Minimum NFL Source Map

| Research Asset ID | Candidate providers | Primary provider | Secondary providers | Connector family | Historical availability | Licensing / risk | Certification readiness | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dataset.nfl.games` | `nflverse`, `nflfastr`, `nflreadr`, `manual_schedule_import` | `nflverse` | `nflfastr`, `nflreadr` | `src.connectors.feeds` | High | Open dataset terms review required | Ready | P0 |
| `dataset.nfl.odds_snapshots` | `the_odds_api`, `sportsgameodds`, `odds_api_io`, `oddsmagnet`, `manual_export` | `the_odds_api` | `sportsgameodds`, `odds_api_io` | `src.connectors.odds_data` | Medium | Terms / API-key review required | Needs Source Approval | P0 |
| `dataset.nfl.weather_snapshots` | `open_meteo`, `national_weather_service`, `noaa_public_datasets`, `weatherapi`, `weatherstack` | `open_meteo` | `national_weather_service`, `noaa_public_datasets` | `src.connectors.market_data` | Medium to High | Public-data terms review required | Source Identified | P0 |
| `dataset.nfl.team_stats_snapshots` | `nflverse`, `nflfastr`, `nflreadr` | `nflverse` | `nflfastr`, `nflreadr` | `src.connectors.feeds` | High | Open dataset review required | Ready | P0 |
| `dataset.nfl.rest_travel` | computed from certified events and venue history | computed | `dataset.nfl.games` | `computed` | High once sources exist | No separate external license | Connector Ready | P0 |
| `dataset.nfl.injury_snapshots` | `official_team_reports`, `manual_import`, `official_team_press_releases`, `official_nfl_staff_or_news_pages` | none yet | `manual_import` | `manual_import` or `src.connectors.web_scraping` | Medium | Timing / provenance / terms review required | Needs Provider | Enrichment |
| `dataset.nfl.officials` | `official_gamebook_records`, `manual_import`, open assignment lanes | none yet | `manual_import` | `manual_import` or `src.connectors.feeds` | Medium | Assignment timing must be explicit | Needs Provider | Enrichment |
| `dataset.nfl.coaching` | `wikidata_coaching_seed`, `wikipedia_coaching_seed`, official team pages, open GitHub coaching datasets | `wikidata_coaching_seed` | `wikipedia_coaching_seed` | `src.connectors.feeds` / `manual_import` | Medium | Seed lanes are supplemental only | Verification Candidate | Enrichment |
| `dataset.nfl.depth_charts` | manual export, official team pages, open public terms-review lanes | none yet | `manual_import` | `manual_import` | Medium | Late changes can leak | Needs Provider | Enrichment |
| `dataset.nfl.player_stats` | `nflverse`, `nflfastr`, `nflreadr` | `nflverse` | `nflfastr`, `nflreadr` | `src.connectors.feeds` | High | Not needed for the minimum baseline slice | Deferred | Future |

## Engineering Improvements Implemented

- The discovery phase now names the canonical provider, connector, and source-quality owners explicitly.
- The minimum NFL schema is separated from optional enrichment sources.
- Source candidates are classified by historical availability, licensing, and point-in-time safety.
- The report now distinguishes connector families from provider families so future markets can reuse the same pattern.

## Engineering Improvements Deferred

- connector activation
- provider authentication
- data acquisition
- dataset certification execution
- ingestion jobs
- feature engineering
- mathematical engines
- backtesting

## Senior Systems Engineer Review

The phase is a good fit for the repository.

What is strong:

- it reuses the existing provider and connector owners rather than creating a new source stack
- it keeps canonical acquisition sources separate from optional enrichment sources
- it gives Phase 4.7B a credible source map instead of leaving acquisition as guesswork
- it remains reusable for MLB, prediction markets, and options / 0DTE

What to watch:

- odds snapshots still depend on API / terms / snapshot discipline
- injury, officials, and coaching lanes remain provenance-sensitive
- source discovery can sprawl if future markets create duplicate inventories instead of reusing this pattern

Overall recommendation:

- keep discovery and connector mapping narrow and source-driven
- reuse `src.data.data_source_registry` as the source discovery backbone
- reuse `src.providers` and `src.connectors` as the runtime boundaries
- do not introduce a second discovery registry unless a new market family proves the current contract is insufficient

## Worldview Intelligence Review

This phase improves future Worldview compatibility by making source availability, licensing posture, point-in-time safety, and certification readiness explicit.

Worldview can now ask:

- what research assets exist
- which providers can supply them
- which sources are canonical
- which sources are optional enrichment
- which sources are blocked or deferred
- which acquisition lane supports the next experiment

## Readiness For Phase 4.7B - Historical Dataset Acquisition Runtime

The repository is ready for Phase 4.7B - Historical Dataset Acquisition Runtime to begin from the discovered minimum-schema source map.
