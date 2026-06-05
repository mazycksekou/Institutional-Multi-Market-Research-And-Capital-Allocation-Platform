# Kalshi Cron Check Report

- `branch_name`: `ncaaf-final-oxylabs-source-policy-free-open-exhaustion`
- `base_commit_hash`: `1840afeb5cbcb976502f6a417dc312199295b95c`
- `final_verdict`: `KALSHI_CRON_HEALTHY_BUT_NO_RECENT_RUN_EVIDENCE`

## Cron Configuration

| Field | Value |
| --- | --- |
| `cron_found` | `true` |
| `cron_source_file` | `docs/RENDER_PERSISTENT_STORAGE_AND_CRON.md` |
| `cron_name` | `Render Cron Job (documented)` |
| `cron_schedule` | `*/30 * * * *` |
| `cron_enabled` | `documented_expected_not_machine_verifiable` |
| `cron_target` | `POST /api/automation/calibration-collector/scheduled-run` |
| `target_daily_new_contracts` | `100` |
| `hard_cap_daily_new_contracts` | `250` |
| `max_new_contracts_per_cycle` | `25` |
| `max_markets_scanned` | `5000` |
| `adaptive_throttle` | `true` |

The repo does not contain a machine-managed Render cron service definition in `render.yaml`. The schedule is documented, but direct runtime proof requires Render Cron Job history or a persisted `/var/data/collector_scheduler/latest_cycle.json` artifact from the protected scheduled endpoint.

## Live Read-Only Validation

| Check | Result |
| --- | --- |
| Kalshi health status | `read_only_ready` |
| Snapshot status | `live_snapshot_complete` |
| Run-once status | `dry_run_complete` |
| Review queue status | `ok` |
| Kalshi records received | `100` |
| Kalshi records valid | `100` |
| Kalshi records rejected | `0` |
| Kalshi candidates created | `100` |
| Missing prices count | `0` |
| Flagged low-liquidity count | `100` |
| Review queue Kalshi candidates | `200` |
| Review queue prediction-market count | `200` |
| Review queue review-only count | `250` |
| Execution allowed count | `0` |

The required live snapshot probe returned `dry_run=false` and `/var/data/data_sources/provider_payload_samples/kalshi_prediction_market_snapshot.json` before the local fix, which showed the endpoint ignored the dry-run body. The endpoint is now patched locally to require `dry_run=false` and `write_snapshot=true` before writing a snapshot.

## Safety Flags

| Flag | Value |
| --- | --- |
| `provider_write` | `false` |
| `execution_allowed` | `false` |
| `kalshi_order_execution_enabled` | `false` |
| `auto_execution_enabled` | `false` |
| `actual_orders_submitted` | `0` |
| `actual_bets_submitted` | `0` |
| `raw_payload_included` | `false` |
| `raw_html_persisted` | `false` |
| `secrets_included` | `false` |
| `compact_response_preserved` | `true` |

Safety scan passed with no blocking generated-report leak, no `kalshi_order_execution_enabled=true`, no committed `.env`, and no concrete Kalshi secret values found. Non-blocking findings were expected code/docs/test references, fake unit-test key strings, tracked `.env.example`, and an untracked local `.env`.

## Tests

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_automation_scheduler_endpoints.py -q` | `26 passed` |
| `python -m pytest tests/test_collector_scheduled_runner.py -q` | `8 passed` |
| `python -m pytest tests/test_kalshi_readonly_adapter.py -q` | `14 passed` |
| `python -m pytest tests/test_kalshi_market_provider.py -q` | `6 passed` |
| `python -m pytest tests/test_scheduler_runner.py -q` | `5 passed` |
| `python -m pytest tests/test_review_queue.py -q` | `7 passed` |
| `python -m pytest tests/test_response_compactor.py -q` | `22 passed` |
| `python -m pytest tests/test_kalshi_monitor.py -q` | `1 passed` |
| `python -m pytest tests/test_kalshi_scoring.py -q` | `5 passed` |
| `python -m compileall automation_scheduler scripts tests` | `passed` |

## Issues And Fixes

Issues found:

- Scheduled Kalshi collector defaults and Render cron documentation had drifted from expected caps `100/250/25/5000`.
- Live Kalshi snapshot endpoint ignored the `dry_run` body and returned a persisted snapshot path before the local fix.
- Direct cron runtime evidence is insufficient without Render Cron Job history or a persisted collector `latest_cycle.json`.

Fixes applied:

- Updated scheduled collector, calibration collector, and API request defaults to `target_daily_new_contracts=100`, `hard_cap_daily_new_contracts=250`, `max_new_contracts_per_cycle=25`, `max_markets_scanned=5000`, `adaptive_throttle=true`.
- Updated Render cron documentation and scheduled-run tests to the expected caps.
- Patched `POST /api/providers/kalshi/snapshot` to honor `dry_run/write_snapshot` and avoid writing snapshots for `dry_run=true`.
- Added endpoint regression coverage for Kalshi snapshot dry-run no-write behavior.
