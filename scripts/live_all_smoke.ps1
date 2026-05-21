$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$children = @(
    "live_basketball_smoke.ps1",
    "live_core_smoke.ps1"
)
foreach ($child in $children) {
    Write-Host "Running $child"
    & powershell -ExecutionPolicy Bypass -File (Join-Path $ScriptDir $child)
    if ($LASTEXITCODE -ne 0) {
        Write-Host "$child failed."
        exit $LASTEXITCODE
    }
}
Write-Host "All current active sport live smoke PASS"
exit 0

