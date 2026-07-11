# Research Asset Source Discovery And Connector Mapping

This document defines the canonical discovery framework for research assets, their candidate acquisition sources, and the connector families that can reach them.
It is discovery-only. It does not activate providers, download datasets, or implement connector code.

## Purpose

The framework answers one question: how does the repository discover what research assets exist, which providers can supply them, which connector family should reach them, and which sources are canonical versus optional enrichment?

It keeps the following responsibilities on one canonical path:

- research asset discovery
- source family classification
- provider candidate mapping
- connector family mapping
- coverage and historical availability tracking
- cost and licensing tracking
- point-in-time safety classification
- acquisition priority
- certification readiness

## Canonical Ownership

This discovery framework reuses the existing canonical owners instead of introducing a parallel source-discovery stack:

- `src.data.data_source_registry` owns the broad source registry, source scoring, and source catalog synthesis.
- `src.providers` owns provider contracts, provider classification, provider registry state, and provider readiness.
- `src.connectors` owns connector contracts, connector registry state, and read-only connector boundaries.
- `src.data.historical_sources` owns historical import source planning.
- `src.data.open_sports_history_sources` owns open sports history lane discovery.
- `src.data.source_quality_scoring` owns source and lane quality scoring.
- `src.data.local_platform` owns dataset registry, versioning, lineage, and local certified dataset ownership.
- `src.data.historical_research_database` owns event-centric historical certification and readiness.
- `src.services.streamlit_dashboard_data` owns dashboard-ready readiness summaries.

The framework does not replace those owners.
It connects them.

## Discovery Lifecycle

Every research asset should progress through the same discovery sequence:

Research Asset -> Supported Providers -> Connector Type -> Coverage -> Historical Availability -> Cost -> Licensing -> Point-in-Time Safety -> Acquisition Priority -> Certification Readiness

## Source Classification Legend

- `OPEN_DATA` - open historical dataset or open public release
- `OPEN_PUBLIC` - openly published endpoint or public web surface
- `FREE_API` - API-backed source with no paid gate discovered
- `FREE_KEY` / `FREE_TIER` - key-based or limited free tier source
- `LOCAL_CSV` / `LOCAL_JSON` / `LOCAL_PARQUET` / `SQLITE` / `DUCKDB` - repository-local data or materialized artifacts
- `MANUAL_IMPORT` - human-curated import lane
- `COMPUTED` - derived from already certified repository-owned inputs
- `PAID_OR_DEFERRED` - gated, paid, or intentionally deferred until proven necessary
- `UNKNOWN` - not yet proven in discovery

## Connector Mapping Legend

Connector families are mapped conceptually, not activated here:

- `src.connectors.feeds` - read-only feed or open-dataset style adapter boundary
- `src.connectors.market_data` - read-only market-context adapter boundary
- `src.connectors.odds_data` - read-only odds adapter boundary
- `src.connectors.web_scraping` - read-only web intake boundary, only if terms allow
- `manual_import` / `local_file_loader` - repository-local import path, not a live connector
- `computed` - no external connector; derived from certified repository-owned inputs

If a source family does not map cleanly to an approved connector boundary, the source stays discovery-only.

## Minimum NFL Source Map

The first certified NFL slice should start with the smallest reusable dataset that can support spread, moneyline, and totals research.

| Research Asset ID | Market Profile | Market Family | Description | Minimum Schema Support | Advanced Schema Support | Candidate Providers | Primary Provider | Secondary Providers | Open Source Availability | Commercial Availability | Historical Coverage | Update Frequency | Estimated Reliability | Known Limitations | Licensing Notes | Point-in-Time Safety | Recommended Connector | Future Runtime Owner | Certification Readiness | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dataset.nfl.games` | `sports:nfl` | Sports | Game identity, schedule, kickoff, venue, and settled result backbone. | Yes | Yes | `nflverse`, `nflfastr`, `nflreadr`, `manual_schedule_import` | `nflverse` | `nflfastr`, `nflreadr` | Yes | No | High | Daily / historical | High | Schedule/result joins must stay stable and event-centric. | Open dataset terms review still required. | High when frozen by `game_id` and kickoff cutoff | `src.connectors.feeds` | `src.data` / `src.data.local_platform` | Ready | P0 |
| `dataset.nfl.odds_snapshots` | `sports:nfl` | Sports | Pregame odds snapshots for spread, moneyline, and totals. | Yes | Yes | `the_odds_api`, `sportsgameodds`, `odds_api_io`, `oddsmagnet`, `manual_export` | `the_odds_api` | `sportsgameodds`, `odds_api_io` | Limited | Yes | Medium | Near-live / historical snapshots | Medium | Requires snapshot discipline; closing lines cannot leak into pregame features. | Terms and API-key review required. | High only when frozen at decision time | `src.connectors.odds_data` | `src.data` / `src.backtesting` | Ready | P0 |
| `dataset.nfl.weather_snapshots` | `sports:nfl` | Sports | Forecast weather at the decision point. | Yes | Yes | `open_meteo`, `national_weather_service`, `noaa_public_datasets`, `weatherapi`, `weatherstack` | `open_meteo` | `national_weather_service`, `noaa_public_datasets` | Yes | Yes | Medium to High | Near-live / historical | High | Must preserve forecast timestamp versus actual condition time. | Public-data terms review required. | High when forecast timestamp is frozen | `src.connectors.market_data` | `src.data` / `src.market_intelligence` | Source Identified | P0 |
| `dataset.nfl.team_stats_snapshots` | `sports:nfl` | Sports | Prior-game team statistics and efficiency context. | Yes | Yes | `nflverse`, `nflfastr`, `nflreadr` | `nflverse` | `nflfastr`, `nflreadr` | Yes | No | High | Daily / historical | High | Must be cut off before the decision time. | Open dataset review required. | High when frozen before kickoff | `src.connectors.feeds` | `src.data` / `src.market_intelligence` | Ready | P0 |
| `dataset.nfl.rest_travel` | `sports:nfl` | Sports | Rest, travel, and schedule fatigue context derived from certified events. | Yes | Yes | `COMPUTED` from `dataset.nfl.games`, venue history, and team location data | Computed | `dataset.nfl.games` as supporting input | N/A | N/A | High once source data exists | Computed on demand | High | Depends on event and venue lineage being complete. | No separate source license once derived from certified inputs. | High if derived only from pregame data | `computed` | `src.market_intelligence` | Connector Ready | P0 |
| `dataset.nfl.injury_snapshots` | `sports:nfl` | Sports | Injury and availability context. | Optional | Yes | `nflverse_injuries`, `manual_import`, `official_team_reports`, `official_team_press_releases`, `official_nfl_staff_or_news_pages` | `nflverse_injuries` | `manual_import`, `official_team_reports`, `official_team_press_releases` | Yes | Possible | Medium to High | Daily / historical | Medium to High | Timing and provenance are the main leakage risks. | Open-dataset path plus manual evidence review required. | High when report timestamps are preserved | `src.data.nfl_injuries_research_asset_population` | `src.data` / `src.market_intelligence` | Source Identified | Enrichment |
| `dataset.nfl.officials` | `sports:nfl` | Sports | Official crew identity and assignment context. | Optional | Yes | `official_gamebook_records`, `manual_import`, `open_public_assignment_lanes` | None yet | `manual_import` | Partial | Possible | Medium | Event-driven | Medium | Assignment timing must be preserved. | Terms review required. | Medium only when assignment time is explicit | `src.connectors.feeds` or `manual_import` | `src.data` / `src.market_intelligence` | Needs Provider | Enrichment |
| `dataset.nfl.coaching` | `sports:nfl` | Sports | Coaching staff identity and continuity context. | Optional | Yes | `wikidata_coaching_seed`, `wikipedia_coaching_seed`, `official_team_staff_pages`, `official_team_press_releases`, `open_github_nfl_coaches_dataset` | `wikidata_coaching_seed` | `wikipedia_coaching_seed` | Yes | No | Medium | Seasonal / event-driven | Medium | Provenance quality varies by lane. | Seed lanes are supplemental only. | High when season-timestamped | `src.connectors.feeds` / `manual_import` | `src.market_intelligence` | Verification Candidate | Enrichment |
| `dataset.nfl.depth_charts` | `sports:nfl` | Sports | Depth chart and starter status context. | Optional | Yes | `manual_export`, `official_team_pages`, `open_public_terms_review_lanes` | None yet | `manual_export` | Partial | Possible | Medium | Event-driven | Medium | Late changes can leak if not frozen by decision time. | Terms review required. | Medium only when timestamped before cutoff | `manual_import` | `src.data` / `src.market_intelligence` | Needs Provider | Enrichment |
| `dataset.nfl.player_stats` | `sports:nfl` | Sports | Player statistics and usage context. | No | Yes | `nflverse`, `nflfastr`, `nflreadr` | `nflverse` | `nflfastr`, `nflreadr` | Yes | No | High | Historical | High | Not needed for the minimum baseline slice. | Open dataset review required. | High when history is frozen | `src.connectors.feeds` | `src.market_intelligence` | Deferred | Future |

## Connector Mapping Summary

| Source category | Recommended connector family | Canonical owner | Notes |
| --- | --- | --- | --- |
| `OPEN_DATA` | `src.connectors.feeds` | `src.providers` and `src.connectors` | Best fit for open historical releases and local mirrored datasets. |
| `OPEN_PUBLIC` | `src.connectors.market_data` or `src.connectors.web_scraping` | `src.providers` and `src.connectors` | Use only when terms and robots constraints are clear. |
| `FREE_API` / `FREE_KEY` / `FREE_TIER` | `src.connectors.market_data` / `src.connectors.odds_data` | `src.providers` and `src.connectors` | Useful for source discovery, but still subject to snapshot timing and license review. |
| `LOCAL_*` | `local_file_loader` | `src.data.local_platform` | Repository-owned certified artifacts, not live providers. |
| `MANUAL_IMPORT` | `manual_import` | `src.data.local_platform` | Acceptable only where automation is blocked or provenance requires human review. |
| `COMPUTED` | `computed` | `src.market_intelligence` and `src.core` | Derived from certified inputs; no external connector. |
| `PAID_OR_DEFERRED` | none until approved | `src.providers` | Discovery-only until the repository proves the lane is necessary and safe. |

## Multi-Provider Strategy

One certified dataset may combine many acquisition sources.
The repository does **not** assume one provider owns the truth.

Source selection should be documented as:

- primary acquisition source
- secondary verification source
- fallback source
- enrichment source

The certified dataset remains repository-owned after certification.

## Certification Readiness Rules

A research asset is not certification-ready until the repository can answer:

- where the data came from
- what connector family would reach it
- whether the source is point-in-time safe
- whether the source is licensed or terms-safe
- whether the source is open, free, manual, computed, or deferred
- whether the source can support the minimum certified schema

## Reuse Expectations

This framework is reusable for:

- NFL
- MLB
- NBA
- prediction markets
- options / 0DTE

The reuse contract is:

research asset -> supported providers -> connector type -> coverage -> historical availability -> cost -> licensing -> point-in-time safety -> acquisition priority -> certification readiness

## Phase Boundary

Phase 4.7A defines research asset source discovery and connector mapping.
Phase 4.7B builds the reusable historical dataset acquisition runtime using the discovered source map.
Phase 4.7C completes the historical research asset certification runtime and gates dataset certification on the required research assets.
Phase 4.8 implements the research asset lifecycle runtime and time/entity alignment certification.
Phase 4.9A populates the NFL schedule research asset.
Phase 4.9B builds the research asset coverage planner and provider selection framework.
Phase 5.0 materializes the historical dataset population layer from certified historical research assets.
Phase 5.1 populates reusable features from the certified historical dataset layer and certified event context.

## Out Of Scope

This framework does not:

- activate providers
- download datasets
- ingest data
- implement connectors
- authenticate with providers
- perform ETL
- calculate features
- implement mathematical formulas
- build backtests
- build models

It only defines the reusable discovery relationship that future runtime owners must honor.
