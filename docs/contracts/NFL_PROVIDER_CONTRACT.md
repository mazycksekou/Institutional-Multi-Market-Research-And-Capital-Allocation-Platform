# NFL Provider Contract

This contract defines the provider behavior expected for NFL-related sources.
It is discovery-only and intentionally does not activate any provider.

## Provider Categories

| Category | Meaning | Current NFL examples | Current status |
|---|---|---|---|
| OPEN | openly published or open-data source | `nflverse`, `nflfastr`, `nflreadr`, `wikidata_coaching_seed`, `wikipedia_coaching_seed` | usable as discovery facts, not yet fully validated ingest |
| FREE | no paid gate discovered | `nflverse` family, some open coaching seeds | available only as metadata/discovery in this phase |
| LOCAL | local validated artifact | local validated NFL markdown / JSON snapshots | present as artifacts, not as a complete data plane |
| API | API-backed source or candidate | `CollegeFootballData`, `SportData`, ESPN wrappers, The Odds API | mixed; many are blocked or require approval |
| COMMERCIAL | paid or budget-gated | `the_odds_api_market` | blocked / not the default |
| PLACEHOLDER | blocked, future, or disabled | official scraping lanes, license-gated datasets | intentionally not activated |
| UNKNOWN | not proven in discovery | certain charting / external coach datasets | needs further review |

## Current Provider Families Discovered

- open-data NFL providers:
  - `nflverse`
  - `nflfastr`
  - `nflreadr`
- NCAAF adapter/provider path:
  - `CollegeFootballData`
  - `sportsdataverse_cfb`
  - ESPN/NCAAF wrappers
- coaching / staff lanes:
  - official team pages
  - official press releases
  - official NFL staff/news pages
  - Wikidata / Wikipedia seed lanes
  - open GitHub coaching dataset candidate
- market / weather / context candidates:
  - `the_odds_api_market`
  - `open_meteo_stadium_weather`
  - `pro_football_reference_web`
  - `ftn_charting_open_candidate`

## Provider Contract Rules

- providers are metadata-first in this phase
- no provider writes
- no live execution
- no hidden scraper activation
- blocked or commercial lanes require explicit approval and terms review
- every provider must have a canonical owner in `src.*`

## Current Provider Risk Posture

The largest risks are:

- scraping / terms uncertainty
- paid-provider dependence
- redundant open-data families that should not become duplicate owners
- coaching data provenance

## Current Conclusion

The repo has a believable provider architecture for NFL discovery.
It does not yet have a fully activated provider system for NFL production use.

