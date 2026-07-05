# 0DTE Data Field + Formula Coverage Audit

## Executive Summary
This 0DTE Data Field + Formula Coverage Audit for `10K8ZA` reviews the current paper-only 0DTE runway under the frozen controlled prediction-testing stack.

`0DTE is the primary active trading lane`, but the repo remains in `controlled paper-only prediction testing`, `local fixture-backed testing`, `readiness only`, and `review-only` mode. The audit confirms a strong baseline for `bid`, `ask`, `mid`, `mark`, `last_price`, the core Greeks, expiration timing, underlying context, and paper evaluation outputs, but it also shows material gaps in institutional footprint fields, GEX fields, volume profile fields, strategy-specific fields, and several 0DTE formula helpers.

Material gaps exist. Recommend `10K8ZB 0DTE Field + Formula Gap Patch`.

## Existing Owner Review
The existing owner rule was preserved. No duplicate owner created.

## 0DTE Field Coverage Audit
The current 0DTE field baseline is anchored in `automation_scheduler/model_data_field_catalog.py` and `automation_scheduler/zero_dte_fixture_template.py`.

### Core Options Chain Fields
`present`

The current 0DTE template and catalog cover:

- `bid`
- `ask`
- `mid`
- `mark`
- `last_price`
- `implied_volatility`
- `delta`
- `gamma`
- `theta`
- `vega`
- `volume`
- `open_interest`
- `underlying_symbol`
- `underlying_price`
- `trade_date`
- `timestamp`
- `expiration_date`
- `minutes_to_expiration`
- `strike`
- `option_type`
- `call_put`
- `moneyness`
- `spread`
- `spread_percent`
- `premium`

### Greeks and Expiration Risk Fields
`present`

The current template already carries the core Greeks and expiration timing fields used by the dedicated 0DTE paper fixture and review stack.

### Liquidity and Slippage Fields
`present_as_field_only` for the current 0DTE liquidity boundary, but `missing_candidate` for deeper execution-quality coverage.

Currently present:

- `spread`
- `spread_percent`
- `liquidity_score`

Still missing for a professional execution-quality audit surface:

- `quoted_depth`
- `slippage_estimate`

### Volume and Open Interest Fields
`present`

The current 0DTE audit surface already covers `volume` and `open_interest`.

### Underlying Intraday Context Fields
`present`

The current 0DTE catalog already includes:

- `underlying_open`
- `underlying_high`
- `underlying_low`
- `underlying_close`
- `underlying_volume`
- `vwap`
- `ema_12`
- `ema_26`
- `macd`
- `macd_signal_line`
- `macd_histogram`
- `rsi`
- `adx`
- `support_level`
- `resistance_level`
- `trend_line`
- `breakout_level`
- `breakdown_level`

### Institutional Footprint Fields
`missing_candidate`

These are not yet covered as dedicated 0DTE fields:

- `bid_size`
- `ask_size`
- `quoted_depth`
- `liquidity_score`

`liquidity_score` exists as a broader catalog concept, but the institutional footprint view still needs a dedicated 0DTE audit path before it can be treated as execution-grade evidence.

### Gamma Exposure / GEX Fields
`missing_candidate`

Not yet present in the frozen 0DTE surface:

- `net_gex`
- `strike_gex`
- `call_gex`
- `put_gex`
- `gamma_flip_level`
- `gex_regime`

### Volume Profile Fields
`missing_candidate`

The repo does not yet expose a dedicated `0DTE volume profile` layer:

- `strike_volume_profile`
- `volume_profile_peak_strike`

### Strategy-Specific Fields
`missing_candidate`

The current controlled stack does not yet expose a strategy taxonomy for 0DTE:

- `strategy_type`
- `iron_condor`
- `iron_butterfly`
- `vertical_credit_spread`
- `long_straddle`
- `long_strangle`
- `single_call_put_scalp`

### Macro Event Context Fields
`present_as_field_only` for macro context, but `missing_candidate` for specific event-day flags.

Currently present in the frozen 0DTE surface:

- `macro_context`
- `fed_event_context`
- `market_regime`

Still missing as dedicated audit fields:

- `cpi_day`
- `fomc_day`
- `jobs_day`
- `fed_speaker_day`

### Paper Evaluation Output Fields
`present`

The current paper evaluation layer already exposes:

- `paper_edge`
- `paper_ev`
- `paper_stake_units`
- `paper_result`
- `paper_arbitrage_percentage`
- `total_paper_ev`
- `total_paper_stake_units`
- `total_paper_arbitrage_percentage`
- `average_paper_arbitrage_percentage`

## Formula Coverage Audit
`present_as_formula` for paper-only review math; `missing_candidate` for formula helpers that should be added later if the audit expands into execution-quality coverage.

Already present as source-owned formulas or helpers:

- `implied_probability_from_american_odds`
- `paper_edge = model_probability - implied_probability`
- `paper_ev = paper_edge * premium`

Still missing as explicit helper coverage in the current frozen 0DTE audit surface:

- `spread = ask - bid`
- `mid = (bid + ask) / 2`
- `spread_percent = spread / mid`
- `volume_open_interest_ratio = volume / open_interest`
- `estimated_slippage`
- `moneyness_percent`

## Formula Owner Review
`EV`, `edge`, `Kelly`, and the other universal math owners remain in `quant_engine.py` by design.

`paper_edge` and `paper_ev` are present as paper-only review outputs in the 0DTE fixture and evaluation stack, but they are not a reason to move universal math ownership.

## Unsupported Claim Cleanup
The audit keeps the language controlled:

- `no guaranteed profit language`
- `no assured profit language`
- `unsupported 8-figure certainty claims excluded`
- `market-maker trapped language softened`
- `pinning is not guaranteed`

These claims should remain softened or excluded from any later dashboard copy.

## Keep / Soften / Exclude Decision Table

| Item | Status | Audit Decision |
| --- | --- | --- |
| `bid`, `ask`, `mid`, `mark`, `last_price`, `implied_volatility`, `delta`, `gamma`, `theta`, `vega`, `volume`, `open_interest`, `underlying_symbol`, `underlying_price`, `trade_date`, `timestamp`, `expiration_date`, `minutes_to_expiration`, `strike`, `option_type`, `call_put`, `moneyness`, `spread`, `spread_percent`, `premium` | `present` | Keep |
| `support_level`, `resistance_level`, `trend_line`, `breakout_level`, `breakdown_level` | `present_as_field_only` | Keep |
| `paper_edge = model_probability - implied_probability`, `paper_ev = paper_edge * premium`, `implied_probability_from_american_odds` | `present_as_formula` | Keep |
| `spread = ask - bid`, `mid = (bid + ask) / 2`, `spread_percent = spread / mid`, `volume_open_interest_ratio = volume / open_interest`, `estimated_slippage`, `moneyness_percent` | `missing_candidate` | Add later |
| `bid_size`, `ask_size`, `quoted_depth`, `liquidity_score` | `missing_candidate` | Add later |
| `net_gex`, `strike_gex`, `call_gex`, `put_gex`, `gamma_flip_level`, `gex_regime` | `missing_candidate` | Add later |
| `strike_volume_profile`, `volume_profile_peak_strike` | `missing_candidate` | Add later |
| `strategy_type`, `iron_condor`, `iron_butterfly`, `vertical_credit_spread`, `long_straddle`, `long_strangle`, `single_call_put_scalp` | `missing_candidate` | Add later |
| `cpi_day`, `fomc_day`, `jobs_day`, `fed_speaker_day` | `missing_candidate` | Add later |
| `guaranteed profit language`, `assured profit language`, `unsupported 8-figure certainty claims excluded` | `intentionally_excluded` | Keep out |
| `market-maker trapped language`, `pinning is not guaranteed` | `needs_next_phase_review` | Soften only |

## Missing Field Candidates
The missing field candidates for the next patch phase are:

- `volume_open_interest_ratio`
- `bid_size`
- `ask_size`
- `quoted_depth`
- `liquidity_score`
- `slippage_estimate`
- `net_gex`
- `strike_gex`
- `call_gex`
- `put_gex`
- `gamma_flip_level`
- `gex_regime`
- `strike_volume_profile`
- `volume_profile_peak_strike`
- `strategy_type`
- `iron_condor`
- `iron_butterfly`
- `vertical_credit_spread`
- `long_straddle`
- `long_strangle`
- `single_call_put_scalp`
- `max_profit`
- `max_loss`
- `breakeven_low`
- `breakeven_high`
- `risk_reward_ratio`
- `cpi_day`
- `fomc_day`
- `jobs_day`
- `fed_speaker_day`
- `moneyness_percent`

## Missing Formula Candidates
The missing formula candidates for the next patch phase are:

- `spread = ask - bid`
- `mid = (bid + ask) / 2`
- `spread_percent = spread / mid`
- `volume_open_interest_ratio = volume / open_interest`
- `estimated_slippage`
- `moneyness_percent`

## Do Not Add Yet Boundary
Do not add new formulas yet.
Do not add new production behavior yet.
Do not add live connectors.
Do not add broker execution.
Do not add real trade execution.
Do not add API calls.
Do not write database rows.
Do not add file upload.
Do not add CSV parsing.
Do not add frontend page files.
Do not create duplicate owners.

Boundary strings preserved exactly:

- no broker execution
- no real trade execution
- no live connectors
- no API calls
- no database writes
- no file upload
- no CSV parsing
- no frontend page files
- no guaranteed profit language
- no assured profit language
- unsupported 8-figure certainty claims excluded

## Paper-Only Boundary
The audit stays paper-only.

## Readiness-Only Boundary
The audit stays readiness only and review-only.

## Broker Boundary
No broker execution is added.

## Connector Boundary
No live connectors are added.

## API Boundary
No API calls are added.

## Database Write Boundary
No database writes are added.

## Test Plan
The audit test checks the frozen 10K8 stack, the 0DTE template and evaluation helpers, the technical signal boundary, and the presence of the missing-field and missing-formula candidates.

## Next Phase Recommendation
Material gaps exist. Proceed to `10K8ZB 0DTE Field + Formula Gap Patch`.

implementation reviewed in 10K8ZA
