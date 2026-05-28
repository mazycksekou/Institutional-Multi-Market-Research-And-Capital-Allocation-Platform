. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "water_polo" -ExpectedModel "water_polo_goalkeeper_power_play_shot_quality_monte_carlo_model" -ExpectedCalibration "water_polo"
