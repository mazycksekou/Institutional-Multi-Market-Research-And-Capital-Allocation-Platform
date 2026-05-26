. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "lol" -ExpectedModel "league_of_legends_draft_objective_gold_monte_carlo_model" -ExpectedCalibration "league_of_legends"
