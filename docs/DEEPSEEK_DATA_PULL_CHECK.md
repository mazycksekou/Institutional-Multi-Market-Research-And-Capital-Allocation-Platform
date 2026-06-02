# DeepSeek Data Pull Check

This wrapper gives DeepSeek a safe way to inspect compact reports and identify prediction-market outcome candidates without changing production state.

## Manual Commands

Default dry run:

```powershell
.\scripts\deepseek_data_pull_check.ps1 -DryRun
```

Prediction-market outcome candidate check:

```powershell
.\scripts\deepseek_data_pull_check.ps1 -DryRun -PredictionMarketOutcomeCheck
```

Tiny provider mode is gated and capped for future adapter work:

```powershell
.\scripts\deepseek_data_pull_check.ps1 -DryRun -AllowTinyProviderCalls -MaxProviderCalls 3 -MaxRecords 5
```

## What It Does

The script resolves the project root, activates `.venv` when present, sets `APP_BASE_URL` to the Render app when unset, then runs:

- `.\scripts\check_local.ps1`
- `.\scripts\check_render.ps1`
- `.\scripts\check_data_availability_tiers.ps1`

It then writes compact DeepSeek check reports. Compact report persistence is allowed; outcome persistence, source enabling, deploys, imports, migrations, and execution actions are blocked.

## Provider Calls

Defaults:

- `DryRun=true`
- `AllowTinyProviderCalls=false`
- `MaxProviderCalls=0`
- `MaxRecords=0`

Tiny provider mode requires `-AllowTinyProviderCalls`. The wrapper hard caps `MaxProviderCalls` at 3 and `MaxRecords` at 5. Step 1 does not execute provider calls; it only records whether the gate would allow a future tiny adapter sample.

Paid and budget-gated sources remain blocked by default. No source is enabled by this wrapper.

## Outcome Candidate Rules

Accepted evidence:

- explicit `result=yes`
- explicit `result=no`
- `settled_yes`
- `settled_no`
- `final_outcome`
- provider-normalized explicit result fields that already resolve to yes or no

Rejected evidence:

- price-only inference
- bid/ask inference
- last-trade inference
- market closed but no explicit result
- ambiguous result
- missing result

Candidate reports are review-only. They never persist outcomes.

## Report Paths

DeepSeek check reports:

- `data/deepseek_data_checks/latest.json`
- `data/deepseek_data_checks/latest.md`
- `data/deepseek_data_checks/items/<run_id>.json`
- `data/deepseek_data_checks/items/<run_id>.md`
- `data/deepseek_data_checks/daily/<YYYY-MM-DD>.json`
- `data/deepseek_data_checks/daily/<YYYY-MM-DD>.md`

Prediction-market candidate reports:

- `data/prediction_market_outcome_candidates/latest.json`
- `data/prediction_market_outcome_candidates/latest.md`
- `data/prediction_market_outcome_candidates/items/<run_id>.json`
- `data/prediction_market_outcome_candidates/items/<run_id>.md`
- `data/prediction_market_outcome_candidates/daily/<YYYY-MM-DD>.json`
- `data/prediction_market_outcome_candidates/daily/<YYYY-MM-DD>.md`

## Safety Invariants

The report must keep:

```text
provider_write=false
execution_allowed=false
execution_allowed_count=0
live_execution_enabled=false
auto_execution_enabled=false
kalshi_order_execution_enabled=false
sportsbook_bet_execution_enabled=false
broker_order_execution_enabled=false
crypto_trade_execution_enabled=false
stock_trade_execution_enabled=false
actual_orders_submitted=0
actual_bets_submitted=0
actual_trades_submitted=0
actual_crypto_swaps_submitted=0
raw_payload_included=false
secrets_included=false
```
