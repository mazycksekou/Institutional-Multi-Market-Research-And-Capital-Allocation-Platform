# PROVIDER_PRODUCT_GOAL_ALIGNMENT_REPORT_AFTER_10K8ZFQ

## Executive Summary
The repository still contains vendor-specific functionality that maps to the product goal, but the canonical architecture must remain product-category based. Useful code for prediction markets, 0DTE/stocks, and sportsbooks should be transported into category-owned packages. Vendor-only or unrelated areas should be isolated or marked for later deletion after safe verification.

## Prediction Markets
Vendor functionality that supports prediction markets includes:
- `betting_providers/kalshi_api.py`
- `providers/kalshi_provider.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `automation_scheduler/kalshi_monitor.py`
- `automation_scheduler/kalshi_scoring.py`
- `automation_scheduler/kalshi_readonly_readiness.py`
- `automation_scheduler/kalshi_adapter_contract.py`
- `kalshi_client.py`
- Polymarket references used in historical/backfill and planning surfaces

These modules support market fetches, normalization, readiness checks, candidate generation, and scoring for prediction-market workflows.

## 0DTE / Stocks
Vendor functionality that supports 0DTE/stocks includes:
- `automation_scheduler/data_source_registry.py`
- `automation_scheduler/provider_allowlist.py`
- `automation_scheduler/provider_write_firewall.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `market_pricing.py`
- `quant_engine.py`
- `main.py` references that route stock and market-data capabilities
- references to Robinhood, Alpaca, Polygon, IEX, Tradier, Schwab, Yahoo/yfinance, Nasdaq, and CME

These areas support market-data selection, pricing/math helpers, and stock-facing provider policy surfaces.

## Sportsbooks
Vendor functionality that supports sportsbooks includes:
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `providers/sharp_provider.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `automation_scheduler/sportsbook_adapter_contract.py`
- sportsbook brand references such as DraftKings, FanDuel, BetMGM, Caesars, ESPN BET, Pinnacle, Bet365, and Bovada

These modules support sportsbook odds, normalization, adapter contracts, and routing.

## Non-Goal or Delete Candidate Areas
The following do not support the current product goal and should be isolated or marked for deletion after safe verification:
- AI vendor references such as OpenAI, Anthropic, Gemini, Perplexity, and Together
- crypto / exchange references such as CoinMarketCap, Coinbase, Binance, and Kraken
- any broker-execution or live-trading code path
- any scraper-only or external connector-only path not required for the product categories

## Ambiguous Areas
Ambiguous areas that require a later decision before migration include:
- `automation_scheduler/data_source_registry.py`, because it mixes useful stock/data-source support with non-goal vendor families
- `automation_scheduler/provider_allowlist.py`, because it blends safety policy with vendor classification
- `automation_scheduler/provider_write_firewall.py`, because it is a safety wrapper rather than a product feature
- `screenshot_intake.py`, because it bridges route behavior and provider lookups
- `src/services/enrichment_service.py`, because it still routes through legacy provider shells

## Decision Points Before Migration
1. Split pure prediction-market functionality from sportsbook functionality.
2. Decide whether market-data vendor references belong in `zero_dte_stocks` or are non-goal.
3. Decide whether shared provider safety belongs in `src/providers/` policy helpers or remains a bridge layer.
4. Keep AI, broker, and scraper references out of canonical provider ownership.

## Required Statement
Vendor-specific modules are not canonical architecture owners. Useful functionality should be transported into prediction_markets, zero_dte_stocks, or sportsbooks. Vendor modules that do not support the product goal should be marked for deletion after safe verification.

## Files and Categories
| Category | Representative vendors / modules | Status |
| --- | --- | --- |
| `prediction_markets` | Kalshi, Polymarket | transport target |
| `zero_dte_stocks` | Robinhood, Alpaca, Polygon, IEX, Tradier, Schwab, Yahoo/yfinance, Nasdaq, CME | transport target |
| `sportsbooks` | Sharp, The Odds API, SportsGameOdds, DraftKings, FanDuel, BetMGM, Caesars, ESPN BET, Pinnacle, Bet365, Bovada | transport target |
| non-goal / delete candidate | OpenAI, Anthropic, Gemini, Perplexity, Together, CoinMarketCap, Coinbase, Binance, Kraken | isolate or delete later |

## Next Decision Need
Choose a first transport batch that moves one product category at a time, preserves compatibility wrappers, and proves import safety with fake-client tests before any legacy module removal.

## Boundary Clarification
AI/LLM, brokerage/live-trading, and scraper/live-connector functionality are future production domains, not automatic deletion categories. The delete-or-isolate labels in this report apply only to vendor-specific or duplicate legacy ownership. Preserve the scaffold boundaries under `src/ai`, `src/brokerage`, and `src/connectors` for later controlled implementation.
