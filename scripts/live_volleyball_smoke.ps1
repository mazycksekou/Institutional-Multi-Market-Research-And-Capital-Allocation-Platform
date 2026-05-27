. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "volleyball" -ExpectedModel "volleyball_sideout_attack_block_serve_monte_carlo_model" -ExpectedCalibration "volleyball"
