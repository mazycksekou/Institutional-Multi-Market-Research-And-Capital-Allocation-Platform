. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "badminton" -ExpectedModel "badminton_serve_return_rally_momentum_shuttle_monte_carlo_model" -ExpectedCalibration "badminton"
