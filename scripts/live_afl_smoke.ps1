$ErrorActionPreference = "Stop"

. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "afl" -ExpectedModel "afl_clearance_inside50_scoring_shot_monte_carlo_model" -ExpectedCalibration "afl"
