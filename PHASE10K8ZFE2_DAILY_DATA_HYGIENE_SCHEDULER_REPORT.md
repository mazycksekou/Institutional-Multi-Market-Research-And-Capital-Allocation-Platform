# PHASE10K8ZFE2 Daily Data Hygiene Scheduler

## Executive Summary
10K8ZFE2 adds a deterministic daily cleanup workflow so generated files can build during the day and then be archived, verified, and cleaned up around 10 PM. The cleanup path stays gated behind explicit flags and the existing R2 archive pipeline.
10 PM Verified Cleanup

This phase is not an AI phase, not a backtest phase, and not a live trading phase.

## Current HEAD
Current HEAD before patch: `cf74655e56c6a11d6f6ac782f491640d9a8d693e`

## Purpose
Create a daily hygiene scheduler that reduces cleanup alerts by batching generated data into a predictable verified cleanup window.

## Scope
- Daily inventory first
- Archive before delete
- Use the existing R2 archive pipeline
- Add a PowerShell runner
- Document Windows Task Scheduler setup
- Add tests and a report

## Non-Goals
- no AI integration
- no ML training
- no backtest runner
- no broker execution
- no real trade execution
- no scraper actions
- no blind delete

## Why This Phase Exists
Generated JSON files can appear under data/ during the day. The scheduler lets generated files build during the day and then runs cleanup around 10 PM in a deterministic way.

## Daily Hygiene Contract
let generated files build during the day
run cleanup around 10 PM
archive before delete
manifest-listed files only
no blind delete

## 10 PM Schedule Policy
The local-time hint defaults to `22:00` and is documented, but it is not hardcoded into deletion logic.

## R2 Verification Policy
Local deletion is only allowed after `upload_status` is `uploaded`, `verification_status` is `verified`, `deletion_eligible` is true, and the manifest marks the batch as eligible.

## Deletion Safety Policy
The cleanup flow deletes only manifest-listed files under the approved input directory.
`deletion_performed` stays false until cleanup runs.

- markdown files preserved
- DB files preserved
- source code preserved
- tests/fixtures preserved
- tracked files preserved
- manifests preserved
- archives preserved
- files outside data/ preserved
- no credentials committed
- no secrets printed
- R2 credentials come from environment variables only

## Dry-Run Behavior
dry-run by default. No upload, verification, or deletion occurs unless execute mode is explicitly selected.

## Execute Behavior
execute requires explicit flag. Real cleanup requires `--execute --upload --verify --cleanup --allow-delete-local-raw`.

## PowerShell Runner
The repository includes `scripts/run_daily_data_hygiene.ps1` to launch the scheduler from the repo root.

## Windows Task Scheduler Setup
Manual setup is documented. The scheduler command is:

```powershell
schtasks /Create /TN "BettingRepoDailyDataHygiene" /SC DAILY /ST 22:00 /TR "powershell.exe -ExecutionPolicy Bypass -File '<repo>\scripts\run_daily_data_hygiene.ps1' -Execute" /F
```

## Agent Policy
agent is advisory only
agent does not directly delete files

## Files Changed
- `scripts/daily_data_hygiene.py`
- `scripts/run_daily_data_hygiene.ps1`
- `docs/DAILY_DATA_HYGIENE_SCHEDULER.md`
- `PHASE10K8ZFE2_DAILY_DATA_HYGIENE_SCHEDULER_REPORT.md`
- `tests/test_phase10k8zfe2_daily_data_hygiene_scheduler.py`

## Tests Run
- `pytest tests/test_phase10k8zfe2_daily_data_hygiene_scheduler.py -q`
- `pytest tests/test_phase10k8zfe1_universal_product_language_alignment.py -q`
- `pytest tests/test_phase10k8zfe_duplicate_code_evidence_scan.py -q`
- `pytest tests/test_phase10k8zf9d_final_data_inventory_reconciliation.py -q`
- `pytest tests/test_phase10k8zf9c_headerless_csv_final_deletion.py -q`
- `pytest tests/test_phase10k8zf9b_batch_safe_remaining_transfer.py -q`
- `pytest tests/test_phase10k8zf9_full_r2_transfer_report.py -q`
- `pytest tests/test_phase10k8zf8_r2_transfer_proof_report.py -q`
- `pytest tests/test_phase10k8zf7_r2_archive_pipeline.py -q`

## Acceptance Results
- daily hygiene script added: yes
- PowerShell runner added: yes
- Task Scheduler docs added: yes
- dry-run by default: yes
- execute requires explicit flag: yes
- archive before delete: yes
- manifest-listed deletion only: yes
- markdown preserved: yes
- DB preserved: yes
- tracked files preserved: yes
- agent advisory only: yes
- no AI integration: yes
- no ML training: yes
- no backtest runner: yes
- no broker execution: yes
- no real trade execution: yes
- no scraper actions: yes

## Next Phase Recommendation
Proceed to 10K8ZFF Canonical Owner Decision Report.
