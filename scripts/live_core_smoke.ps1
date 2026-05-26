$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$children = @(
    "live_nfl_smoke.ps1",
    "live_mlb_smoke.ps1",
    "live_soccer_smoke.ps1",
    "live_nhl_smoke.ps1",
    "live_tennis_smoke.ps1",
    "live_combat_smoke.ps1",
    "live_golf_smoke.ps1",
    "live_ncaaf_smoke.ps1",
    "live_f1_smoke.ps1",
    "live_nascar_smoke.ps1",
    "live_indycar_smoke.ps1",
    "live_motogp_smoke.ps1",
    "live_cricket_smoke.ps1",
    "live_cs2_smoke.ps1",
    "live_valorant_smoke.ps1",
    "live_lol_smoke.ps1",
    "live_dota2_smoke.ps1",
    "live_cod_smoke.ps1"
)
foreach ($child in $children) {
    Write-Host "Running $child"
    & powershell -ExecutionPolicy Bypass -File (Join-Path $ScriptDir $child)
    if ($LASTEXITCODE -ne 0) {
        Write-Host "$child failed."
        exit $LASTEXITCODE
    }
}
Write-Host "Core live smoke PASS"
exit 0
