param(
    [switch]$Execute,
    [switch]$DryRun,
    [switch]$AtTenPmSetup
)

# Example dry run:
# powershell -ExecutionPolicy Bypass -File .\scripts\run_daily_data_hygiene.ps1 -DryRun

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $RepoRoot

$PythonArgs = @(
    'scripts/daily_data_hygiene.py',
    '--input-dir', 'data',
    '--output-dir', '.',
    '--environment', 'local',
    '--source', 'local-data',
    '--market', 'raw-generated',
    '--trading-date', 'auto',
    '--batch-prefix', 'daily-hygiene',
    '--report-dir', 'reports/daily_data_hygiene',
    '--local-time', '22:00',
    '--include-pattern', '*.json',
    '--include-pattern', '*.jsonl',
    '--include-pattern', '*.csv'
)

if ($Execute) {
    $PythonArgs += @('--execute', '--upload', '--verify', '--cleanup', '--allow-delete-local-raw')
} elseif ($DryRun) {
    $PythonArgs += '--dry-run'
}

if ($AtTenPmSetup) {
    $TaskCommand = "schtasks /Create /TN `"BettingRepoDailyDataHygiene`" /SC DAILY /ST 22:00 /TR `"powershell.exe -ExecutionPolicy Bypass -File '$RepoRoot\scripts\run_daily_data_hygiene.ps1' -Execute`" /F"
    Write-Host $TaskCommand
    exit 0
}

python @PythonArgs
exit $LASTEXITCODE
