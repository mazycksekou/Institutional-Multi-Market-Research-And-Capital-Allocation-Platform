param(
    [string]$ProjectPath = "C:\Users\user\betting-stock-api-code-integration\betting stock api code intergration",
    [ValidateSet("Daily", "Hourly")]
    [string]$Frequency = "Daily",
    [string]$Time = "21:00",
    [string]$TaskName = "BettingStockApiJsonAudit",
    [switch]$NoDeepSeek
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $ProjectPath)) {
    Write-Host "Project path not found: $ProjectPath"
    exit 1
}

$PipelineScript = Join-Path $ProjectPath "scripts\run_json_audit_pipeline.ps1"
if (!(Test-Path $PipelineScript)) {
    Write-Host "Pipeline script not found: $PipelineScript"
    Write-Host "Copy this pack's scripts folder into the project root first."
    exit 1
}

$Argument = "-NoProfile -ExecutionPolicy Bypass -File `"$PipelineScript`" -ProjectPath `"$ProjectPath`""
if ($NoDeepSeek) {
    $Argument += " -NoDeepSeek"
}

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $Argument -WorkingDirectory $ProjectPath

if ($Frequency -eq "Hourly") {
    $Start = (Get-Date).AddMinutes(5)
    $Trigger = New-ScheduledTaskTrigger -Once -At $Start -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 3650)
}
else {
    $Trigger = New-ScheduledTaskTrigger -Daily -At $Time
}

$Settings = New-ScheduledTaskSettingsSet -Compatibility Win8 -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Read-only JSON audit and optional DeepSeek review for betting-stock-api." -Force | Out-Null

Write-Host "Scheduled task installed: $TaskName"
Write-Host "Frequency: $Frequency"
if ($Frequency -eq "Daily") { Write-Host "Time: $Time" }
Write-Host "Project: $ProjectPath"
Write-Host "Run now with: Start-ScheduledTask -TaskName `"$TaskName`""
Write-Host "Check task with: Get-ScheduledTask -TaskName `"$TaskName`""
Write-Host "Remove task with: powershell -ExecutionPolicy Bypass -File scripts\uninstall_json_audit_scheduled_task.ps1"
