# Provider Field Matrix

| Lane | Category | Status | Candidate sources | Verified sources | Top missing fields |
|---|---|---|---:|---:|---|
| `prediction_markets` | `prediction_market` | candidate_sources_available | 4 | 0 | `bid_ask`, `close_time`, `market_status` |
| `polymarket` | `prediction_market` | candidate_sources_available | 4 | 0 | `settlement_result` |
| `institutional_stock_pro_analyst` | `stock_analytics` | candidate_sources_available | 24 | 0 | `liquidity`, `macro_context`, `news_sentiment`, `rates_context` |
| `cryptocurrency_edge_lab` | `crypto` | candidate_sources_available | 27 | 0 | `macro_context` |
| `bonds` / `rates` / `macro` / `major_assets` | `financial_market` | candidate_sources_available | 4-10 | 0 | `volume` |
| `sportsbooks` | `odds` | candidate_sources_available | 10 | 0 | `event_id`, `source_context`, `stable_join_key`, `timestamp` |
| `officials` / `injuries` / `lineups` / `news_context` | `context` | needs_external_research | not yet stable | 0 | `event_id`, `source_context`, `stable_join_key`, `timestamp` |

## Provider source-type interpretation

- `API` sources are present as candidates for multiple lanes.
- `CSV`, `SQLite`, `Parquet`, and manual import paths are represented in the historical/data contracts.
- `USB`, streaming, and unknown source classes remain architectural possibilities rather than current implementation facts.

## Current provider safety posture

- No provider writes are enabled.
- No execution is allowed.
- No live connector activation is permitted in this phase.
