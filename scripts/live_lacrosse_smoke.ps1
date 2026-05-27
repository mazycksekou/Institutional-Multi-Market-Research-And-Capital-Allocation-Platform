. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "lacrosse" -ExpectedModel "lacrosse_faceoff_possession_shot_quality_monte_carlo_model" -ExpectedCalibration "lacrosse"
