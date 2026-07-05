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

## Canonical Runner

Run from the repo root with the portable Python implementation:

```bash
python scripts/daily_data_hygiene.py --dry-run
```

For an execution run:

```bash
python scripts/daily_data_hygiene.py --execute --upload --verify --cleanup --allow-delete-local-raw
```

## PowerShell runner

The PowerShell wrapper remains available as a Windows convenience layer:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_daily_data_hygiene.ps1 -Execute
```

## Windows Task Scheduler

Register manually only when you are ready:

```powershell
schtasks /Create /TN "BettingRepoDailyDataHygiene" /SC DAILY /ST 22:00 /TR "python '<repo>\scripts\daily_data_hygiene.py' --execute --upload --verify --cleanup --allow-delete-local-raw" /F
```

This command is documented for manual use on Windows. The repository does not auto-register the task in tests or normal runs.

## macOS/Linux cron

```cron
0 22 * * * cd <repo> && python scripts/daily_data_hygiene.py --execute --upload --verify --cleanup --allow-delete-local-raw
```

## GitHub Actions scheduled workflow

```yaml
on:
  schedule:
    - cron: "0 22 * * *"
jobs:
  daily-data-hygiene:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python scripts/daily_data_hygiene.py --execute --upload --verify --cleanup --allow-delete-local-raw
```

## Render scheduled/background job

```yaml
startCommand: python scripts/daily_data_hygiene.py --execute --upload --verify --cleanup --allow-delete-local-raw
```

## Safety

- upload_status must be `uploaded`
- verification_status must be `verified`
- deletion_eligible must be true
- deletion_performed must remain false until cleanup runs
- manifest-listed files only
