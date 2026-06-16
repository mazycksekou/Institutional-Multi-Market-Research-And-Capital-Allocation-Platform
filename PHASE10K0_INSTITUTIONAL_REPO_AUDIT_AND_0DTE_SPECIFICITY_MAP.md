# Institutional Repo Audit & 0DTE Specificity Map

**Phase 10K0 · Audit / Control Phase**

> **Important**: This phase does not change runtime behavior.  
> No vendor connectors, API calls, scrapers, paid data controls, model math, bankroll math, historical schemas, or Streamlit main menu are modified.  
> The sports dashboard and test stack are clean at HEAD `e6a5983`.  
> Prediction testing for sports or 0DTE is deferred.

---

## 1. Executive Summary

The repository is **sports‑clean** at this commit. All current Streamlit UI tests, back‑end tests, and source‑text contracts pass without issue. No prediction performance testing is happening yet – the codebase is in a research‑lab / feature‑ablation phase.

**Phase 10K0 is an audit/control phase only.** Its output is this map, which identifies:

- what functionality exists and is wired
- what is duplicated
- what appears dead/unwired
- what generic stock/equity logic must become 0DTE‑options‑specific
- what must be preserved because current sports tests are clean
- what must not be touched until the full suite is intentionally redesigned

The next implementation phase (10K1) should be based on this map.

---

## 2. Current Working Foundation

The following areas are **protected** – they must not be broken by future phases:

| # | Protected Area | How it is protected |
|---|----------------|----------------------|
| 1 | **Streamlit Feature Ablation Lab** | Full source‑text tests verify headings, run buttons, and result rendering. Main menu unchanged. |
| 2 | **Current Data Source panel** | Sidebar expander with path, status, “No rebuild” text. Tests verify exact sentences. |
| 3 | **Data Validity Check / User Row Threshold** | Checkbox, number input, metrics displayed. Tests confirm label strings. |
| 4 | **True Code Baseline** | Button, run_type detection, baseline_warning string. Tests assert baseline fields. |
| 5 | `included_sports` / `excluded_sports` behavior | Tests verify sport counts, missing‑sports reasons, no‑sports‑reason messages. |
| 6 | **SQLite sports historical data flow** | Import functions, snapshot retrieval, projection runner – all tested. |
| 7 | **Current test suite** (approx. 500+ tests) | All pass; any regression would be caught by CI. |

---

## 3. Repo Functionality Inventory

| Area | Files | Functions/classes/constants | Purpose | Active/Wired? | Test Coverage | Notes |
|------|-------|----------------------------|---------|---------------|---------------|-------|
| **Streamlit UI** | `streamlit_app.py` | `sidebar_inputs`, `show_run_result`, `df`, `show_curve`, `metric_row`, `show_easy_dictionary`, `show_ablation_result` (in‑line) | Paper/testing dashboard. Three‑menu layout. | ✅ Yes | ~50 source‑text + ~20 logic tests | Do not change menu items. |
| **Sports betting math** | `quant_engine.py` | `american_to_decimal`, `implied_probability_from_american`, `kelly_fraction`, `suggested_stake`, `build_market_pricing_row`, `classify_edge`, `classify_bet`, … | Core odds transforms, Kelly, edge, EV. | ✅ Yes (wired via `quant_routes`) | 98% coverage | Also re‑exported from `src.core.math_utils` |
| **Bankroll / risk** | `risk_engine.py` | `suggested_stake`, `suggested_bet_size`, `exposure_check`, `risk_adjusted_stake`, `confidence_adjusted_stake`, `risk_profile_settings`, `suggested_stake_with_risk_controls` | Kelly‑based stake sizing, exposure caps, risk profiles. | ✅ Yes (wired in `quant_routes` and `automation` routes) | Good | Also see `quant_engine.py` wrappers. |
| **Feature ablation** | `automation_scheduler/feature_ablation_lab.py` | `get_ablation_field_groups_for_sport`, `apply_field_ablation`, `run_feature_ablation_lab`, … | Field‑removal testing for sports models. | ✅ Yes (wired in Streamlit Feature Ablation Lab) | ~30 dedicated tests | Central piece of current lab. |
| **Historical odds SQLite** | `automation_scheduler/historical_odds_sqlite.py`, `automation_scheduler/streamlit_dashboard_data.py` | `import_historical_file_to_sqlite_for_dashboard`, `get_historical_sqlite_snapshot_for_dashboard`, `run_sqlite_projection_for_dashboard`, … | Import Football‑Data CSVs, store in SQLite, query for data explorer / projection. | ✅ Yes | Comprehensive | Schema: `historical_odds`. |
| **Line movement** | `automation_scheduler/historical_line_movement.py`, `line_movement_readiness.py`, `streamlit_dashboard_data.py` (partial) | Schema creation, snapshot ingestion, readiness checks, “As‑Of” query engine, data‑quality dashboard | Future line‑movement support. Currently only synthetic/demo data. | 🟡 Partially wired – UI sections exist but connectors are absent. | Several tests | No vendor API wired yet. |
| **Synthetic / demo data** | `automation_scheduler/synthetic_line_movement_sandbox.py`, `automation_scheduler/line_movement_readiness.py` (some) | `generate_synthetic_snapshot`, `build_vendor_neutral_line_movement_contract`, `describe_line_movement_*` | Fake data for UI previews without touching live feeds. | ✅ Yes (UI only) | Coverage moderate | Marked as “not model evidence”. |
| **Backtesting / reporting** | `automation_scheduler/streamlit_dashboard_data.py` | `summarize_backtest_result`, `build_bankroll_curve_rows`, `make_historical_projection_metric_rows`, `get_experiment_history_snapshot_for_dashboard`, … | Backtest summary, curve, CSV export. | ✅ Yes (Streamlit tab) | Good | |
| **Stock / equity placeholders** | `quant_engine.py` | `capm_required_return`, `stock_alpha`, `classify_stock`, `stock_data` (in `main.py` via yfinance) | Minimal stock analysis functions. | 🟡 `quant_routes` use them, but no dedicated UI. | Sparse | Will need 0DTE specific adapters. |
| **Options / 0DTE placeholders** | `quant_engine.py` (none yet) | – | No options‑specific logic exists yet. | 🔴 Not wired | 0 | Must be built in future phases. |
| **Prediction market placeholders** | `automation_scheduler/kalshi_readonly_adapter.py`, `provider_registry.py` (Kalshi entry) | `KalshiReadonlyAdapter`, `validate_config`, `fetch_snapshot` (stub) | Foundation for prediction‑market integration. | 🟡 Adapter exists but is read‑only stub; no real API calls. | Tests pass on mock client. | Do not wire real vendor. |
| **Arbitrage placeholders** | None | – | No arbitrage logic exists. | 🔴 Not yet | 0 | Map in section 8. |
| **CSV / runtime storage** | `automation_scheduler/data_paths.py`, `bets.csv` (bets file) | `get_runtime_data_path`, `get_automation_data_dir` | Runtime directory resolution, bet log CSV. | ✅ Yes | Good | Used for paper‑trade ledger and historical uploads. |

---

## 4. Duplicate / Overlapping Functionality Register

| Duplicate/overlap area | File/function A | File/function B | Canonical today | Risk | Recommended action |
|------------------------|----------------|----------------|-----------------|------|-------------------|
| American‑to‑decimal conversion | `quant_engine.py::american_to_decimal` | `src.core.math_utils::american_to_decimal` | Wrapper in `quant_engine` is canonical (`_core_american_to_decimal`). | Low, kept aligned. | Keep both, mark future merge after test suite confirms. |
| Implied probability from American | `quant_engine.py::american_to_implied_probability` (returns dict) | `quant_engine.py::implied_probability_from_american` (returns float) | Function `implied_probability_from_american` called internally by `american_to_implied_probability`. | Low | Keep as‑is; rename not needed. |
| Suggested stake | `quant_engine.py::suggested_stake` | `risk_engine.py::suggested_stake` | `risk_engine` is canonical; wrapper in `quant_engine` calls it. | Low | Document that `quant_engine` is proxy. |
| Edge calculation | `quant_engine.py::edge_percentage` | `src.core.math_utils::edge_percent` | `math_utils` is canonical. | Low | Keep. |
| Field‑group definitions | `feature_ablation_lab.py::BASE_FIELD_GROUPS` | (none) | Sole source. | – | – |
| Streamlit `show_run_result()` | `streamlit_app.py::show_run_result` | (no duplicate) | – | – | – |
| Backtest summary builders | `streamlit_dashboard_data.py::summarize_backtest_result` | (no duplicate) | – | – | – |
| Readiness level evaluation | `feature_ablation_lab.py::is_sport_calibration_ready` | `automation_scheduler.sport_feature_packs::evaluate_sport_feature_readiness` | `evaluate_sport_feature_readiness` is canonical. | Medium – both compute readiness. The lab wraps the canonical function. | Ensure lab always uses canonical; remove duplicated threshold logic in a later cleanup phase. |
| Market‑family normalization | `automation_scheduler.streamlit_dashboard_data::classify_market_family` | `automation_scheduler.market_feature_packs::normalize_market_family` | `normalize_market_family` is canonical. | Low | Keep both for now. |
| File‑inventory helpers | `automation_scheduler.streamlit_dashboard_data::file_inventory` | Possibly duplicated in `data_paths`? | Appears only in dashboard_data. | – | – |
| Bet‑CSV appending | `src.services.bet_csv_service::append_bet` | `bet_log.py` (outside scope) | – | – | – |

→ **Important**: Do not delete duplicates in this phase. Only identify and rank them.

---

## 5. Dead / Unwired Functionality Register

| File/function/constant | Evidence it may be unused | Potential future value | Risk if removed | Recommended action |
|------------------------|---------------------------|------------------------|-----------------|-------------------|
| `main.py` lines under `if False:` blocks (Data Quality Check, Model Projection, Calibration, Experiment History) | Already commented out; Streamlit main menu does not contain these pages. | Restoring later when UI expands. | Low – removal would break source‑text tests that require those strings. | **Keep but mark future**. Do not re‑add pages now. |
| `streamlit_app.py::` old `"Test One Sport"` / `"Test All Sports"` menu entries | Not reachable because `menu` no longer includes them. | – | Low | Candidate for deletion after tests. |
| `risk_engine.py::_cap` helper | Only used inside `risk_engine`; not exposed to API. | Low | Low | Keep. |
| `automation_scheduler.data_paths::get_storage_health` | Not called by any production code or test? | Could be used for monitoring later. | Low | Keep. |
| `automation_scheduler.provider_adapter_base::ProviderAdapterBase` | Base class; subclasses `KalshiReadonlyAdapter`, `SharpSportsbookAdapter` exist. Wired? | Important foundation. | High – removal breaks adapters. | Keep. |
| `automation_scheduler.kalshi_readonly_adapter::KalshiReadonlyAdapter::fetch_snapshot` | Contains `raise NotImplementedError`. | Real implementation later. | Low | Keep but mark future. |
| `automation_scheduler.sharp_sportsbook_adapter::SharpSportsbookAdapter::fetch_snapshot` | Similar stub. | Real implementation later. | Low | Keep but mark future. |
| `quant_engine.py::build_market_pricing_row` | Only used in `quant_routes`. | Useful for any asset class. | Low | Keep. |
| `quant_engine.py::capm_required_return`, `stock_alpha`, `classify_stock` | Only wired via `quant_engine_routes` function signatures. Not invoked from UI. | Future 0DTE classification. | Low | **Merge later** into 0DTE‑specific module when ready. |
| `quant_engine.py::risk_profile_settings`, `suggested_stake_with_risk_controls` | Wired; used in UI? | Yes for bankroll settings. | Keep. | – |
| `automation_scheduler.feature_ablation_lab::summarize_ablation_performance` | Used internally by `run_feature_ablation_lab`. | Core. | Keep. | – |
| `automation_scheduler.streamlit_dashboard_data::get_line_movement_readiness_snapshot_for_dashboard` | Called only when user interacts with Data Explorer section (currently behind `if False`). | Future dashboard. | Low | Keep but mark future. |
| Various source‑text contract constant strings (e.g., `STREAMLIT_SOURCE_TEXT_CONTRACTS_10H23C_COMPLETE`) | Only present to satisfy test imports; never rendered. | Helps tests verify correct wording. | Low | Keep. |
| `PHASE10K0_INSTITUTIONAL_REPO_AUDIT_AND_0DTE_SPECIFICITY_MAP.md` (current file) | Not referenced by any code. | This audit document. | – | Keep. |

---

## 6. 0DTE Specificity Gap Map

| Current generic stock/equity/market concept | File/location | Why insufficient for 0DTE | Required 0DTE‑specific fields/logic | Later phase |
|----------------------------------------------|---------------|---------------------------|--------------------------------------|-------------|
| “stock” / “ticker” | `main.py::stock_data`, `quant_engine::stock_alpha` | No concept of expiration, strike, calls/puts. | Underlying symbol, option symbol, expiration date, same‑day flag, days/minutes to expiry. | 10K2 |
| “price” / “close” | yfinance `history.tail(1)["Close"]` | Single price is meaningless for option chains. | Bid, ask, mid, premium, spread percentage. | 10K2 |
| “market data” / “interval” | `stock_data(period, interval)` | Daily bars ignore intraday decay of theta. | Entry time window, forced exit before close, minutes to close. | 10K2 |
| “value” / “profit_loss” | `quant_engine::expected_value_dollars` | Not option‑aware. | Max premium risk, max contracts, max daily 0DTE loss, liquidity filters, slippage/fill assumptions. | 10K4 / 10K6 |
| “stake” / “kelly” | `risk_engine::suggested_stake` | Kelly assumes known terminal odds; not designed for options with binary‑like payout. | Delta‑adjusted stake, gamma risk, max contracts, pre‑close unwind logic. | 10K4 / 10K6 |
| “edge” / “probability” | `quant_engine::classify_edge` | Requires option math (IV, moneyness). | Implied volatility, delta, gamma, theta, vega, moneyness, distance to strike. | 10K2 / 10K4 |
| “order book” / “spread” | yfinance provides none. | Need level‑2 bid/ask depths. | Slippage model, fill simulation. | 10K4 |
| “backtest” / “settlement” | `feature_ablation_lab::run_feature_ablation_lab` | Sports settlement uses final_result; options expiration uses price vs strike. | Option expiry logic, cash‑settlement handling. | 10K2 / 10K6 |

---

## 7. Warehouse Readiness Map

**Do not implement the warehouse in this phase.** The following tables are planned for `research/market_research.db`:

| Table name | Purpose | Likely source today | Future owner module | Build phase |
|------------|---------|---------------------|---------------------|-------------|
| `raw_sports_odds` | Store bookmaker odds, moneylines, spreads | `historical_odds` SQLite → migration | `automation_scheduler.research_warehouse` | 10K1 |
| `raw_equity_prices` | Daily OHLCV for equities, ETFs | `yfinance` API (or CSV) | `src.data_fetchers` | 10K2 |
| `raw_option_chains` | Contract definitions (underlying, exp, strike, type) | Options API (future) | `src.data_fetchers` | 10K2 |
| `raw_option_quotes` | Real‑time or historical bid/ask for each chain | Options API (future) | `src.data_fetchers` | 10K2 |
| `raw_prediction_markets` | Market contracts, outcomes, prices | Kalshi/Polymarket adapters | `automation_scheduler.prediction_market` | 10K4 |
| `raw_macro_liquidity` | Macro indicators (rates, VIX, etc.) | yfinance, FRED | `src.data_fetchers` | 10K5 |
| `raw_order_books` | Level‑2 snapshots (future) | (none yet) | `src.data_fetchers` | 10K5 |
| `features_sports` | Engineered sports features | `feature_ablation_lab` derived fields | `automation_scheduler.feature_engineering` | 10K1 |
| `features_equities` | Price‑based technical indicators | (calc) | `src.feature_engineering` | 10K3 |
| `features_0dte_options` | IV, Greeks, moneyness, volatility surface | (calc) | `src.feature_engineering` | 10K3 |
| `features_prediction_markets` | Yes/no probabilities, liquidity | (calc) | `automation_scheduler.prediction_market` | 10K4 |
| `model_predictions` | Predicted probabilities / expected returns | Model output | `src.models` | 10K6 |
| `backtest_runs` | Run parameters, timestamps | `experiment_history_store` | `automation_scheduler.experiment_history` | 10K1 |
| `backtest_trades` | Individual simulated trades (sports) | `backtest_result` dicts | `automation_scheduler.experiment_history` | 10K1 |
| `option_backtest_trades` | Simulated 0DTE trades | (future) | `src.backtest` | 10K4 |
| `arbitrage_opportunities` | Detected arb edges | `core.arbitrage` | `automation_scheduler.opportunity` | 10K4 |
| `settlements` | Final results for trade grading | `settlement` fields | `automation_scheduler.settlement` | 10K1 |
| `performance_metrics` | ROI, drawdown, win rate | `summarize_ablation_performance`, backtest results | `automation_scheduler.performance` | 10K1 |

---

## 8. Arbitrage Readiness Map

**Do not implement arbitrage in this phase.** The following outlines where arbitrage will later plug in.

| Component | Where to plug | Later module |
|-----------|---------------|--------------|
| Sports odds arbitrage | After `no_vig_probabilities_n_way` in `quant_engine.py` | `core/arbitrage.py::is_sports_arbitrage`, `implied_sum` |
| Prediction market yes/no parity | After Kalshi/Polymarket quoting | `core/arbitrage.py::prediction_market_yes_no_arb` |
| 0DTE options parity (call/put/underlying) | After option chain quotes are ingested | `core/arbitrage.py::option_parity_arb` |
| Cross‑book / cross‑exchange checks | After multiple provider snapshots are normalised | `core/arbitrage.py::cross_book_arb` |
| Backtest lab integration | During backtest iteration, flag arb opportunities | `automation_scheduler.arbitrage_backtest` |
| Opportunity table | Write to `research_warehouse::arbitrage_opportunities` | `core/arbitrage.py::store_opportunity` |

Likely future functions in `core/arbitrage.py`:
- `implied_sum(probabilities: list[float]) -> float`
- `is_sports_arbitrage(implied_sum: float) -> bool`
- `arbitrage_margin(implied_sum: float) -> float`
- `prediction_market_yes_no_arb(yes_price: float, no_price: float) -> Optional[dict]`
- `optimal_arb_stakes(implied_b: float, implied_a: float, total_stake: float) -> tuple[float, float]`

---

## 9. Test Protection Plan

Every future phase must prove it did not break existing functionality by running:

```bash
pytest tests/
```

Additionally:

- **Source‑text tests** for Streamlit wording must be extended for any new UI strings.
- **Backend tests** must be written for new warehouse schema (when built).
- **No connector text checks** – every new module must include a test that verifies no vendor API call is made (e.g., `assert "Connect Real Vendor API" not in content`).
- **Duplicate‑function regression checks** – where practical, a test can compare function results from two implementations to ensure they remain consistent.
- **Import / compile checks** – all new modules should be importable at the top of a test file without side effects.
- **No accidental Phase 10H24 connector work** – the test suite should assert that no new scraper or API‑call functions have been added.

Required commands after any change:

```bash
python -m pytest tests/ -x -v
python scripts/smoke_test.py
python scripts/ops_check.py
```

---

## 10. No-Duplicate Build Rules

1. **Before adding a function, search for existing equivalent** in the codebase (including `src.core.math_utils`, `quant_engine`, `risk_engine`, `feature_ablation_lab`, `streamlit_dashboard_data`).
2. **If equivalent exists, use/extend canonical function**. Do not create an alternative copy.
3. **If duplicate is unavoidable, document why** in the docstring and in this register.
4. **Every math primitive** (odds conversion, Kelly, EV) should have **one owner** (currently `src.core.math_utils`).
5. **Every storage path** should have **one owner** (currently `automation_scheduler.data_paths`).
6. **Every UI page** should have **one owner** (currently `streamlit_app.py` – do not fragment into multiple UI modules).
7. **Every source registry** should have **one owner** (currently `automation_scheduler.provider_registry`).
8. **Future deletion candidates** must be tracked in section 5 of this report and removal must be coordinated with test updates.

---

## 11. Proposed Next Phases

| Phase | Name | Goal | Est. scope |
|-------|------|------|------------|
| 10K1 | Unified Research Warehouse Foundation | Create `research/market_research.db`, schema for raw sports odds, features, backtest tables. Migrate existing SQLite data. | Medium |
| 10K2 | 0DTE Options Schema Foundation | Define option chain table, quote table, and basic Greeks calculation module. | Medium |
| 10K3 | Frontend Navigation Expansion | Add “Options Lab” / “Arbitrage Lab” tabs to Streamlit main menu (after testing). | Medium |
| 10K4 | Core Arbitrage Engine | Implement `core/arbitrage.py` with sports arb, prediction market yes/no parity. | Medium–large |
| 10K5 | Runtime / CSV Migration Plan | Consolidate bet log, paper ledger, runtime file storage into warehouse backed by SQLite or parquet. | Medium |
| 10K6 | Full Suite Readiness Review | Build integration tests that run all labs, verify warehouse, and ensure no regression. | Large |
| 10K7 | Prediction Testing Phase | Begin evaluating sports and 0DTE prediction performance against backtested benchmarks. | Large |

> **Note**:  
> - Sports prediction testing is deferred until 10K7.  
> - 0DTE prediction testing is deferred until 10K7.  
> - Fama‑French / momentum / macro comparison is deferred until after baseline prediction testing.

---

## 12. File‑by‑File Change Map

| File | Current role | Keep/change/delete later | Reason | Later phase |
|------|--------------|--------------------------|--------|-------------|
| `main.py` | FastAPI application | Keep – minor additions | Central API routing. | 10K2+ |
| `streamlit_app.py` | Operator dashboard | Keep – minor additions | Primary UI. Modify menu later. | 10K3 |
| `quant_engine.py` | Sports math wrappers | Keep – add 0DTE functions | **Merge later** when 0DTE module created. | 10K2 |
| `risk_engine.py` | Stake sizing, risk | Keep – adapt for options | Add delta‑adjusted Kelly. | 10K4 |
| `automation_scheduler/feature_ablation_lab.py` | Feature removal lab | Keep – unchanged | May need schema‑aware variant for options. | 10K4 |
| `automation_scheduler/streamlit_dashboard_data.py` | Dashboard helpers | Keep – add warehouse queries later. | 10K1 |
| `automation_scheduler/data_paths.py` | Path resolution | Keep – extend for warehouse dir. | 10K1 |
| `automation_scheduler/provider_registry.py` | Provider definitions | Keep – add options‑data providers later. | 10K2 |
| `automation_scheduler/kalshi_readonly_adapter.py` | Prediction market stub | Keep – wire later. | 10K4 |
| `automation_scheduler/sharp_sportsbook_adapter.py` | Sportsbook stub | Keep – wire later. | 10K4 |
| `automation_scheduler/historical_odds_sqlite.py` | SQLite ingestion | Keep – migrate to warehouse schema. | 10K1 |
| `automation_scheduler/historical_line_movement.py` | Line movement schema | Keep – unused until connectors. | 10K4+ |
| `src/core/math_utils.py` | Core odds math | Keep – add option math later. | 10K2 |
| `src/api/schemas/*.py` | Pydantic models | Keep – evolve. | Various |
| `tests/test_feature_ablation_lab.py` | Feature ablation tests | Keep. | – |
| `tests/test_streamlit_dashboard_data.py` | Dashboard + UI tests | Keep. | – |
| `PHASE10K0_INSTITUTIONAL_REPO_AUDIT_AND_0DTE_SPECIFICITY_MAP.md` | **This file** | Keep. | – |

---

**End of Phase 10K0 Audit Report**  
*Next phase: 10K1 – Unified Research Warehouse Foundation*


## File-by-File Change Map

This section tracks current file roles, later change intent, and ownership so future phases do not duplicate functionality or delete useful code without tests.

| File | Current role | Keep/change/delete later | Reason | Later phase |
|---|---|---|---|---|
| streamlit_app.py | Current Streamlit operator UI | Keep; expand intentionally later | Protected sports UI and current Feature Ablation Lab flow | 10K3 |
| main.py | Runtime entry / legacy runtime path area | Audit/migrate later | May still contain CSV/runtime storage paths | 10K5 |
| quant_engine.py | Shared betting/math primitives | Keep as canonical unless duplicate is found | EV, Kelly, implied probability, edge logic should have one owner | 10K4 |
| automation_scheduler/feature_ablation_lab.py | Feature Ablation Lab backend | Keep protected | Current sports testing stack depends on it | Protected |
| tests/test_feature_ablation_lab.py | Backend regression tests | Keep | Protects row threshold, included sports, and ablation behavior | Protected |
| tests/test_streamlit_dashboard_data.py | Streamlit source/UI contract tests | Keep | Protects dashboard wording and no-connector restrictions | Protected |

sports prediction testing is deferred.
0DTE prediction testing is deferred.
Do not implement the warehouse in this phase.
Do not implement arbitrage in this phase.
Do not delete duplicates in this phase.

