. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "handball" -ExpectedModel "handball_fastbreak_goalkeeper_efficiency_monte_carlo_model" -ExpectedCalibration "handball"
