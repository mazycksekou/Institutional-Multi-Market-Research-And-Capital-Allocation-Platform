# Phase 8C Run Once Artifact Verification

Generated: 2026-06-12T15:20:07

- HEAD: `fddfa8b`
- Git clean at start: `True`

## Safety Environment
- PAPER_TRADING: `1`
- DRY_RUN: `1`
- DISABLE_LIVE_BETS: `1`
- ACTION_API_KEY: `SET`
- ODDS_API_KEY: `MISSING`
- THE_ODDS_API_KEY: `MISSING`
- DEEPSEEK_API_KEY: `MISSING`

## Run Once Response Summary
- status_code: `200`
- ok: `True`
- status: `dry_run_complete`
- error: `None`
- detail: `None`
- run_id: `run_ab397f4ebf3b`
- report_id: `run_ab397f4ebf3b`

## Count Fields
| Field | Value |
|---|---:|
| `records_received` | `100` |
| `records_valid` | `100` |
| `records_rejected` | `0` |
| `candidates_created` | `100` |
| `paper_decisions_count` | `1100` |
| `paper_decisions_written` | `400` |
| `review_required_count` | `0` |
| `review_queue_items_written` | `400` |
| `watch_recheck_count` | `100` |
| `kalshi_records_received` | `100` |
| `kalshi_records_valid` | `100` |
| `kalshi_records_rejected` | `0` |
| `kalshi_candidates_created` | `100` |
| `kalshi_watch_items_created` | `100` |
| `sharp_records_received` | `0` |
| `sharp_records_valid` | `0` |
| `sharp_records_rejected` | `0` |
| `sharp_candidates_created` | `0` |

## Artifact Path Verification
| Key | Exists | Kind | Size Bytes | Line Count | Path |
|---|---:|---|---:|---:|---|
| `report_path` | `True` | `file` | `3354597` | `84657` | `C:\Users\user\betting-stock-api-code-integration\betting stock api code intergration\data\reports\scheduler_run_run_ab397f4ebf3b.json` |
| `paper_ledger_write_path` | `False` | `not_found` | `None` | `None` | `paper_ledger\latest.json` |
| `review_queue_write_path` | `False` | `not_found` | `None` | `None` | `review_queue\latest.json` |

## Artifact Samples
### report_path
```json
[
  "{",
  "  \"auto_bet_enabled\": false,",
  "  \"auto_execution_enabled\": false,",
  "  \"auto_trade_enabled\": false,",
  "  \"dry_run\": true,"
]
```
### paper_ledger_write_path
```json
null
```
### review_queue_write_path
```json
null
```

## Phase 8C Result
OVERALL_OK: `True`
Run-once artifacts and returned paths are internally consistent in dry-run/paper-safe mode.
