# NFL Provider Inventory

This inventory records the provider and source lanes discovered for NFL / football capability.
It classifies sources as discovery facts, not approvals to activate them.

Legend:

- `FREE` = free source with no paid gate discovered
- `OPEN` = openly published dataset or open web source
- `LOCAL` = local validated artifact or local fixture
- `CSV` / `JSON` / `SQLITE` / `DUCKDB` = local file or storage form
- `API` = API-backed provider or candidate
- `COMMERCIAL` = paid or budget-gated
- `PLACEHOLDER` = intentionally blocked, disabled, or not yet approved
- `UNKNOWN` = not proven in discovery

| Provider / source | Type | Coverage | Quality / status | Canonical owner | Notes |
|---|---|---|---|---|---|
| `nflverse` | OPEN | schedules, play-by-play, team stats, research lanes | strong discovery lane | `src.data.nfl_open_data_sources` / `src.providers.nfl_open_data_adapters` | Core free/open NFL data family. |
| `nflfastr` | OPEN | play-by-play / release-backed lane | strong but redundant with nflverse lanes | same as above | Source exhaustion flagged it as redundant. |
| `nflreadr` | OPEN | research / release-backed lane | strong but redundant with nflverse lanes | same as above | Source exhaustion flagged it as redundant. |
| `nflverse_coaching_research` | OPEN | coaching research lane | blocked until approved open source is verified | `src.data.nfl_open_data_sources` | Metadata-only candidate. |
| `CollegeFootballData` | API / FREE | NCAAF data, team stats, advanced records | partial, free-key candidate | `src.providers.ncaaf_collegefootballdata_adapter` | Useful for NCAAF, not NFL. |
| `sportsdataverse_cfb` | OPEN | NCAAF open data | partial | `src.data.data_source_registry` | Discovery lane for NCAAF. |
| `espn_nfl_public_wrapper` | API / PLACEHOLDER | NFL public wrapper | blocked by terms review | `src.data.data_source_registry` | Discovery found it, but not approved for use. |
| `espn_cfb_public_wrapper` | API / PLACEHOLDER | NCAAF public wrapper | blocked by terms review | `src.data.data_source_registry` | Discovery only. |
| `sportdata_nfl` | API / PLACEHOLDER | NFL candidate data lane | candidate only | `src.data.data_source_registry` | No active activation in this phase. |
| `sportdata_ncaaf` | API / PLACEHOLDER | NCAAF candidate data lane | candidate only | `src.data.data_source_registry` | No active activation in this phase. |
| `official_team_staff_pages` | OPEN / WEB | coaching staff metadata | blocked (`robots_disallows_automation`) | `src.market_intelligence.nfl_coaching_sources` | Useful source family, but not currently allowed for automation. |
| `official_team_press_releases` | OPEN / WEB | coaching/staff announcements | blocked (`html_scraping_terms_unclear`) | same | Provenance review required. |
| `official_nfl_staff_or_news_pages` | OPEN / WEB | coaching/staff announcements | blocked (`html_scraping_terms_unclear`) | same | Provenance review required. |
| `wikidata_coaching_seed` | OPEN | coaching seed data | allowed as structured seed lane | `src.providers.nfl_coaching_adapters` | Seed lane, not a complete authoritative source. |
| `wikipedia_coaching_seed` | OPEN | coaching seed data | allowed as structured seed lane | same | Seed lane, provenance should remain explicit. |
| `wikipedia_coaching_tables` | OPEN | coaching table supplement | partial | same | Supplemental only. |
| `open_github_nfl_coaches_dataset` | OPEN / PLACEHOLDER | coaching dataset candidate | blocked pending license/provenance review | `src.data.nfl_open_data_source_exhaustion` | Candidate only. |
| `pro_football_reference_web` | WEB / BLOCKED | coaching and advanced football context | blocked (`sports_reference_scraping_blocked`) | `src.data.nfl_open_data_source_exhaustion` | Not approved for scraping. |
| `ftn_charting_open_candidate` | UNKNOWN | charting metrics | terms unclear | `src.data.nfl_open_data_source_exhaustion` | Research required before use. |
| `the_odds_api_market` | COMMERCIAL | market odds | paid or budget required | `src.data.nfl_open_data_source_exhaustion` | Not a free/open default. |
| `open_meteo_stadium_weather` | OPEN | weather context | redundant with existing weather coverage | `src.data.nfl_open_data_source_exhaustion` | Not a new canonical need right now. |

## Current Ownership Pattern

The canonical owners are split by responsibility:

- open-data metadata and field catalogs: `src.data`
- provider adapters and readiness: `src.providers`
- coaching source registry and coaching features: `src.market_intelligence`
- availability / cutoff / impact diagnostics: `src.market_intelligence` and `src.analytics`

## Practical Conclusion

The repo already knows about many NFL provider candidates.
It does **not** yet have a validated, activated, end-to-end NFL ingestion lane.

That is the right place to be for discovery:

- enough structure to plan
- enough blockers to stay safe
- not enough evidence to pretend the slice is complete

