. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "table_tennis" -ExpectedModel "table_tennis_serve_return_rally_momentum_monte_carlo_model" -ExpectedCalibration "table_tennis"
