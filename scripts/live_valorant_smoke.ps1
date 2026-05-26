. "$PSScriptRoot\live_payloads.ps1"
. "$PSScriptRoot\live_helpers.ps1"
. "$PSScriptRoot\live_checks.ps1"

Invoke-LiveSportSmoke -Sport "valorant" -ExpectedModel "valorant_agent_composition_economy_map_pool_monte_carlo_model" -ExpectedCalibration "valorant"
