# Market Capability Matrix

Implementation status is based on current repository discovery, not assumptions.

| Market lane | Category | Lane status | Candidate sources | Verified sources | Overall maturity |
|---|---|---|---:|---:|---|
| `prediction_markets` | `prediction_market` | candidate_sources_available | 4 | 0 | PARTIAL |
| `kalshi` | `prediction_market` | candidate_sources_available | 2 | 0 | PARTIAL |
| `polymarket` | `prediction_market` | candidate_sources_available | 4 | 0 | PARTIAL |
| `institutional_stock_pro_analyst` | `stock_analytics` | candidate_sources_available | 24 | 0 | PARTIAL |
| `cryptocurrency_edge_lab` | `crypto` | candidate_sources_available | 27 | 0 | PARTIAL |
| `stocks` / `ETFs` / `bonds` / `rates` / `macro` / `major_assets` | `financial_market` | candidate_sources_available | 13 / 3 / 4 / 5 / 10 / 3 | 0 | PARTIAL |
| `fx_currencies` | `fx` | candidate_sources_available | 11 | 0 | PARTIAL |
| `sportsbooks` / `odds` | `odds` | candidate_sources_available | 10 / 10 | 0 | PARTIAL |
| `weather` / `news_sentiment` / `government_open_data` | `environment` / `news_sentiment` / `government_open_data` | candidate_sources_available | 21 / 18 / 24 | 0 | PARTIAL |
| `transportation_logistics` / `health_public_context` / `security_ops` | `transportation` / `health_public_context` / `security_ops` | candidate_sources_available | 9 / 6 / 8 | 0 | PARTIAL |
| `officials` / `injuries` / `lineups` / `news_context` | `context` | needs_external_research | not yet stable | 0 | SCAFFOLD |
| `basketball_nba` / `basketball_wnba` / `americanfootball_nfl` / `americanfootball_ncaaf` / `baseball_mlb` / `icehockey_nhl` / `soccer` / `tennis` / `ufc_mma` / `boxing` / `golf` / `basketball_ncaab` / `basketball_ncaaw` | `sport` | candidate_sources_available | present | 0 | PARTIAL |

## Reading the matrix

- `candidate_sources_available` means the repo has candidate data-source planning for the lane.
- `needs_external_research` means the lane still needs external validation before a safe source plan.
- `PARTIAL` means the lane is modeled but not verified end-to-end.
- `SCAFFOLD` means the lane exists as an architectural lane but still needs source work.
- `COMPLETE` is reserved for concrete runtime artifacts and verified source-backed support.
