# Daily Data Hygiene Scheduler

This repository uses a deterministic daily data hygiene workflow to let generated files build during the day and run cleanup around 10 PM.

## Workflow

- Inspect `data/` first.
- Archive eligible generated JSON, JSONL, and CSV files.
- Verify the R2 object.
- Delete only manifest-listed files after verification.
- Preserve markdown files, DB files, source code, tests/fixtures, manifests, archives, and tracked files.

## Default behavior

- Dry-run by default.
- Execute requires explicit flags.
- Archive before delete.
- No blind delete.

## PowerShell runner

Run from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_daily_data_hygiene.ps1 -Execute
```

## Windows Task Scheduler

Register manually only when you are ready:

```powershell
schtasks /Create /TN "BettingRepoDailyDataHygiene" /SC DAILY /ST 22:00 /TR "powershell.exe -ExecutionPolicy Bypass -File '<repo>\scripts\run_daily_data_hygiene.ps1' -Execute" /F
```

This command is documented for manual use. The repository does not auto-register the task in tests or normal runs.

## Safety

- upload_status must be `uploaded`
- verification_status must be `verified`
- deletion_eligible must be true
- deletion_performed must remain false until cleanup runs
- manifest-listed files only

