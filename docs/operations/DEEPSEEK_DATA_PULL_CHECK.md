# External Model Data Pull Check

This wrapper gives the external model review workflow a safe way to inspect compact reports and identify prediction-market outcome candidates without changing production state.

The legacy script name remains DeepSeek-named for compatibility with existing operational commands.

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

Tiny prediction-market settlement check:

```powershell
.\scripts\deepseek_data_pull_check.ps1 -DryRun -PredictionMarketOutcomeCheck -AllowTinyProviderCalls -MaxProviderCalls 3 -MaxRecords 5 -NoDeepSeek
```

## What It Does

The script resolves the project root, activates `.venv` when present, sets `APP_BASE_URL` to the Render app when unset, then runs:

- `.\scripts\check_local.ps1`
- `.\scripts\check_render.ps1`
- `.\scripts\check_data_availability_tiers.ps1`

It then writes compact check reports. Compact report persistence is allowed; outcome persistence, source enabling, deploys, imports, migrations, and execution actions are blocked.

## Provider Calls

Defaults:

- `DryRun=true`
- `AllowTinyProviderCalls=false`
- `MaxProviderCalls=0`
- `MaxRecords=0`

Tiny provider mode requires `-AllowTinyProviderCalls`. The wrapper hard caps `MaxProviderCalls` at 3 and `MaxRecords` at 5. When combined with `-PredictionMarketOutcomeCheck`, the wrapper may use the existing Kalshi read-only adapter and settlement discovery logic to check a tiny set of pending prediction-market records.

The check stops on the first rate limit or provider error. If the existing read-only provider configuration is disabled, missing credentials, or live reads are not enabled, the wrapper records the block and makes no external provider call.

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

Provider settlement-check report fields include:

- `env_file_present`
- `env_loaded`
- `env_loader`
- `readiness_source`
- `readiness_checker_consistent_with_wrapper`
- `missing_env_names`
- `tiny_provider_mode_requested`
- `tiny_provider_mode_allowed`
- `provider_readiness_status`
- `provider_readiness_blockers`
- `provider_config_present`
- `live_read_enabled`
- `credentials_present`
- `pending_records_seen`
- `provider_eligible_records`
- `provider_ineligible_records`
- `provider_ineligible_reason_counts`
- `missing_identifier_count`
- `missing_ticker_count`
- `missing_market_id_count`
- `already_settled_or_closed_without_result_count`
- `local_explicit_outcome_count`
- `provider_selection_limit`
- `provider_selected_count`
- `provider_selection_blocker`
- `why_provider_calls_zero`
- `provider_calls_attempted`
- `provider_calls_succeeded`
- `provider_calls_failed`
- `markets_checked_with_provider`
- `explicit_outcomes_found`
- `rejected_count`
- `rejection_reasons`
- `rate_limited`
- `persisted=false`
- `dry_run=true`

Zero-call reasons are compact safe labels:

- `provider_not_ready`
- `live_reads_disabled`
- `credentials_missing`
- `no_pending_records`
- `no_provider_eligible_records`
- `missing_required_identifiers`
- `all_records_rejected_before_provider_check`
- `call_budget_zero`
- `tiny_provider_mode_not_requested`
- `unknown_diagnostic_gap`

## Report Paths

Check reports:

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
