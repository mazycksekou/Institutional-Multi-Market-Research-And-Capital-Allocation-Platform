# Phase 10K4 – 0DTE Options Schema Foundation and Existing Owner Validation

## A. Executive Summary

Phase 10K4 validates the existing stock, equity, and option placeholder modules already present in the repository, deepens the warehouse design for 0DTE options, and produces a documented 0DTE field contract.

**Hard restrictions observed:**  
- No vendor connectors, API calls, scraper logic, paid data controls, or brokerage integration.  
- No live market data import.  
- No 0DTE prediction testing, sports prediction testing, or prediction‑market testing.  
- No frontend pages added or Streamlit main menu altered.  
- No second warehouse/store created.  
- No runtime/CSV migration.  
- No duplicate code deleted.  
- No old stock/equity placeholders deleted.  
- The current Streamlit main menu remains exactly: Feature Ablation Lab, Bankroll Settings, Instructions.

**Key principle:** 0DTE options are treated as contract‑level instruments, **not** as generic stocks. Generic stock ticker/price/signal is insufficient for 0DTE analysis.

## B. Existing Owner Validation

| Candidate owner / module | Current purpose | Evidence inspected | Behavior proven by test/source | Fits 10K4 need? | Decision | Risk |
|---|---|---|---|---|---|---|
| `research/market_research_schema.py` | 10K1 warehouse schema: defines `raw_option_chains`, `raw_option_quotes`, `features_0dte_options`, `option_backtest_trades`. | Source code, existing test `test_market_research_store.py` | `raw_option_chains` contains underlying_symbol, option_symbol, expiration_date, is_0dte, days_to_expiration, minutes_to_expiration, contract_type, strike, bid, ask, mid, implied_volatility, delta, gamma, theta, vega, underlying_price. <br>`raw_option_quotes` contains spread_pct, premium, contract_multiplier, moneyness, distance_to_strike. <br>`features_0dte_options` and `option_backtest_trades` exist. | Yes – all required 0DTE identity, quote, Greeks, and trade fields are present. | **Use** as‑is. | Low |
| `research/market_research_store.py` | Idempotent warehouse initialisation and table inspection. | Source and tests. | Creates all 10K1 tables; schema version stored; no vendor imports. | Partial – store layer already handles the tables without change. | **Use** as‑is. Do not extend in 10K4. | Low |
| `src/api/stock_analysis_routes.py` | Stock analysis endpoint using yfinance (period/interval) for any ticker. | Source + `main.py` registration. | Returns OHLCV with ticker, but no contract or Greeks fields. | No – generic stock endpoint cannot be reused for 0DTE. | **Go around**. A new 0DTE‑dedicated endpoint will be added in a later phase (never in 10K4). | Low – no wiring needed now. |
| `src/core/math_utils.py` | Core odds/Kelly/edge math; no option Greeks. | Source + existing tests. | Provides American/decimal conversion, implied probability, edge, Kelly, EV. No delta, gamma, theta, vega. | No – 0DTE requires option‑specific math. | **Go around**. Option Greeks module (`src/core/options_math.py`) deferred to 10K5. | Low – no change required now. |
| `automation_scheduler/historical_line_movement.py` | Timeline snapshot table (`historical_line_snapshots`) and volatility helpers for sports odds. | Source + tests. | Creates deterministic snapshots; upsert by snapshot_id; line/odds ranges; volatility classification. | Partial – the append‑only snapshot pattern and volatility classification are reusable. | **Extend** later (10K6) to support option chain snapshots. Do **not** alter in 10K4. | Low – left untouched. |
| `automation_scheduler/historical_odds_importers.py` | CSV/JSON parsers for Football‑Data, MLB, SBR. No options. | Source + tests. | Reading local files only; no network. | No – no options ingestion yet. | **Go around**. Future option‑chain importer will be separate. | Low – no wiring. |
| `automation_scheduler/historical_odds_sqlite.py` | Legacy sports‑odds SQLite store. | Source + tests. | Tables: `source_imports`, `historical_events`, `historical_odds`, `historical_results`. Upserts by deterministic IDs. | No – not raw append‑only; lacks contract fields. | **Go around**. Future 0DTE warehouse will be `research.market_research_store`, not this legacy store. | Low – no change. |
| `automation_scheduler/backtest_strategy_profiles.py` | Sport‑aware regression profile selection for sports backtesting. | Source + tests. | Normalises profile keys; builds all‑sports / sport‑specific configs. | Partial – the profile routing pattern can be reused for 0DTE‑specific profiles later. | **Extend** later (10K6) with `option` profile keys. Not now. | Low. |
| `automation_scheduler/provider_registry.py` | Provider definitions (Sharp, Kalshi, placeholder). | Source + tests. | Contains `stock_placeholder`, `news_placeholder`; no 0DTE provider. | No – no options provider exists. | **Go around**. Future 0DTE provider registration will happen in a later phase. | Low. |
| `automation_scheduler/streamlit_dashboard_data.py` | Dashboard data facade; currently handles sports odds, backtest results, line movement. | Source + tests. | No options‑related functions. | No – no 0DTE dashboard methods yet. | **Go around**. Future 0DTE dashboard helpers will be added in 10K6. | Low. |
| `quant_engine.py` | Sports math wrappers for odds conversion, Kelly, EV, edge. | Source + tests. | No option math. | No – must be extended later with options‑specific wrappers. | **Go around**. Extension deferred to 10K5/10K6. | Low. |

**No owner candidate was used incorrectly.** All decisions are documented above. No blind wiring occurred.

## C. 0DTE Field Contract

### Required contract identity
- `underlying_symbol`
- `option_symbol`
- `expiration_date`
- `is_0dte` (TINYINT, 1 = same‑day expiry)
- `days_to_expiration`
- `minutes_to_expiration`
- `contract_type` (`call` / `put`)
- `strike`

### Required quote / liquidity
- `bid`
- `ask`
- `mid`
- `spread_pct`
- `premium`
- `volume`
- `open_interest`

### Required Greeks / volatility
- `implied_volatility`
- `delta`
- `gamma`
- `theta`
- `vega`

### Required risk / fill
- `contract_multiplier`
- `max_premium_risk`
- `max_contracts`
- `max_daily_0dte_loss`
- `entry_window_start`
- `entry_window_end`
- `forced_exit_time`
- slippage / fill‑assumption profile
- liquidity filter profile

### Required derived features (for future `features_0dte_options`)
- `moneyness`
- `distance_to_strike`
- `minutes_to_close` (derived from expiration minus observation)
- `theta_decay_proxy`
- `gamma_risk_proxy`
- `spread_pct` (already in `raw_option_quotes`)
- `premium_as_pct_of_underlying`
- `max_premium_risk` / `max_contracts` / `max_daily_0dte_loss` (risk limits, will be in separate tables later)

All fields above that are present in the 10K1 schema are already verified in the warehouse.

## D. Current Warehouse Compatibility

### What 10K1 already has
- All 18 tables including `raw_option_chains`, `raw_option_quotes`, `features_0dte_options`, `option_backtest_trades`.
- The required identity, quote, liquidity, Greeks, and trade fields are present.  
- `raw_option_chains` includes: underlying_symbol, option_symbol, expiration_date, is_0dte, days_to_expiration, minutes_to_expiration, contract_type, strike, bid, ask, mid, last, volume, open_interest, implied_volatility, delta, gamma, theta, vega, underlying_price, observed_at, inserted_at.  
- `raw_option_quotes` adds: spread_pct, premium, contract_multiplier, moneyness, distance_to_strike.  
- `features_0dte_options` exists (generic EAV pattern).  
- `option_backtest_trades` includes: run_id, underlying_symbol, option_symbol, expiration_date, is_0dte, contract_type, strike, entry_bid/ask/mid, exit_bid/ask/mid, contracts, premium_risk, max_loss, spread_pct_at_entry, entry_time, exit_time, forced_exit, pnl, inserted_at.

### What was validated
All columns listed in the contract (Section C) that are mandatory for the phase 10K4 foundation were verified against the schema file and existing tests.

### What was missing (deferred)
- `option_trade_candidates` table (risk/pre‑trade evaluation)
- `option_risk_limits` table
- `option_fill_assumptions` table
- `features_0dte_options` derived field columns (minutes_to_close, theta_decay_proxy, gamma_risk_proxy, premium_as_pct_of_underlying)

**No schema changes were made in 10K4.** The 10K1 warehouse is sufficient to hold raw 0DTE data once ingestors are added (later phases). Missing tables are documented as deferred candidates (see Section E).

## E. Optional Tables Decision

| Table name | Proposed fields (if added) | Decision | Reason | Later phase |
|---|---|---|---|---|
| `option_trade_candidates` | candidate_id, model_name, model_version, underlying_symbol, option_symbol, expiration_date, is_0dte, contract_type, strike, side, entry_bid/ask/mid, spread_pct, premium, contract_multiplier, delta, gamma, theta, vega, implied_volatility, moneyness, distance_to_strike, max_premium_risk, max_contracts, max_daily_0dte_loss, entry_window_start/end, forced_exit_time, reason_codes, as_of_time, inserted_at | **Deferred** – no existing prediction or candidate generation code yet. | Adding the table now would create an unreferenced table that no code populates. | 10K6 (when first 0DTE backtest/projection is wired) |
| `option_risk_limits` | profile_name, underlying_symbol, max_premium_per_trade, max_contracts, max_daily_loss, max_trades_per_day, no_new_entries_after, forced_exit_time, min_volume, min_open_interest, max_spread_pct, inserted_at | **Deferred** – no risk‑profile code for options exists yet. | Same rationale as above. | 10K6 |
| `option_fill_assumptions` | profile_name, market_type, fill_price_method, slippage_bps, use_mid_price, reject_wide_spreads, max_spread_pct, inserted_at | **Deferred** – no fill‑assumption logic exists yet. | Same rationale. | 10K6 |

No optional table was added in 10K4.

## F. Generic Stock vs 0DTE Separation

- `raw_equity_prices` stores daily OHLCV for stocks/ETFs. It lacks any option‑specific fields (strike, expiration, Greeks, premium).  
- 0DTE options require **contract‑level rows** (`raw_option_chains`, `raw_option_quotes`) and **dedicated risk rules** (`max_premium_risk`, `forced_exit_time`, etc.).  
- A future `market_type` discriminator should separate `equities` from `options_0dte` (and later `options_non_0dte`).  
- Future UI (10K6) must present Stocks/ETFs and 0DTE Options as separate sections; **no UI changes now**.

## G. No‑Duplicate Decisions

All new functions/tables considered for 10K4 were checked against existing owners. The full register is documented in Section B. No duplicate code was created. No duplicate table was created.

## H. Testing Plan

Efficient same‑flow:

1. Targeted test (this phase):
   ```bash
   pytest tests/test_phase10k4_0dte_options_schema_foundation.py -q
   ```
2. Full suite (after first commit):
   ```bash
   pytest tests/ -x
   ```
3. Smoke check:
   ```bash
   python scripts/smoke_test.py
   ```
4. Stat check:
   ```bash
   python scripts/ops_check.py
   ```
5. Commit only when clean.
6. Rerun stat after commit.
7. Do **not** rerun full test after commit unless code/hooks changed files after tests.

No additional tests are required for the existing warehouse tests; they continue to pass.

## I. Next Phase Impact

- **10K5 Core Arbitrage Engine**: The 0DTE quote fields (`spread_pct`, `moneyness`, `distance_to_strike`) are ready for parity‑arbitrage logic.  
- **10K6 Frontend Navigation Expansion**: The report documents that 0DTE Options must be separate from Stocks/ETFs in the UI; menu remains unchanged.  
- **10K7 Full Suite Readiness Review**: All 10K1 tables are validated; no incomplete schema blocks.  
- **10K8 Prediction Testing Phase**: Option model predictions will use the `features_0dte_options` table; risk‑limit and fill‑assumption tables will be added before live inference.  
- **10K9 Asset‑Grade Clean Product Repo**: Duplicate owners tracked in Section B are candidates for cleanup after migration parity is proven.

---

**End of Phase 10K4 Report**  
*No vendor connectors, no prediction testing, no UI changes, no schema changes.*


## Required Phase 10K4 Guardrail Strings

Do not assume existing owners work correctly.
0DTE is not generic stocks.
no live connectors.
do not alter Streamlit main menu.

