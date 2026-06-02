param(
    [string]$TaskName = "BettingStockApiJsonAudit"
)

$ErrorActionPreference = "Stop"

$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($Task) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Scheduled task removed: $TaskName"
}
else {
    Write-Host "Scheduled task not found: $TaskName"
}
