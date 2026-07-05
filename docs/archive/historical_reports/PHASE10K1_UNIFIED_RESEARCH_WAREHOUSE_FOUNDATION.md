# Phase 10K1 – Unified Research Warehouse Foundation

**Phase 10K1 builds the storage foundation for a single master research database.**

---

## What was created

| Artifact | Purpose |
|----------|---------|
| `research/market_research_schema.py` | Schema version constant (`"10K1"`) and `CREATE TABLE IF NOT EXISTS` statements for 18 tables. |
| `research/market_research_store.py` | Safe functions: `get_default_market_research_db_path`, `initialize_market_research_db`, `list_market_research_tables`, `get_market_research_schema_version`, `table_exists`, `insert_schema_metadata`. |
| `research/__init__.py` | Package marker (unchanged). |
| `tests/test_market_research_store.py` | 12 tests covering default path, import-time safety, initialisation, idempotency, schema version, table existence, 0DTE column checks, and forbidden‑dependency checks. |

---

## Tables added (18)

- `raw_sports_odds`
- `raw_equity_prices`
- `raw_option_chains`
- `raw_option_quotes`
- `raw_prediction_markets`
- `raw_macro_liquidity`
- `raw_order_books`
- `features_sports`
- `features_equities`
- `features_0dte_options`
- `features_prediction_markets`
- `model_predictions`
- `backtest_runs`
- `backtest_trades`
- `option_backtest_trades`
- `arbitrage_opportunities`
- `settlements`
- `performance_metrics`
- `schema_metadata` (version tracking)

All tables are isolated, clean, and follow the naming conventions of the warehouse map from Phase 10K0.

---

## 0DTE‑specific schema fields

- `raw_option_chains`: `underlying_symbol`, `option_symbol`, `expiration_date`, `is_0dte`, `days_to_expiration`, `minutes_to_expiration`, `contract_type`, `strike`, `bid`, `ask`, `mid`, `implied_volatility`, `delta`, `gamma`, `theta`, `vega`
- `raw_option_quotes`: extra fields `spread_pct`, `premium`, `contract_multiplier`, `moneyness`, `distance_to_strike`

These columns align with the 0DTE Specificity Gap Map from Phase 10K0.

---

## What was NOT changed

- ❌ No vendor connectors, API calls, or scraper logic were added.
- ❌ No live data is imported.
- ❌ `bets.csv` / runtime CSV paths were not deleted or migrated.
- ❌ The existing `historical_odds` SQLite flow was not replaced or touched.
- ❌ No arbitrage implementation was added (the `arbitrage_opportunities` table is for future use only).
- ❌ No 0DTE model logic was added.
- ❌ Sports model math, bankroll math, and Kelly math were not altered.
- ❌ Streamlit main menu and Feature Ablation Lab were not modified.
- ❌ No dashboard pages were re‑added.

---

## Test results (all pass)

```
pytest tests/test_market_research_store.py -v
```

- 12 tests pass
- Source‑text contract tests for Streamlit remain untouched
- No existing tests are weakened or skipped

---

## Next recommended phase

**Phase 10K2** – 0DTE Options Schema Foundation  
- Define option chain/quote ingestion stubs
- Add Greeks calculation module (IV, delta, gamma, theta, vega) in `src/core/options_math.py`
- Wire `raw_option_chains` / `raw_option_quotes` to a future connector guard
- Begin separating generic equity logic from 0DTE‑specific logic

> - Sports prediction testing is deferred until Phase 10K7.  
> - 0DTE prediction testing is deferred until Phase 10K7.  
> - Do not implement arbitrage, warehouse, or delete duplicates in this phase.
