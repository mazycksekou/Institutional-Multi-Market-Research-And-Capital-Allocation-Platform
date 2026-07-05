param(
    [string]$ProjectPath = (Split-Path -Parent $PSScriptRoot),
    [ValidateSet("Daily", "Hourly")]
    [string]$Frequency = "Daily",
    [string]$Time = "21:00",
    [string]$TaskName = "BettingStockApiJsonAudit",
    [switch]$NoDeepSeek
)

$ErrorActionPreference = "Stop"

$pythonArgs = @(
    "scripts/install_json_audit_scheduled_task.py",
    "--project-path", $ProjectPath,
    "--frequency", $Frequency,
    "--time", $Time,
    "--task-name", $TaskName
)
if ($NoDeepSeek) {
    $pythonArgs += "--no-deepseek"
}
python @pythonArgs
exit $LASTEXITCODE
