. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "rugby" -ExpectedModel "rugby_set_piece_territory_expected_points_monte_carlo_model" -ExpectedCalibration "rugby"
