# Complete Gap Analysis

## Missing metrics

- No discovered metric remains unclassified at the architecture level in the current discovery set.
- Remaining gaps are about source verification, not about missing metric names.

## Missing schemas

- Verified source-backed schemas for all 38 lanes are still missing.
- The four external-research lanes remain `needs_external_research`.
- Some context lanes still need source validation before they can be treated as stable contracts.

## Missing providers

- 0 lanes have verified sources.
- 8 future source candidates are already named.
- Provider activation is still disabled across the board.

## Missing backtests

- Source-backed historical backtests are not yet verified for any lane.
- The backtest contracts exist, but lane-by-lane historical coverage still needs provider work.

## Missing dashboards

- The main dashboard exists.
- Some lane-specific dashboards remain represented as scaffolds rather than fully populated operational pages.

## Missing APIs

- There is no live provider API activation in this phase.
- Current APIs are still primarily dashboard / orchestration surfaces.

## Top unresolved data gaps from the registry

| Module | Top missing fields |
|---|---|
| `prediction_markets` | `bid_ask`, `close_time`, `market_status` |
| `polymarket` | `settlement_result` |
| `institutional_stock_pro_analyst` | `liquidity`, `macro_context`, `news_sentiment`, `rates_context` |
| `cryptocurrency_edge_lab` | `macro_context` |
| `bonds` / `rates` / `macro` / `major_assets` | `volume` |
| `sportsbooks` | `event_id`, `source_context`, `stable_join_key`, `timestamp` |
| `officials` / `injuries` / `lineups` / `news_context` | `event_id`, `source_context`, `stable_join_key`, `timestamp` |

## Recommended resolution order

1. Prioritize lanes with the strongest source candidates: prediction markets, sportsbooks, crypto, and the most mature financial-market lanes.
2. Fill the four external-research lanes only after the core lanes are source-stable.
3. Use the canonical backtest contract to prove leakage safety before widening model scope.
4. Keep dashboard work aligned with the same canonical field groups so display and backtest stay in sync.
