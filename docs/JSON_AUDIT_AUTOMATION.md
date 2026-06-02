# JSON Audit Automation Pack

This pack automates the read-only JSON audit workflow for the betting-stock-api project.

## Files

- `scripts/analyze_json_data.py` — scans JSON/JSONL and writes audit reports.
- `scripts/review_json_audit_with_deepseek.ps1` — manually sends the report to DeepSeek.
- `scripts/run_json_audit_pipeline.ps1` — runs audit + optional DeepSeek review.
- `scripts/install_json_audit_scheduled_task.ps1` — installs a Windows Scheduled Task.
- `scripts/uninstall_json_audit_scheduled_task.ps1` — removes the scheduled task.

## Install

Copy the `scripts` folder into:

`C:\Users\user\betting-stock-api-code-integration\betting stock api code intergration`

## Run once

```powershell
cd "C:\Users\user\betting-stock-api-code-integration\betting stock api code intergration"
powershell -ExecutionPolicy Bypass -File scripts\run_json_audit_pipeline.ps1 -OpenReport
```

## Run once without DeepSeek

```powershell
cd "C:\Users\user\betting-stock-api-code-integration\betting stock api code intergration"
powershell -ExecutionPolicy Bypass -File scripts\run_json_audit_pipeline.ps1 -NoDeepSeek -OpenReport
```

## Install daily automation at 9 PM

```powershell
cd "C:\Users\user\betting-stock-api-code-integration\betting stock api code intergration"
powershell -ExecutionPolicy Bypass -File scripts\install_json_audit_scheduled_task.ps1 -Frequency Daily -Time 21:00
```

## Install hourly automation without DeepSeek

```powershell
cd "C:\Users\user\betting-stock-api-code-integration\betting stock api code intergration"
powershell -ExecutionPolicy Bypass -File scripts\install_json_audit_scheduled_task.ps1 -Frequency Hourly -NoDeepSeek
```

## Run scheduled task manually

```powershell
Start-ScheduledTask -TaskName "BettingStockApiJsonAudit"
```

## Open report

```powershell
notepad reports\json_data_audit\latest_summary.md
```

If DeepSeek review runs successfully, open:

```powershell
notepad reports\json_data_audit\latest_deepseek_review.md
```

## Remove automation

```powershell
cd "C:\Users\user\betting-stock-api-code-integration\betting stock api code intergration"
powershell -ExecutionPolicy Bypass -File scripts\uninstall_json_audit_scheduled_task.ps1
```

## Safety

The audit is read-only against project data. It writes reports under:

`reports\json_data_audit\`

It does not call live providers, place bets/trades/orders, persist production outcomes, migrate data, or print environment secrets. The optional DeepSeek review sends the compact markdown report, not raw JSON files.
