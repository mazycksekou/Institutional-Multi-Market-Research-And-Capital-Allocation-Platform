$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$children = @(
    "live_nba_smoke.ps1",
    "live_wnba_smoke.ps1",
    "live_ncaab_smoke.ps1",
    "live_ncaawb_smoke.ps1"
)
foreach ($child in $children) {
    Write-Host "Running $child"
    & powershell -ExecutionPolicy Bypass -File (Join-Path $ScriptDir $child)
    if ($LASTEXITCODE -ne 0) {
        Write-Host "$child failed."
        exit $LASTEXITCODE
    }
}
Write-Host "Basketball live smoke PASS"
exit 0

