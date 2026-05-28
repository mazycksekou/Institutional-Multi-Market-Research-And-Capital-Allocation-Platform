. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "snooker" -ExpectedModel "snooker_frame_break_safety_potting_monte_carlo_model" -ExpectedCalibration "snooker"
