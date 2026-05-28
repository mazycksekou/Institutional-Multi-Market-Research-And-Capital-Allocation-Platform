. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "darts" -ExpectedModel "darts_checkout_scoring_pressure_leg_set_monte_carlo_model" -ExpectedCalibration "darts"
