$ErrorActionPreference = "Stop"

. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "pickleball" -ExpectedModel "pickleball_dink_kitchen_serve_return_monte_carlo_model" -ExpectedCalibration "pickleball"
